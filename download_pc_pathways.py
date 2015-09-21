__author__ = 'dexter'

from os import listdir, makedirs
from os.path import isfile, join, abspath, dirname, exists
import datetime
import pc.pathway_commons_api as pca
import common_ndex_utilities


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
failures = []
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

    # iterate over the pathways to get the data and save in a new file in the directory
    for pathway in hits:
        #print str(pathway)
        pathway_name = common_ndex_utilities.sanitize_filename(pathway.get("name"))

        print pathway_name + " (" + pathway.get("uri") + ")"

        try:
            text = pc.get_pathway_ebs_by_uri(pathway.get("uri"))
            filename = join(output_directory, pathway_name + ".sif")
            file = open(filename, "w")
            file.write(text)
            file.close()
        except Exception, e:
            failures.append(pathway_name)
            #print "error getting pathway file: " + pathway_name + " => " + str(e)

else:
    if not datasource:
        print "bad datasource " + arg.datasource
    if not format:
        print "bad format " + arg.format

if len(failures) > 0:
    print "Failed pathways"
    for name in failures:
        print name
