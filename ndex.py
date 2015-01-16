import requests, json
from requests.auth import HTTPBasicAuth


def get_networks_administered_ids(username, password):
    url = 'http://54.148.42.155/rest/network/search/0/1000'
    payload = {"accountName":username,"permission":"ADMIN","searchString":""}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    network_ids = []
    networks = r.json()
    for network in networks:
        network_ids.append(network['externalId'] )
    return network_ids

def get_networks_administered(username, password):
    url = 'http://54.148.42.155/rest/network/search/0/1000'
    payload = {"accountName":username,"permission":"ADMIN","searchString":""}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.json()

