import requests, json
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
import string
import ndex.client as nc

def get_networks_administered_ids(server, username, password):
    ndex = nc.Ndex(server, username, password)
    networks = ndex.search_networks("", username, block_size=1000)
    network_ids = []
    for network in networks:
        network_ids.append(network['externalId'] )
    return network_ids

def get_networks_administered(server, username, password):
    ndex = nc.Ndex(server, username, password)
    networks = ndex.search_networks("", username, block_size=1000)
    return networks

def change_network_version(network_id, server, username, password, version):
    ndex = nc.Ndex(server, username, password)
    network_profile = {"version":version}
    return ndex.update_network_profile(network_id, network_profile)

def change_network_description(network_id, server, username, password, description):
    ndex = nc.Ndex(server, username, password)
    network_profile = {"description":description}
    return ndex.update_network_profile(network_id, network_profile)

def delete_network(network_id, server, username, password):
    ndex = nc.Ndex(server, username, password)
    return ndex.delete_network(network_id)

def set_network_visibility(network_id, server, username, password, visibility):
    ndex = nc.Ndex(server, username, password)
    network_profile = {"visibility": visibility}
    return ndex.update_network_profile(network_id, network_profile)

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
