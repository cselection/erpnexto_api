import os
import sys
from subprocess import call
import time
import base64
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from urllib import parse
import xml.etree.ElementTree as etree
import pexpect
from python_hosts import Hosts, HostsEntry
import logging
import logging.handlers
import json
from datetime import datetime, date
import requests
'''
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
    return ip '''

#verify the current cloudflare toekn 
def verify_cloudflare_token():
    try:
        request = Request('https://api.cloudflare.com/client/v4/user/tokens/verify', method='GET')
        request.add_header('Authorization', 'Bearer %s' % CONFIG['cloudflare_read_tokens_token'])
        request.add_header('Content-Type', 'application/json')
        request.add_header('User-Agent', CONFIG['user_agent'])
        with urlopen(request, timeout=20) as response:
            #if request was successfull
            if response.getcode() == 200:
                response_data = response.read().decode(response.info().get_param('charset') or 'utf-8')
                data = json.loads(response_data)
                token_status = data['result']['status']
                # if token is active return 1
                if token_status == 'active':
                    return 1
            #if request is unauthorized
            elif response.getcode() == 403:
                logging.info("verify current token request is unauthorized")
            #if something went wrong
            else: 
                logging.info("couldn't make verify current token request")
            return 0
    except Exception as e:
       print('VERIFY CURRENT TOKEN REQUEST EXCEPTION =========================================== '+ str(e))
       logging.exception("verify current token exception : " + str(e) + "\n")
       logging.exception("-------------------------------")
       sys.exit()

#issue a new token from cloudflare api
def create_new_cloudflare_token():
    try:
        response_dic = {'status' : 404, 'token' : ''}
        print("0")
        create_new_token_data = {
                                    "name":"readonly token",
                                    "not_before": datetime.now(),
                                    "expires_on": date.today(),
                                    "policies":
                                        [
                                            {
                                                "id":"f267e341f3dd4697bd3b9f71dd96247f",
                                                "effect":"allow",
                                                "resources":
                                                    {
                                                        "com.cloudflare.api.account.zone.2a8aca5cba7eb3c5796b491c564c8dc8": "*",
                                                    },
                                                "permission_groups":
                                                    [
                                                        {
                                                            "id":"c8fed203ed3043cba015a93ad1616f1f",
                                                            "name":"Zone Read"
                                                        },
                                                        {
                                                            "id":"82e64a83756745bbbb1c9c2701bf816b",
                                                            "name":"DNS Read"
                                                        }
                                                    ]
                                            }
                                        ],
                                    "condition":
                                        {
                                            "request.ip" :
                                                {
                                                    "in":
                                                        [
                                                            "197.57.133.44",
                                                            "54.86.50.139"
                                                        ]
                                                }
                                        }
                                }
        request = Request('https://api.cloudflare.com/client/v4/user/tokens', method='POST', data=urlencode(create_new_token_data).encode('ascii'))
        request.add_header('Authorization', 'Bearer %s' % CONFIG['cloudflare_read_tokens_token'])
        request.add_header('Content-Type', 'application/json')
        request.add_header('User-Agent', CONFIG['user_agent'])
        with urlopen(request, timeout=20) as response:
            #if request was successfull
            if response.getcode() == 200:
                response_data = response.read().decode(response.info().get_param('charset') or 'utf-8')
                data = json.loads(response_data)
                new_token = data['result']['value']
                response_dic['status'] = 200
                response_dic['token'] = new_token
            #if request is unauthorized
            elif response.getcode() == 403:
                logging.info("create new token request is unauthorized")
            #if something went wrong
            else:
                logging.info("couldn't make create new token request")
            return response_dic
    except Exception as e:
       print('NEW TOKEN REQUEST EXCEPTION =========================================== '+ str(e))
       logging.exception("create new token exception : " + str(e) + "\n")
       logging.exception("-------------------------------")
       sys.exit()

####------------------------------------- main method -----------------------------
def main(argv):
    #get user data from client registration form
    site_name = argv[0]
    business_mail = argv[1]
    phone = argv[2]
    password = argv[3]
    plan = argv[4]

    #get all arguments needed to create a new A dns record
    ip = CONFIG['ip']
    ttl = CONFIG['record_ttl']
    record_type = CONFIG['record_type']
    domain = site_name

    #prepare some authentication data
    mysql_password = CONFIG['mysql_password']
    admin_password = CONFIG['admin_password']

    #prepare some helper data
    is_domain_available=0
    domain_created=0

    #---------------------------------------------------------------------------------------------------------#
    #Fetch existing DNS records on 'erpnexto.com' zone
    try:
        is_token_verified = verify_cloudflare_token()
        access_token = CONFIG['cloudflare_read_zone_token']
        if is_token_verified != 1:
            logging.info("the current token is not verified")
            access_token_dic = create_new_cloudflare_token()
            if access_token_dic['status'] == 200 :
                access_token = access_token_dic['token']
        request = Request('https://api.cloudflare.com/client/v4/zones/'+CONFIG['erpnexto_zone_id']+'/dns_records?type=CNAME&name='+domain+'&content='+CONFIG['subdomain']+'&proxied=true&page=1&per_page=20&order=type&direction=desc&match=all', method='GET')
        request.add_header('X-Auth-Key', '9f9fa825aad939ec61cc335bf0a423828856d')
        request.add_header('X-Auth-Email', 'erpnextosas@gmail.com')
        request.add_header('Content-Type', 'application/json')
        request.add_header('User-Agent', CONFIG['user_agent'])
        with urlopen(request, timeout=20) as response:
            #if request was successfull
            if response.getcode() == 200:
                response_data = response.read().decode(response.info().get_param('charset') or 'utf-8')
                data = json.loads(response_data)
                if len(data['result']) > 0:
                    logging.info("the requested domain is already taken")
                else:
                    is_domain_available=1
                    logging.info("the requested domain is available")
            #if request is unauthorized
            elif response.getcode() == 403:
                logging.info("sorry, you're not authorized to make the request")
            #if something went wrong
            else:
                logging.info("sorry, we couldn't make the request")
    except Exception as e:
       print('FETCH RECORDS REQUEST EXCEPTION =========================================== '+ str(e))
       logging.exception("fetching records exception : " + str(e) + "\n")
       logging.exception("-------------------------------")
       sys.exit()

    #---------------------------------------------------------------------------------------------------------#
    #add the new cname dns record
    if is_domain_available == 1 :
        try:
            data = { 'type':'CNAME', 'name':domain, 'content':CONFIG['subdomain'], 'ttl':1, 'priority':10, 'proxied':True }
            headers = {
                'X-Auth-Key': '9f9fa825aad939ec61cc335bf0a423828856d',
                'X-Auth-Email' : 'erpnextosas@gmail.com',
                'Content-Type' : 'application/json',
                'Accept' : '*/*',
                'User-Agent' : CONFIG['user_agent']
                }
            response = requests.post('https://api.cloudflare.com/client/v4/zones/'+CONFIG['erpnexto_zone_id']+'/dns_records', json=data, headers=headers)
            response_data = response.json()
            if response.status_code == requests.codes.ok :
                domain_created = 1
                print(response_data['result'])
            else :
                print(response_data['errors'])    
        except Exception as e:
            print('CREATE NEW RECORD REQUEST EXCEPTION =========================================== ')
            logging.exception("creating new record apported :" + str(e))
            sys.exit()


    if domain_created == 1 : 
        #make the suitable environment for the erpnext installation
        '''child = pexpect.spawn("apt install git python-dev redis-server")
        child = pexpect.spawn("apt-get install software-properties-common")
        child = pexpect.spawn("apt-get update")
        child = pexpect.spawn("apt-get install mariadb-server-10.3")
        child = pexpect.spawn("pip install frappe-bench")'''

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

        if plan == 'free':
            print('FREE EXCEPTION =========================================== ')
            out = subprocess.Popen(['bench', '--site', site_name, 'set-limits', '--limit', 'users', 3, '--limit', 'space', 0.157], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        elif plan == 'standard':
            print('STANDARD EXCEPTION =========================================== ')
            out = subprocess.Popen(['bench', '--site', site_name, 'set-limit', 'users', 8], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        #open /etc/hosts and add the new sub-domain as a new entry
        my_hosts = Hosts()
        new_entry = HostsEntry(entry_type='ipv4', address=ip, names=[site_name])
        my_hosts.add([new_entry])
        my_hosts.write()

        #start the user erpnext instance
        out = subprocess.Popen(['bench', 'start'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("too fre args")
    else:
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