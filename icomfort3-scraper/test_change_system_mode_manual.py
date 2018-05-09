#!/usr/bin/python

import secrets
import time
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
homes = s.fetch_home_zones()

#mode: heat = 1, off = 4, cool = 0, Heat_And_Cool = 2
#schedule 16 = manual mode
for home in homes:
    for (lcc, zone) in homes[home]:
        z = IComfort3Zone(home, lcc, zone)
        s.set_context(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        sch_id = update['ScheduleId']
        per_id = update['PeriodId']
        if update['ScheduleId'] == 16:
            mode_text = "Manual"
        else:
            mode_text = "Schedule %s" % update['ScheduleId']
        print("Before Change Manual Mode: %s, mode %s" % (mode_text, update['SystemMode']))
        change = z.change_system_mode_manual(s, sch_id, per_id, 'Heat_And_Cool')
        after = z.fetch_update(s)
        if update['ScheduleId'] == 16:
            mode_text = "Manual"
        else:
            mode_text = "Schedule %s" % update['ScheduleId']
        print("After Change Manual Mode: %s, mode %s" % (mode_text, update['SystemMode']))

s.logout()
