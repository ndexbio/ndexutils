import requests
from requests_toolbelt import MultipartEncoder
from os import listdir
from os.path import isfile, join
from requests.auth import HTTPBasicAuth


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

def get_filenames(dir):
    files = [ f for f in listdir(dir) if isfile(join(dir,f)) ]
    return files

# body

import argparse

parser = argparse.ArgumentParser(description='upload-to-ndex arguments')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('directory', action='store')
parser.add_argument('server', action='store')

arg = parser.parse_args()

filenames = get_filenames(arg.directory)
for filename in filenames:
    full_path = arg.directory + '/' + filename
    upload_file(full_path, arg.server, arg.username, arg.password)
