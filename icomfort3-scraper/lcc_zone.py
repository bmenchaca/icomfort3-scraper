import logging
import time
import json
import random
from session import IComfort3Session as IC3Session

try:
    from urllib.parse import urlencode, urlunsplit
except ImportError:
    from urlparse import urlunsplit, urlparse
    from urllib import urlencode

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

"""
  Most of the information below is from the User Manual at:
    https://static.lennox.com/pdfs/owners/s30/Lennox_iComfortS30_Homeowner_Manual.pdf
  The heirachy of constructs in the Lennox Page looks like this:
    There may be one or more Homes,
    Which may contain one or more Lennox Climate Control Systems,
    Which may contain one or more Zones.

    Zones
      Each Zone contains a Mode, which is one of:
        (Off, Cool Only, Heat Only, Heat/Cool)
        Each of these Modes contain required Temperatures, as:
          (Off = None,
           Cool = Max Indoor Temp; >= Cooling Starts,
           Heat = Min Indoor Temp <= Heating Starts,
           Heat/Cool = Max and Min as above.  As a note, these cannot be closer
             than 3 degrees from each other.
      Addtionally, each zone contains a Fan setting:
        On = Fan is turned on regardless of Climate Control,
        Auto = Fan is controlled by Climate Control,
        Circulate = As Auto, and also runs at a low rate between CC cycles.  The
        amount of time circulate runs per hour can be configured from the
        Settings->Fan->Circulate option (9 to 27 minutes).
        Allergen Defender = Circulates air inside when the air quality is bad
          outside to filter it.  This is basically Circulate mode that only runs
          if the Air Quality outside is poor.  For this to be an available
          option, Allergen Defender must be enabled in the Settings->Fan menu
          under Allergen Defender.
      
      Schedules
            The Mode and Fan settings can be automatically adjusted
        based on one or more Schedules.  These schedules change based on the
        season: Summer, Winter, and Spring/Fall. 
            Each schedule is subdivided into Periods.  Each Period has a start
        time, as well as Mode and Fan settings.  Schedules can be configured
        to have the same Periods for all days of the week, different Periods
        for weekdays and weekends, or a different set of Periods every day.  For
        each configured day, there may be at most 4 periods.
        
            Schedule IQ has the same periods every day, and is based  wake-up
        time, sleep time, and away Mode scheduling rather than season or day
        of the week.

      Current Set Points (Mode)
        Instantaneous changes can be made to Mode, Temperatures, and Fan.  These
        will be automatically changed when the next schedule changes them, or
        a "Schedule Hold" can be set for a fixed amount of time to prevent the
        schedule from changing them.  The changes and the hold can be cancelled
        by disabling the Schedule Hold.

      Away Mode
        This mode may be set per household, and configures the Thermostat to
        put all LCCs and Zones into a cost-saving Heat/Cool setting.  The
        temperature for these may be controlled from the Settings->Away menu
        under away-set-points. You may also toggle Smart Away on, which uses
        the installed iComfort App on your phone to control automatic enabling
        of the Away feature using Geofencing for all participating devices.

  For all requests, look for a 302 redirect, with the location:
     /Account/Login?_isSessionExpired=True
  This means we need to log in again, so set login = false, and clear the data.
  TODO: We should also parse and check if a login fails, and we are locked out.
  This should yield a different error so the user understands no amount of
  uname/password changes will fix this issue (for 15 minutes).
"""
class IComfort3Zone(object):
    MYHOMES_PATH = 'Dashboard/MyHomes'
    HD_REFERER_PATH = 'Dashboard/HomeDetails'
    DETAILS_PATH = 'Dashboard/RefreshLatestZoneDetailByIndex'
    SET_AWAY_PATH = 'Dashboard/SetAwayMode'
    CANCEL_AWAY_PATH = 'Dashboard/CancelAwayMode'
    CHANGE_SET_POINT = 'Dashboard/ChangeSetPoint'
    MODE_SCHED_PATH = 'ModesSchedules/ModesSchedulesMenu'
    CHANGE_ZONE_SCHED = 'ModesSchedules/ChangeZoneScheduleId'
    SYSMODE_MANUAL = 'modesSchedules/ChangeSystemModeManual'

    def __init__(self, home_id, lcc_id, zone_id):
        # static, pre-configured entries
        self.zone_id = str(zone_id)
        self.home_id = str(home_id)
        self.lcc_id = str(lcc_id)
        details_referer_query = ( ('zoneId', self.zone_id),
                                  ('homeId', self.home_id),
                                  ('lccId', self.lcc_id),
                                  ('refreshZonedetail', 'False') )
        self.hd_url = IC3Session.create_url(IComfort3Zone.HD_REFERER_PATH,
                                            details_referer_query)  
        mode_sched_query = ( ('zoneId', self.zone_id), ('lccId', self.lcc_id) )
        self.ms_url = IC3Session.create_url(IComfort3Zone.MODE_SCHED_PATH,
                                            mode_sched_query)


    def __send_update_request(self, session):
        current_millis = (int(time.time()) * 1000) + random.randint(0, 999)
        details_query = ( ('zoneid', self.zone_id), ('isPolling', 'true'),
                          ('lccid', self.lcc_id), ('_', str(current_millis)) )
        up_url = IC3Session.create_url(IComfort3Zone.DETAILS_PATH,
                                                 details_query)
        resp = session.request_json(up_url, self.hd_url)
        resp_json = session.process_as_json(resp)
        return resp_json


    # The requestor validated that the session has not Failed
    def __parse_update(self, update):
        if not update['Code'] == 'LCC_ONLINE':
            print("LCC is offline.")
        # Remove Unused temperature Range
        # Check if zoneDetail exists
        flat = dict()
        if update['data']['zoneDetail']:
            # Copy all other zone details
            for (k,v) in update['data']['zoneDetail'].items():
                flat[k] = v
            # Ambient temp comes across not flattened, and as a string
            flat['AmbientTemperature'] = flat['AmbientTemperature']['Value']
            flat['AmbientTemperature'] = int(flat['AmbientTemperature'])
            flat['CoolSetPoint'] = flat['CoolSetPoint']['Value']
            flat['HeatSetPoint'] = flat['HeatSetPoint']['Value']
            flat['SingleSetPoint'] = flat['SingleSetPoint']['Value']
            # This is only for visuals
            del flat['TemperatureRange']
        del update['data']['zoneDetail']
        del update['data']['zonepaging']
        # Copy the rest of data
        for (k,v) in update['data'].items():
            flat[k] = v
        flat['Code'] = update['Code']
        return flat


    
    def fetch_update(self, session):
        """ Fetches an update from the web API.

        Uses the session to fetch the latest status info from the web API for a
        thermostat, and returns the resulting dictionary.  If there is a
        problem an exception will be thrown.

        Args:
            session: A logged-in session with permission to access this zone.

        Returns:
            A dict with the current status information for this zone.

        Raises:
            Possible Errors
            Username/Password could be wrong
            the session could not be logged in
            The session is now expired
            The system is not currently accessible
        """
        update_json = self.__send_update_request(session)
        if not update_json:
            return False
        return self.__parse_update(update_json)


    def set_away_mode(self, session):
        """ Post to set away mode for an LCC/Zone, and returns current state.
        """
        set_away_url = IC3Session.create_url(IComfort3Zone.SET_AWAY_PATH)
        payload = [('lccId', self.lcc_id), ('currentzoneId', self. zone_id)]
        resp = session.post_url_json(set_away_url, payload, self.hd_url)
        rsep_json = session.process_as_json(resp)
        if not resp_json:
            return False
        return self.__parse_update(resp_json)


    def cancel_away_mode(self, session):
        """ Post to cancel away mode for an LCC/Zone, and returns current state.
        """
        cancel_away_url = IC3Session.create_url(IComfort3Zone.CANCEL_AWAY_PATH)
        payload = [('lccId', self.lcc_id), ('currentzoneId', self. zone_id),
                   ('smartawayS', 'false')]
        resp = session.post_url_json(cancel_away_url, payload, self.hd_url)
        resp_json = session.process_as_json(resp)
        if not resp_json:
            return False
        return self.__parse_update(resp_json)

    def change_set_point(self, session, cool, heat):
        """ Set new heat/cool ScheduleHold values.

            By default, these changes will last until the next Period.

            Args:
                cool: The value above which the LCC should cool the zone.  If in
                heating mode, this parameter must be set to minCSP.

                heat: The value below which the LCC should heat the zone.  If in
                cooling only mode, this parameter must be set to maxHSP.

            FIXME: Does not support PerfectTemp today.
        """
        hd_referer = IC3Session.create_url(IComfort3Zone.MYHOMES_PATH)
        session.request_url(self.hd_url, hd_referer)
        current_millis = (int(time.time()) * 1000) + random.randint(0, 999)
        query = [('zoneId', self.zone_id), ('lccId', self.lcc_id),
                 ('coolSetPoint', str(cool)), ('heatSetPoint', str(heat)),
                 ('isPerfectTempOn', 'false'), ('_', str(current_millis))]
        change_url = IC3Session.create_url(IComfort3Zone.CHANGE_SET_POINT,
                                           query)
        resp = session.request_json(change_url, referer_url=self.hd_url)
        resp_json = session.process_as_json(resp)
        return self.__parse_update(resp_json)


    def change_zone_schedule_id(self, session, schedule_id):
        """ Change the current zone Schedule by ID.
        """
        payload = [('lccId', self.lcc_id), ('zoneId', self.zone_id),
                   ('scheduleId', schedule_id)]
        change_zs_url = IC3Session.create_url(IComfort3Zone.CHANGE_ZONE_SCHED)
        resp = session.post_url_json(change_zs_url, post_data=payload, 
                                     referer_url=self.ms_url)
        resp.raise_for_status
        return resp.status_code == 200

    def change_system_mode_manual(self, session, schedule_id, period_id, mode):
        """ Change to a manually controlled mode rather than a schedule.
        """
        payload = [('zoneId', self.zone_id), ('lccId', self.lcc_id),
                   ('scheduleId', schedule_id), ('periodId', period_id),
                   ('mode', mode)]
        sysmode_url = IC3Session.create_url(IComfort3Zone.SYSMODE_MANUAL)
        resp = session.post_url_json(sysmode_url, post_data=payload, 
                                     referer_url=self.ms_url)
        resp.raise_for_status
        return resp.status_code == 200

