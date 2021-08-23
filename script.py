import os
import sys
import getopt
import dns.resolver
from subprocess import call
import time
import base64
from urllib.parse import urlencode
from urllib.request import urlopen,Request
import xml.etree.ElementTree as etree
import pexpect
from python_hosts import Hosts, HostsEntry

def fetch_external_ip(type):
    url = 'http://' + ("ipv6" if type == "AAAA" else "ipv4") + '.myexternalip.com/raw'
    ip = urlopen(url).read().decode('utf-8')[:-1]
    return ip

def main(argv):
    #get user data from client registration form
    site_name = argv[0]
    business_mail = argv[1]
    phone = argv[2]
    password = argv[3]

    #prepare some authentication data
    mysql_password = "password"
    admin_password = "password"

    # Generate a auth_string to connect to cPanel
    auth_string = 'Basic ' + base64.b64encode((CONFIG['username']+':'+CONFIG['password']).encode()).decode("utf-8")

    # Show all arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ttl', default='300', help='Time To Live')
    parser.add_argument('--type', default='CNAME', help='Type of record: A for IPV4 or AAAA for IPV6')
    parser.add_argument('--ip', help='The IPV4/IPV6 address (if known)')
    parser.add_argument('--value', help='The value of the CNAME (if known)')
    parser.add_argument('--name', help='Your record name, ie: ipv6.domain.com', required=True)
    parser.add_argument('--domain', help='The domain name containing the record name', required=True)
    args = parser.parse_args()

    # Fetch existing DNS records
    q = Request(CONFIG['url'] + '/xml-api/cpanel?cpanel_xmlapi_module=ZoneEdit&cpanel_xmlapi_func=fetchzone&cpanel_xmlapi_apiversion=2&domain=' + domain)
    q.add_header('Authorization', auth_string)
    xml = urlopen(q).read().decode("utf-8")

    domain = args.domain    
    record = args.name
    if not record.endswith('.'):
        record += "."
    type = "CNAME"
    if args.type.upper() == "CNAME":
        type = args.type.upper()
    ip = args.ip if args.ip != None else fetch_external_ip(type)
    ttl = args.ttl
    value = args.value if args.value != None else ""

    # Parse the records to find if the record already exists
    root = etree.fromstring(xml)
    line = "0"
    for child in root.find('data').findall('record'):
        if child.find('name') != None and child.find('name').text == record:
            line = str(child.find('line').text)
            break

    # Update or add the record
    query = "&address=" + ip
    if type == "TXT":
        query = "&" + urlencode( {'txtdata': value} )

    url = CONFIG['url'] + "/xml-api/cpanel?cpanel_xmlapi_module=ZoneEdit&cpanel_xmlapi_func=" + ("add" if line == "0" else "edit") + "_zone_record&cpanel_xmlapi_apiversion=2&domain="+ domain + "&name=" + record + "&type=" + type + "&ttl=" + ttl + query
    if line != "0":
        url += "&Line=" + line

    print(url)

    #write bench shell commands to install the new erpnext site
    child = pexpect.spawn("bench config dns-mulitenant on")
    child = pexpect.spawn("bench new-site" + site_name)
    child.expect("MySQL root password:")
    child.sendline(mysql_password)
    child.expect("Set Administrator password:")
    child.sendline(admin_password)
    child.expect("Re-enter Administrator password:")
    child.sendline(admin_password)
    time.sleep(2)
    child = pexpect.spawn("bench setup nginx")
    child.expect("[Y/N]:")
    child.sendline("y")
    out = subprocess.Popen(['sudo', 'service','nginx', 'reload'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = subprocess.Popen(['bench', '--site', site_name, 'install-app', 'erpnext'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #open /etc/hosts and add the new sub-domain as a new entry
    my_hosts = Hosts()
    new_entry = HostsEntry(entry_type='ipv4', address=ip, names=[site_name])
    my_hosts.add([new_entry])
    my_hosts.write()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Not enough arguments!")
    else
        sys.exit()
    try:
        from config import CONFIG
    except ImportError:
        print("Error: config.py NOT found")
        exit()
    main(sys.argv[1:])