import os
import sys
import dns.resolver
from subprocess import call
import time
import base64
from urllib.parse import urlencode
from urllib.request import urlopen,Request
import xml.etree.ElementTree as etree
import pexpect
from python_hosts import Hosts, HostsEntry
import argparse
import logging
import logging.handlers

def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def fetch_ip():
    #prepare google cloud compute engine data 
    project = "project_id"
    bucket = "bucket_name"
    zone = "zone"
    instance_name = "instance_name"
    #build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')
    operation = create_instance(compute, project, zone, instance_name, bucket)
    wait_for_operation(compute, project, zone, operation['name'])
    #get compute engine vm instances
    instances = list_instances(compute, project, zone)
    if instances != None:
        for instance in instances:
            logging.info(' - ' + instance['name'])
    else
        logging.info('no vm instances returned')
    #make a http request to get vm instance info, then get it's ip
    try:
        request = Request('https://compute.googleapis.com/compute/v1/projects/'+project+'/zones/'+zone+'/instances/'+instance-name)
        responseData = urlopen(request).read()
        logging.info(responseData)
    except Exception as e:
        logging.exception(str(e))
    ip = responseData.networkInterfaces.accessConfigs.natIP
    return ip

def main(argv):
    #get user data from client registration form
    site_name = argv[0]
    business_mail = argv[1]
    phone = argv[2]
    password = argv[3]

    #get all arguments needed to create a new A dns record
    ip = CONFIG['ip']
    ttl = CONFIG['record_ttl']
    record_type = CONFIG['record_type']
    record_name = site_name
    if not record_name.endswith('.'):
        record_name += "."
    domain = record_name + CONFIG['subdomain']

    #prepare some authentication data
    mysql_password = CONFIG['mysql_password']
    admin_password = CONFIG['admin_password']

    #Generate a auth_string to connect to cPanel
    auth_string = 'Basic ' + base64.b64encode((CONFIG['cpanel_username']+':'+CONFIG['cpanel_password']).encode()).decode("utf-8")

    # Fetch existing DNS records
    try:
        request = Request(CONFIG['url'] + '/xml-api/cpanel?cpanel_xmlapi_module=ZoneEdit&cpanel_xmlapi_func=fetchzone&cpanel_xmlapi_apiversion=2&domain=' + domain)
        request.add_header('Authorization', auth_string)
        logging.info("fetching records succedded with status code : " + str(request.getCode()))
        response_xml = urlopen(request).read().decode("utf-8")
    except Exception as e:
       logging.exception("fetching records apported with status code : " + str(e.getCode()))

    #Parse the records to find if the record already exists
    root = etree.fromstring(response_xml)
    for child in root.find('data').findall('record'):
        if child.find('name') != None and child.find('name').text == record_name:
            logging.info("record already exist with the same name")
            sys.exit()
            break

    #add the new record
    url = CONFIG['url'] + "/xml-api/cpanel?cpanel_xmlapi_module=ZoneEdit&cpanel_xmlapi_func=add_zone_record&cpanel_xmlapi_apiversion=2&domain="+ domain + "&name=" + record_name + "&type=" + record_type + "&ttl=" + ttl + "&address=" + ip
    logging.info("create new record url " + url)
    try:
        create_record_request = Request(url)
        create_record_request.add_header('Authorization', auth_string)
        returned_response = urlopen(create_record_request).read()
        returned_response_decored = returned_response.decode("utf-8")
        logging.info(returned_response_decored)
    except Exception as e:
        logging.exception("creating new record apported with status code :" + str(e.getCode()))
        sys.exit()

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

    #start the user erpnext instance
    out = subprocess.Popen(['bench', 'start'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Not enough arguments!")
    else
        sys.exit()
    try:
        from config import CONFIG
    except ImportError:
        logging.exception("Error: config.py NOT found")
        sys.exit()
    #prepare logging handlers
    handler = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", "./script_log.log"))
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
    root.addHandler(handler)
    #call the main function
    main(sys.argv[1:])