#!/usr/bin/python

import secrets
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(secrets.icomfort_username, secrets.icomfort_password)
print("Logged In: ", s.login_complete)
print("Initialized: ", s.initialized)
for home in s.homes:
    lcc_zones = s.homes[home]
    for (lcc, zone) in lcc_zones:
        z = IComfort3Zone(home, lcc, zone)
        print(z.fetch_update(s))
