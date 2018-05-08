#!/usr/bin/python

import secrets
import time
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
z = None
for home in s.homes:
    lcc_zones = s.homes[home]
    for (lcc, zone) in lcc_zones:
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Set Away: %s" % update['isSysteminAwayMode'])
        away = z.set_away_mode(s)
        print("After Set Away: %s" % away['isSysteminAwayMode'])

for home in s.homes:
    lcc_zones = s.homes[home]
    for (lcc, zone) in lcc_zones:
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Cancel Away: %s" % update['isSysteminAwayMode'])
        cancel = z.cancel_away_mode(s)
        print("After Cancel Away: %s" % cancel['isSysteminAwayMode'])
