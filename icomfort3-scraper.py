mport logging
import sys
import csv
import re
import ssl
import json
import time

try:
    from urllib.parse import urlencode, urlunsplit
except ImportError:
    from urlparse import urlunsplit
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

         

  The object holds a dictionary of homes, structured as:
  { id0 -> zone_dict, id2 -> zone_dict, ... idN -> zone_dict }
  
  Each zone_dict looks like this:
  { zone_id_0 -> 

  For all requests, look for a 302 redirect, with the location:
     /Account/Login?_isSessionExpired=True
  This means we need to log in again, so set login = false, and clear the data.
"""
class IComfort3Client(object):

    STARTING_COOKIES = { 'iComfort': 'ic3' }
    DOMAIN = 'www.lennoxicomfort.com'
    LOGIN_PATH = 'Account/Login'
    HOMES_PATH = 'Dashboard/MyHomes'
    ZONES_PATH = 'Dashboard/GetHomeZones'
    DETAILS_PATH = 'Dashboard/RefreshLatestZoneDetailByIndex'

    def __init__(self):
        self.session = requests.Session()
        self.homes = {}
        self.login_complete = False
        requests.utils.add_dict_to_cookiejar(sessions.cookies,
                                             IComfort3Client.starting_cookies)
        self.session.headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/apng,*/*;q=0.8'})
        self.session.headers.update({'Accept-Encoding': 'gzip, default, br'})
        self.session.headers.update({'Accept-Language': 'en-US,en;q=0.8'})
        self.session.headers.update({'Connection': 'keep-alive'})
        self.session.headers.update({'DNT': '1'})
        self.session.headers.update({'Host': 'www.lennoxicomfort.com'})
        self.session.headers.update({'Upgrade-Insecure-Requests': '1'})
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'})


    def login(self, email, password):
        self.session.headers.update({'Referer': "https://www.lennoxicomfort.com/Landing.html"})
        parts = ('https', IComfort3Client.DOMAIN,
                 IComfort3Client.LOGIN_PATH, '', '')
        login_url = urlunsplit(parts)
        login_page = self.session.get(login_url,
                                      IComfort3Client.starting_cookies)
        if login_page.status_code != 200:
            print "Could not load login page."
            return False

        login_page_soup = BeautifulSoup(login_page.content, "lxml")
        try:
            form = login_page_soup.find('form')
            req_verf_token = form.find('input', {'name': '__RequestVerificationToken'}).get('value')
        except:
            print "Could not find token."
            return False
        # Headers for the POST
        self.session.headers.update({'Cache-Control': 'max-age=0'})
        self.session.headers.update({'Origin': 'https://www.lennoxicomfort.com'})
        self.session.headers.update({'Referer': login_url})
        payload = (('__RequestVerificationToken', req_verf_token),
                   ('EmailAddress', email),
                   ('Password', password))
        logged_in = session.post(login_url, data=payload)
        # Test if we are logged in - check for login error?
        self.login_complete = True
        return True

    def get_home_ids(self):
        if not self.login_complete:
            return False
        parts = ('https', IComfort3Client.DOMAIN,
                 IComfort3Client.HOMES_PATH, '', '')
        homes_url = urlunsplit(parts);
        homes_session = session.get(homes_url);
        homes_soup = BeautifulSoup(homes_session.content, "lxml")
        # Homes are provided as UL with the ID slider1
        sliders = homes_soup.findAll('ul', {'id': 'slider1'})
        self.home_ids = []
        for slider in sliders:
            home_ids.append(slider.get("data-homeid"))

    def update_home(self, home_id):
        if not self.login_complete:
            return False


    def update_homes(self):
