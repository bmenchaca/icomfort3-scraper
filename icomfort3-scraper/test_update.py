#!/usr/bin/python

import secrets
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
homes = s.fetch_home_zones()

for home in homes:
    lcc_zones = homes[home]
    for (lcc, zone) in lcc_zones:
        s.set_context(home, lcc, zone)
        z = IComfort3Zone(home, lcc, zone)
        print ("Home %s, lcc %s, zone %s" % (home, lcc, zone))
        update = z.fetch_update(s)
        print(update)

out = s.logout()
print(out.status_code)
