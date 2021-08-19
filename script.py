import os
import sys
import getopt
import dns.resolver
from subprocess import call
import time

def main(argv):
    #get user data
    site_name = argv[0]
    business_mail = argv[1]
    phone = argv[2]
    password = argv[3]

    #prepare some data
    admin_password = 'Qwe-123'

    #call dns server
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers[0]

    #call bench commands
    call(["bench", "config", "dns-mulitenant", "on"])]
    call(["bench", "new-site", site_name])]

    #wait for the "Password:" prompt
    time.sleep(2)

    call([b])

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Not enough arguments!")
    else
        sys.exit()
   main(sys.argv[1:])