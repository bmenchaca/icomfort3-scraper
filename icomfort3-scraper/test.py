#!/usr/bin/python

import secrets
from session import IComfort3Session
from lcc_zone import IComfort3Zone

s = IComfort3Session()
s.login(icomfort_username, icomfort_password)
print("Logged In: ", s.login_complete)
print("Initialized: ", s.initialized)
for home in s.homes:
    for (lcc, zone) in home:
        z = IComfort3Zone(home, lcc, zone)
        print(z.fetch_update(s))
