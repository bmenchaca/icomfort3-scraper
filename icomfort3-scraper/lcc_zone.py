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
    HD_REFERER_PATH = 'Dashboard/HomeDetails'
    DETAILS_PATH = 'Dashboard/RefreshLatestZoneDetailByIndex'
    SET_AWAY_PATH = 'Dashboard/SetAwayMode'

    def __init__(self, home_id, lcc_id, zone_id):
        # static, pre-configured entries
        self.zone_id = str(zone_id)
        self.home_id = str(home_id)
        self.lcc_id = str(lcc_id)

    def __send_update_request(self, session):
        details_referer_query = ( ('zoneId', self.zone_id),
                                  ('homeId', self.home_id),
                                  ('lccId', self.lcc_id),
                                  ('refreshZonedetail', 'False') )
        referer_url = IC3Session.create_url(IComfort3Zone.HD_REFERER_PATH,
                                            details_referer_query)  
        current_millis = (int(time.time()) * 1000) + random.randint(0, 999)
        details_query = ( ('zoneid', self.zone_id), ('isPolling', 'true'),
                          ('lccid', self.lcc_id), ('_', str(current_millis)) )
        up_url = IC3Session.create_url(IComfort3Zone.DETAILS_PATH,
                                                 details_query)
        update = session.request_json(up_url, referer_url)
        return update


    # The requestor validated that the session has not Failed
    def __parse_update(self, update):
        if not update['Code'] == 'LCC_ONLINE':
            return False
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
        """ Post to set away mode for an LCC/Zone, and return current state.
        """
        set_away_url = IC3Session.create_url(IComfort3Zone.SET_AWAY_PATH)
        pass



