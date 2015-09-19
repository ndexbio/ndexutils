
from os import listdir
from os.path import isfile, join
import common_ndex_utilities

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
    common_ndex_utilities.upload_file(full_path, arg.server, arg.username, arg.password)
