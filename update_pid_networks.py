
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

cx_str = '[{"numberVerification": [{"longNumber": 281474976710655}]}, {"metaData": [{"idCounter": 4, "name": "nodes"}, {"idCounter": 4, "name": "edges"}]}, {"networkAttributes": [{"v": "indra_assembled", "n": "name"}, {"v": "", "n": "description"}]}, {"nodeAttributes": [{"v": "proteinfamily", "po": 0, "n": "type"}, {"v": "MEK", "po": 0, "n": "BE"}, {"v": "proteinfamily", "po": 1, "n": "type"}, {"v": "C26360", "po": 1, "n": "NCIT"}, {"v": "ERK", "po": 1, "n": "BE"}]}, {"edgeAttributes": [{"v": "Phosphorylation(MEK(), ERK())", "po": 2, "n": "INDRA statement"}, {"v": "Modification", "po": 2, "n": "type"}, {"v": "positive", "po": 2, "n": "polarity"}, {"v": "1.00", "po": 2, "n": "Belief score"}, {"v": "MEK phosphorylates ERK.", "po": 2, "n": "Text"}]}, {"edges": [{"i": "Phosphorylation", "s": 0, "@id": 2, "t": 1}]}, {"edgeSupports": [{"supports": [3], "po": [2]}]}, {"citations": []}, {"nodes": [{"@id": 0, "n": "MEK"}, {"@id": 1, "n": "ERK"}]}, {"supports": [{"text": "MEK phosphorylates ERK.", "@id": 3}]}, {"edgeCitations": []}]'

nd = nc.Ndex('http://preview.ndexbio.org',
                             username='cjtest',
                             password="guilan")

nd.set_debug_mode(True)

network_id = nd.save_cx_stream_as_new_network(cx_str)

parser = argparse.ArgumentParser(description='upload-to-ndex arguments')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('directory', action='store')
parser.add_argument('server', action='store')
parser.add_argument('filename', action='store', default='nci_pid_network_report.csv')

parser.add_argument('check_only', action='store', default=True)
arg = parser.parse_args()

pid_table = {}

ndex = nc.Ndex(arg.server,arg.username, arg.password)

with open(arg.filename) as f:
  #  next(f) # skip headings
    reader=csv.DictReader(f, dialect=csv.excel_tab,delimiter='\t')
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

if not arg.check_only :
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
            if ( getNetworkProperty(summary, 'sourceFormat') == "SIF") and (summary['name'] == name) :
                net_uuid = summary['externalId']
                if check_only:
                    found = True
                    updated_counter +=1
                    break
                print "Processing Network [" + net_uuid+ "] " + name + ' ... '
                original_provenance= ndex.get_provenance(net_uuid)
                rec = pid_table[name]
                rec['uuid'] = net_uuid

                result = ndex.upload_file(arg.directory + "/"+ name + ".sif")
                task_id = result['externalId']

                wait_cycle=0
                while task_id :
                    task = ndex.get_task_by_id(task_id)
                    if task['status'] == 'QUEUED' or task['status'] == 'PROCESSING' :
                        time.sleep(2)
                        if wait_cycle == 0 :
                            sys.stdout.write( "waiting for upload to finish.")
                            wait_cycle = 1
                        else:
                            sys.stdout.write( ".")
                    elif task['status'] == 'COMPLETED':
                        #download the network update the server
                        attrs = task['attributes']
                        new_net_uuid = attrs['networkUUID']
                        new_provenance = ndex.get_provenance(new_net_uuid)
                        cx_stream = io.BytesIO(ndex.get_network_as_cx_stream(new_net_uuid).content)

                        result = ndex.update_cx_network(cx_stream,net_uuid )
                        new_provenance['creationEvent']['inputs'] = [original_provenance]
                        ndex.set_provenance(net_uuid, new_provenance)
                        print "network updated. deleting temp network " + new_net_uuid + " .... "
                        ndex.delete_network(new_net_uuid)
                        print "done.\n"
                        found = True
                        updated_counter +=1
                        break
                    else:
                        print "network upload failed."
                        raise Exception("failed at network " + name )

                break
            else :
                print " .....  '" + summary['name'] + "' (" + getNetworkProperty(summary, 'sourceFormat') + ") in result. ignore it."
        if not found :
            print "Network '" + name + "'\tno SIF version."
            no_sif_counter +=1

print str(updated_counter) + " networks " + (" found. " if check_only else " updated.") + \
      str(not_found_counter) + " networks not found, and " + str(no_sif_counter) + " networks missing sif version."


#filenames = get_filenames(arg.directory)
#for filename in filenames:
#    full_path = arg.directory + '/' + filename
#    common_ndex_utilities.upload_file(full_path, arg.server, arg.username, arg.password)
