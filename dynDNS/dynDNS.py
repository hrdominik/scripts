"""
Script for my Raspberry Pi that runs as an cronjob every 24h
gets the current external ip of my Router 
and set it as a CNAME on my domain hoehr.net on the subdomain pi

run this as CronJob like the following:
###
@daily /usr/bin/python3 /path/to/file/dynDNS.py
### or
0 0 * * * 
###

@author: DHR
@last-modified: 23.01.2022
"""
from email import message
import os
from dotenv import load_dotenv
import logging as log
import requests
import smtplib, ssl

def getCurrentExternalIP():
    Response = requests.get('https://ipinfo.io/ip')
    if Response.status_code != requests.codes.ok:
        raise Exception
    return Response.text


def callPhpApi(api, action, jsonData):
    data = {'action': action, 'param': jsonData}
    Response = requests.post(api, json=data)
    if Response.status_code != requests.codes.ok:
        raise Exception
    return Response.json()['responsedata']

def login2API(apiSettings):
    jsonData = {'customernumber':apiSettings['user'], 'apikey':apiSettings['apikey'], 'apipassword':apiSettings['apipassword']}
    ResponseData = callPhpApi(apiSettings['api'], 'login', jsonData)
    return ResponseData['apisessionid']

def logoutFromAPI(apiSettings):
    jsonData = {'customernumber':apiSettings['user'], 'apikey':apiSettings['apikey'], 'apisessionid':apiSettings['apisessionid']}
    callPhpApi(apiSettings['api'], 'logout', jsonData)


def updateDNSRecord(apiSettings, currIP, domain, record, hostname):
    dnsRecordSet = {'dnsrecords': [{"id":record, "hostname": hostname, "type": "CNAME", "priority": "0", "destination": currIP, "deleterecord": False, "state": "yes"}]}
    jsonData = {'domainname': domain, 'dnsrecordset': dnsRecordSet, 'customernumber':apiSettings['user'], 'apikey':apiSettings['apikey'], 'apisessionid':apiSettings['apisessionid']}
    print(jsonData)
    callPhpApi(apiSettings['api'], 'updateDnsRecords', jsonData)


def sendLogMail(content, mailSettings, receiver):
    context = ssl.create_default_context()
    msg = "{content}\n\n{furtherContent}\n\nPlease do not reply to this Email. If you wish to contact the Administrator write an Email to {adminMail}!"
    message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format(mailSettings['sender'], receiver, content['subject'], msg)
    
    with smtplib.SMTP_SSL(mailSettings['server'], mailSettings['port'], context=context) as server:
        server.login(mailSettings['sender'], mailSettings['password'])
        message = message.format(subject=content['subject'], content=content['content'], furtherContent=content['furtherContent'], adminMail=mailSettings['adminMail'])
        server.sendmail(mailSettings['sender'], receiver, message)



def main():
    logFilename = 'dynDNS.log'
    log.basicConfig(filename=logFilename, level=log.INFO)

    load_dotenv()
    load_dotenv('credentials.env')

    mailSettings = {'sender': os.getenv('MAIL_SENDER'), 'password': os.getenv('MAIL_PW'), 'server': os.getenv('MAIL_SERVER'), 'port': os.getenv('MAIL_PORT'), 'adminMail': os.getenv('MAIL_ADMIN')}
    mailContent = {'subject': 'Systemnotification from your dynDNS running on your Raspberry Pi', 'content': 'The Service {service} Today!'}

    apiSettings = {'api': os.getenv('API'), 'apikey': os.getenv('API_KEY'), 'apipassword': os.getenv('API_PW'), 'user': int(os.getenv('API_USER_ID'))}
    
    try:
        currentExternalIP = getCurrentExternalIP()
        apiSettings['apisessionid'] = login2API(apiSettings)
        updateDNSRecord(apiSettings, currentExternalIP, os.getenv('DOMAIN'), os.getenv('DNS_RECORD'), os.getenv('DNS_HOSTNAME'))
        logoutFromAPI(apiSettings)
        mailContent['content'] = mailContent['content'].format(service='run successful')
        mailContent['furtherContent'] = 'Your current External IP: ' + currentExternalIP
        # sendLogMail(mailContent, mailSettings, os.getenv('MAIL_RECEIVER'))
        log.info('dynDNS run successful Today!')
    except:
        log.critical('dynDNS failed Today!')
        mailContent['content'] = mailContent['content'].format(service='failed')
        mailContent['furtherContent'] = 'See {logFilename} for further informtaion'.format(logFilename=logFilename)
        # sendLogMail(mailContent, mailSettings, os.getenv('MAIL_RECEIVER'))


if __name__ == "__main__":
    main()