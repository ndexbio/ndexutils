from nicecxModel.NiceCXNetwork import NiceCXNetwork
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--username", dest="username", help="NDEx account user name", metavar="USER")
parser.add_option("-p", "--password", dest="password", help="NDEx account password", metavar="PASS")
parser.add_option("-s", "--server", dest="server", help="NDEx server URL", metavar="SERVER")
parser.add_option("-i", "--uuid", dest="uuid", help="NDEx network id", metavar="UUID")
parser.add_option("-f", "--filename", dest="filename", help="Export file name", metavar="FILE")

(options, arg) = parser.parse_args()

input_error_message = []
if not options.server:
    input_error_message.append('Server is not specified')
if not options.uuid:
    input_error_message.append('UUID is not specified')

if len(input_error_message) > 0:
    raise Exception('Missing input: ' + ','.join(input_error_message))

niceCx = NiceCXNetwork()

#================================
# Load network from ndex server
#================================
niceCx.create_from_server(options.server, options.username, options.password, options.uuid)

#=============================
# convert to pandas dataframe
#=============================
my_pd = niceCx.to_pandas()

#=====================
# Export to csv file
#=====================
if options.filename is not None:
    my_pd.to_csv(options.filename, sep=',')
else:
    my_pd.to_csv('CXExport.csv', sep=',')

print 'Done'
