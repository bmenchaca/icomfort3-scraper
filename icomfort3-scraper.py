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


class IComfort3Client(object):

    STARTING_COOKIES = { 'iComfort': 'ic3' }
    DOMAIN = 'www.lennoxicomfort.com'
    LOGIN_PATH = 'Account/Login'
    HOMES_PATH = 'Dashboard/MyHomes'
    ZONES_PATH = 'Dashboard/GetHomeZones'
    DETAILS_PATH = 'Dashboard/RefreshLatestZoneDetailByIndex'


    def __init__(self):
        self.session = requests.Session()
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


    def get_home_list(self):

    def update_home(self, home_id):
