#!/usr/bin/python

import secrets
import time
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
homes = s.fetch_home_zones()
print ("Starting Away Mode test for homes %s." % homes)
for home in homes:
    for (lcc, zone) in homes[home]:
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        while (update == False):
            print("Fetch failed, retrying.")
            s.logout()
            s = IComfort3Session()
            s.login(secrets.icomfort_username, secrets.icomfort_password, True)
            update = z.fetch_update(s)
        print("Before Set Away: %s" % update['isSysteminAwayMode'])
        away = z.set_away_mode(s)
        print("After Set Away: %s" % away['isSysteminAwayMode'])
        while (away['isSysteminAwayMode'] == 'False'):
            away = z.set_away_mode(s)
            print("After Set Away: %s" % away['isSysteminAwayMode'])

for home in homes:
    for (lcc, zone) in homes[home]:
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Cancel Away: %s" % update['isSysteminAwayMode'])
        cancel = z.cancel_away_mode(s)
        print("After Cancel Away: %s" % cancel['isSysteminAwayMode'])
        while (cancel['isSysteminAwayMode'] == 'False'):
            cancel = z.cancel_away_mode(s)
            print("After Cancel Away: %s" % cancel['isSysteminAwayMode'])

s.logout()
