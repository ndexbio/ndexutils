
from os import listdir
from os.path import isfile, join
import csv
import ndex.client as nc
import time
import io
import sys

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
parser.add_argument('filename',   action='store', default='nci_pid_network_report.csv')
parser.add_argument('checkonly')
arg = parser.parse_args()

pid_table = {}

ndex = nc.Ndex(arg.server,arg.username, arg.password)

with open(arg.filename) as f:
  #  next(f) # skip headings
    reader=csv.DictReader(f,delimiter='\t')
    for row in reader:
        if not 'Corrected Pathway Name' in row or len(row['Corrected Pathway Name']) == 0:
            row['Corrected Pathway Name'] = row['Pathway Name']
        pid_table[row['Corrected Pathway Name']] = row

def getNetworkProperty(summary, prop_name):
    for prop in summary['properties']:
        if ( prop['predicateString'] == prop_name) :
            return prop['value']
    return None

check_only = True

if 'False' == arg.checkonly :
    check_only = False

no_sif_counter=0
not_found_counter=0
updated_counter = 0
for name in pid_table.keys():
    summaries = ndex.search_networks('name:"'+ name + '"', arg.username,0,10)
#    if len(summaries) > 2 :
#        print "Network '" + name + "' has " + str(len(summaries)) + " records. Will ignore it"
    if len(summaries) < 1 :
        print "Network '" + name + "'\tnot found!"
        not_found_counter +=1
    else :
        found = False
        for summary in summaries:
            srcFormat = getNetworkProperty(summary, 'sourceFormat')
            if (summary['name'] == name) and (( srcFormat == "SIF") or srcFormat== "BIOPAX") :
                net_uuid = summary['externalId']
                found = True
                updated_counter +=1

                if check_only:
                    break

                print "Processing Network [" + net_uuid+ "]("+ srcFormat+ ') ' + name + ' ... '
                rec = pid_table[name]

                props = summary['properties']

                props.append({'predicateString': 'PID_ID', 'value': rec['PID'], 'dataType': 'string'})
                props.append({'predicateString': 'Curated By', 'value': rec['Curated By'], 'dataType': 'string'})
                props.append({'predicateString': 'Reviewed By', 'value': rec['Reviewed By'], 'dataType': 'string'})
                props.append({'predicateString': 'Revision Date', 'value': rec['Revision Date'], 'dataType': 'string'})

                ndex.set_network_properties(net_uuid, props)

                downloadStr = 'This network belongs to the NCI-Nature curated Pathway Interaction Database (PID) and was obtained from Pathway Commons (PC2v.7)' + \
                              '<p/><p><a href="ftp://ftp.ndexbio.org/NCI_PID/biopax/PID_' + rec['PID'] + '.owl.zip">' + '<em>Download</em></a> BioPAX3 file.</p>'
                description = summary['description']
         #       if description :
         #           description = description + downloadStr
         #       else:
                description = downloadStr

                update_obj = {'description': description}
                if name != rec['Pathway Name']:
                    update_obj['name']= rec['Pathway Name']
                ndex.update_network_profile(net_uuid,update_obj)
                print "done.\n"
            else :
                print " .....  '" + summary['name'] + "' (" + getNetworkProperty(summary, 'sourceFormat') + ") in result. ignore it."
        if not found :
            print "Network '" + name + "'\tnot found."
            not_found_counter +=1

print str(updated_counter) + " networks " + (" found. " if check_only else " updated. ") + \
      str(not_found_counter) + " networks not found."


#filenames = get_filenames(arg.directory)
#for filename in filenames:
#    full_path = arg.directory + '/' + filename
#    common_ndex_utilities.upload_file(full_path, arg.server, arg.username, arg.password)
