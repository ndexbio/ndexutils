import requests, json
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
import string


def get_networks_administered_ids(server, username, password):
    url = 'http://'+server+'/network/search/0/1000'
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

def get_networks_administered(server, username, password):
    url = 'http://'+server+'/network/search/0/1000'
    print 'Getting list of networks from ' + url + ' for ' + username;
    payload = {"accountName":username,"permission":"ADMIN","searchString":""}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json()

def change_network_version(network_id, server, username, password, version):
    url = 'http://'+server+'/network/' + network_id + '/summary'
    payload = {"version":version}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

def change_network_description(network_id, server, username, password, description):
    url = 'http://'+server+'/network/' + network_id + '/summary'
    payload = {"description":description}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

def delete_network(network_id, server, username, password):
    url = 'http://'+server+'/network/' + network_id;
    payload = {"visibility":"PRIVATE"}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.delete(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

def set_network_visibility(network_id, server, username, password, visibility):
    url = 'http://'+server+'/network/' + network_id + '/summary'
    payload = {"visibility": visibility}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

def upload_file(filename, server, username, password):
    fields = {

        'fileUpload': (filename, open(filename, 'rb'), 'application/octet-stream'),
        'filename': filename
    }

    m = MultipartEncoder(
        fields=fields
    )

    url = 'http://'+server+'/network/upload'
    headers = {
        'content-type': m.content_type,
    }

    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=m, headers=headers)
    if r.status_code == 204:
        print("Successfully uploaded " + filename)
    else:
        print("Failed to upload " + filename)

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)
