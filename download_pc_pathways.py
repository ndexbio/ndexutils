__author__ = 'dexter'

from os import listdir, makedirs
from os.path import isfile, join, abspath, dirname, exists
import datetime
import pc.pathway_commons_api as pca


#def create_download_file(directory, name):


# body

import argparse

parser = argparse.ArgumentParser(description='download all pathways for a pathway commons datasource in a specified format')

parser.add_argument('datasource', action='store')
parser.add_argument('format', action='store')

arg = parser.parse_args()

# instantiate a pathway commons object

pc = pca.PathwayCommonsV2()

# check that the datasource is known and the format is known
datasource = pc.check_datasource(arg.datasource)
format = pc.check_format(arg.format)
if datasource and format:

    # create a directory in the downloads folder for this operation
    # with a unique name: datasource-format-time
    # (the user can remove old download directories manually with standard command line operations)
    current_directory = dirname(abspath(__file__))
    sub = datasource + "_" + format + "_" + datetime.datetime.now().isoformat()
    output_directory = join(current_directory, "downloads", sub)
    print "Creating " + str(output_directory)
    if not exists(output_directory):
        makedirs(output_directory)

    # get the pathway information for the datasource
    info = pc.get_pathway_info_for_datasource(datasource)
    hits = info.get("searchHit")

    count = 0
    # iterate over the pathways to get the data and save in a new file in the directory
    for pathway in hits:
        #print str(pathway)
        pathway_name = pathway.get("name")
        print pathway_name + " (" + pathway.get("uri") + ")"
        
        text = pc.get_pathway_ebs_by_uri(pathway.get("uri"))
        filename = join(output_directory, pathway_name + ".txt")
        file = open(filename, "w")
        file.write(text)
        file.close()
        
        count = count + 1
        if count > 5:
            break

else:
    if not datasource:
        print "bad datasource " + arg.datasource
    if not format:
        print "bad format " + arg.format


