import certifi
import requests

try:
    print('Checking connection to Slack...')
    test = requests.get('https://accounts.google.com/.well-known/openid-configuration', verify="secrets/zscaler-root-ca.pem")
    print('Connection to Google OK.')
except requests.exceptions.SSLError as err:
    print('SSL Error. Adding custom certs to Certifi store...')
    cafile = certifi.where()
    with open('secrets/zscaler-root-ca.pem', 'rb') as infile:
        customca = infile.read()
    with open(cafile, 'ab') as outfile:
        outfile.write(customca)
    print('That might have worked.')