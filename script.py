import os
import sys
from subprocess import call
import time
import base64
import xml.etree.ElementTree as etree
import pexpect
from python_hosts import Hosts, HostsEntry
import logging
import logging.handlers
import json
from datetime import datetime, date
import requests
from urllib.request import urlopen,Request

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


def site_install_erpnext(plan, domain):
    print("site install erp next")
    child = pexpect.spawn("bench --site " + domain + " install-app erpnext", timeout = 3600)
    index = child.expect([".*\$ ", pexpect.EOF, pexpect.TIMEOUT])
    if index == 0 or index == 1 : 
        print("prompt $")
        site_set_limits(plan, domain)
    elif index == 2 :
        print("1 expect timeout")    

def site_set_limits(plan, domain):
    print("site set limits")
    if plan == 'free':
        child = pexpect.spawn("bench --site "+domain+" set-limits --limit users 3 --limit space 0.157", timeout = 3600)
        index = child.expect([".*\$ ", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0 or index == 1 : 
            print("prompt $")
        elif index == 2 :
            print("2 1 expect timeout")
    elif plan == 'standard' or plan == 'microsoft_standard':
        child = pexpect.spawn("bench --site "+domain+" set-limit users 5")
        index = child.expect(["$ ", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0 or index == 1 : 
            print("prompt $")
        elif index == 2 :
            print("2 2 expect timeout")
    save_site_to_hosts(domain)

def save_site_to_hosts(domain):
    print("save site to hosts")
    my_hosts = Hosts()
    new_entry = HostsEntry(entry_type='ipv4', address='127.0.0.1', names=[domain])
    my_hosts.add([new_entry])
    my_hosts.write()
    start_bench(domain)

def start_bench(domain):
    print("start bench")
    pexpect.run("bench --site " + domain + "clear-cache")
    pexpect.run("bench start")
    print("erpnext 0000")
    
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
    mysql_username = CONFIG['mysql_username']
    mysql_password = CONFIG['mysql_password']
    admin_password = CONFIG['admin_password']
    system_password = CONFIG['system_password']

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
                #print(response_data['result'])
            else :
                print(response_data['errors'])    
        except Exception as e:
            print('CREATE NEW RECORD REQUEST EXCEPTION =========================================== ')
            logging.exception("creating new record apported :" + str(e))
            sys.exit()


    domain += '.'+CONFIG['subdomain']
    if domain_created == 1 : 
        old_pwd = os.getcwd()
        os.chdir("/home/cselection/frappe-bench/")
        print("erpnext 1")
        pexpect.run("sudo systemctl start mariadb")
        pexpect.run("bench config dns-mulitenant on")
        print("erpnext 2")
        child = pexpect.spawn("bench new-site " + domain + " --admin-password " + admin_password + " --mariadb-root-username " + mysql_username + " --mariadb-root-password " + mysql_password , timeout=3600, encoding='utf-8')
        index = child.expect([".*\$ ", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0 or index == 1 : 
            print("prompt $")
            site_install_erpnext(plan, domain)
        elif index == 1 : 
            print("expect timout")
            


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