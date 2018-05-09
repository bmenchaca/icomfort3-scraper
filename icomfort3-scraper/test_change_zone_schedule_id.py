#!/usr/bin/python

import secrets
import time
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
homes = s.fetch_home_zones()

for home in homes:
    for (lcc, zone) in homes[home]:
        z = IComfort3Zone(home, lcc, zone)
        s.set_context(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Change Zone Schedule: %s" % update['ScheduleId'])
        change = z.change_zone_schedule_id(s, 1)
        after = z.fetch_update(s)
        print("After Change Zone Schedule: %s" % update['ScheduleId'])

for home in homes:
    for (lcc, zone) in homes[home]:
        z = IComfort3Zone(home, lcc, zone)
        s.set_context(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Change Zone Schedule: %s" % update['ScheduleId'])
        change = z.change_zone_schedule_id(s, 3)
        after = z.fetch_update(s)
        print("After Change Zone Schedule: %s" % update['ScheduleId'])

s.logout()
