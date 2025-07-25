# Get IP adress
from ipwhois import IPWhois
from requests import get
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Get network information
print("> Server infos:")
ip = get('https://api.ipify.org').text
whois = IPWhois(ip).lookup_rdap(depth=1)
cidr = whois['network']['cidr']
name = whois['network']['name']

print('Provider:  ', name)
print('Public IP: ', ip)
print('CIDRs:     ', cidr)

print()

# Connect to database
uri = os.getenv('MONGODB_URI')
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
print("> Database connection...")
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(e)