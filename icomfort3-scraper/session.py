import logging
import sys
import csv
import re
import ssl
import json
import time
import requests

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
class IComfort3Session(object):

    DOMAIN = 'www.lennoxicomfort.com'
    STARTING_COOKIES = { 'iComfort': 'ic3' }
    LOGIN_PATH = 'Account/Login'
    RELOGIN_LOC = '/Account/Login?_isSessionExpired=True'

    def __init__(self):
        self.session = requests.Session()
        self.login_complete = False
        requests.utils.add_dict_to_cookiejar(self.session.cookies,
                                             IComfort3Session.STARTING_COOKIES)
        self.session.headers.update({'Accept-Encoding': 'gzip, deflate, br'})
        self.session.headers.update({'Accept-Language': 'en-US,en;q=0.8'})
        self.session.headers.update({'Connection': 'keep-alive'})
        self.session.headers.update({'DNT': '1'})
        self.session.headers.update({'Host': 'www.lennoxicomfort.com'})
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'})

    def request_url(self, url, referer_url=''):
        header_dict = {}
        header_dict['Upgrade-Insecure-Requests'] = '1'
        header_dict['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/apng,*/*;q=0.8'
        if not self.login_complete:
            return 0
        if referer_url:
            header_dict['Referer'] = referer_url

        resp = self.session.get(url, headers=header_dict)
        if resp.status_code == 302:
            if 'Location' in resp.headers:
                if resp.headers['Location'] == IComfort3Session.RELOGIN_LOC:
                        self.login_complete = False
            return 0
        return resp


    def post_url(self, url, post_data=[], referer_url=''):
        post_heads = {}
        if referer_url:
            post_heads['Referer'] = referer_url
        post_heads['Origin'] = "https://" + IComfort3Session.DOMAIN
        resp = self.session.post(url, headers=post_heads, data=post_data)
        return resp


    def request_json(self, url, referer_url=''):
        header_dict = {}
        header_dict['X-Requested-With'] = 'XMLHttpRequest'
        header_dict['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        header_dict['ADRUM'] = 'isAjax:true'
        if not self.login_complete:
            return 0
        if referer_url:
            header_dict['Referer'] = referer_url 
        response = self.session.get(url, headers=header_dict)
        print("URL was: %s" % response.request.url)
        print("Request Headers: %s" % response.request.headers)
        print("Content Type: %s" % response.headers['content-type'])
        if response.headers['content-type'] == 'text/html; charset=utf-8':
            print("Response is HTML.")
            html_soup = BeautifulSoup(response.content, "lxml")
            divs = html_soup.findAll("div", {"class": "tsbody"})
            if divs:
                p = divs[0].findAll("p")[0]
                text = p.getText()
                if text.find("technical difficulties"):
                    print("You have technical difficulties.")
            return {}
        else:
            response_json = response.json()
            response_code = response_json['Code']
        # We don't know what happened here - can't parse.
        # FIXME: Print probably?
            if not response_code:
                print("Could not find resonse code.")
                print(response_json)
                return False
        # Request failed - our session is invalid
            if response_code == 'Fail':
                print("Response code was Fail.")
                print(response_json)
                self.login_complete = False
                return False
            print(response_json)
            return response_json


    @classmethod
    def create_url(cls, path, query_params=''):
        query = urlencode(query_params)
        parts = ('https', cls.DOMAIN, path, query, '')
        return urlunsplit(parts)


    def login(self, email, password):
        header_dict = {}
        header_dict['Referer'] = "https://www.lennoxicomfort.com/Landing.html"
        parts = ('https', IComfort3Session.DOMAIN,
                 IComfort3Session.LOGIN_PATH, '', '')
        login_url = urlunsplit(parts)
        login_page = self.session.get(login_url, headers=header_dict)
        if login_page.status_code != 200:
            print("Could not load login page.")
            return False
        login_page_soup = BeautifulSoup(login_page.content, "lxml")
        form = login_page_soup.find('form')
        token_entry = {'name': '__RequestVerificationToken'}
        req_verf_token = form.find('input', token_entry).get('value')
        # Handle not finding token
        # Headers for the POST
        post_heads = {}
        post_heads['Referer'] = login_url
        post_heads['Cache-Control'] = 'max-age=0'
        post_heads['Origin'] = 'https://www.lennoxicomfort.com'
        payload = [('__RequestVerificationToken', req_verf_token),
                   ('EmailAddress', email),
                   ('Password', password)]
        logged_in = self.session.post(login_url, headers=post_heads,
                                      data=payload)
        # Test if we are logged in - check for login error?
        self.login_complete = True
        return True
