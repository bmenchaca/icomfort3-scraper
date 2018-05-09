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
        s.set_context(home, lcc, zone)
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Change Set Point: Cool %s, Heat %s" % 
              (update['CoolSetPoint'], update['HeatSetPoint']))
        change = z.change_set_point(s, 73, 67)
        print("From Change Set Point: Cool %s, Heat %s" % 
              (change['CoolSetPoint'], change['HeatSetPoint']))
        after = z.fetch_update(s)
        print("Update Change Set Point: Cool %s, Heat %s" % 
              (after['CoolSetPoint'], after['HeatSetPoint']))

for home in homes:
    for (lcc, zone) in homes[home]:
        s.set_context(home, lcc, zone)
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print("Before Change Set Point: Cool %s, Heat %s" % 
              (update['CoolSetPoint'], update['HeatSetPoint']))
        change = z.change_set_point(s, 74, 67)
        print("From Change Set Point: Cool %s, Heat %s" % 
              (change['CoolSetPoint'], change['HeatSetPoint']))
        after = z.fetch_update(s)
        print("Update Change Set Point: Cool %s, Heat %s" % 
              (after['CoolSetPoint'], after['HeatSetPoint']))

s.logout()
