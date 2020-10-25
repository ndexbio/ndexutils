# -*- coding: utf-8 -*-

import os
import logging
import ndexutil
import json
import requests
import pandas
from ndexutil.argparseutil import ArgParseFormatter
from ndexutil.config import NDExUtilConfig

from ndexutil.exceptions import NDExUtilError
from ndex2.client import Ndex2
import ndex2

# create logger
logger = logging.getLogger('ndexutil.reports')


class FeaturedNetworkReportCommand(object):
    """
    Updates network in NDEx with Networkx layout
    """
    COMMAND = 'featurednetworkreport'
    UUID_KEY = 'UUID'
    TYPE_KEY = 'Type'
    TITLE_KEY = 'FeaturedNetworkTitle'
    OWNER_KEY = 'Owner'
    NET_UUID_KEY = 'NetworkUUID'
    NUM_NODES_KEY = 'NumberNodes'
    NUM_EDGES_KEY = 'NumberEdges'
    HAS_LAYOUT_KEY = 'HasLayout'
    NET_NAME_KEY = 'NetworkName'

    HEADER_LIST = [UUID_KEY, TYPE_KEY, TITLE_KEY, OWNER_KEY, NET_UUID_KEY,
                   NUM_NODES_KEY, NUM_EDGES_KEY, HAS_LAYOUT_KEY, NET_NAME_KEY]

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._server = self._args.server

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        if self._server != '-':
            return

        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()

        if self._server == '-':
            self._server = con.get(self._args.profile, NDExUtilConfig.SERVER)

    def _get_client(self):
        """
        Gets Ndex2 client
        :return: Ndex2 python client
        :rtype: :py:class:`~ndex2.client.Ndex2`
        """
        return Ndex2(self._server)

    def run(self):
        """
        :raises NDExUtilError if there is an error
        :return: number of attributes updated upon success
        """

        logger.warning('THIS IS AN UNTESTED ALPHA IMPLEMENTATION '
                       'AND MAY CONTAIN ERRORS')

        self._parse_config()
        client = self._get_client()
        feat_nets = self.get_featured_networks_as_json()
        report_dict = dict()
        for key in FeaturedNetworkReportCommand.HEADER_LIST:
            report_dict[key] = []

        if 'items' not in feat_nets:
            raise NDExUtilError('Expected data under '
                                '\'items\' dict, but none found')

        for entry in feat_nets['items']:
            if 'type' not in entry:
                logger.error(str(entry) +
                             ' no \'type\' found for entry. Skipping')
                continue
            if entry['type'].lower() == 'user':
                self.add_user_networks_to_report(client=client,
                                                 report_dict=report_dict,
                                                 featured_entry=entry)
            elif entry['type'].lower() == 'network':
                self.add_network_to_report(client=client,
                                           report_dict=report_dict,
                                           net_uuid=entry['UUID'],
                                           featured_entry=entry)
            elif entry['type'].lower() == 'networkset':
                self.add_networkset_to_report(client=client,
                                              report_dict=report_dict,
                                              featured_entry=entry,
                                              networkset_id=entry['UUID'])
            else:
                logger.error('Unknown type: ' +
                             str(entry['type']) +
                             ' Skipping')

        df = pandas.DataFrame.from_dict(report_dict)
        logger.info('Resulting CSV size: ' + str(df.shape))
        df.to_csv(self._args.output)

    def append_featured_info(self, report_dict=None, featured_entry=None):
        """

        :param report_dict:
        :param featured_entry:
        :return:
        """
        report_dict[FeaturedNetworkReportCommand.UUID_KEY].append(featured_entry['UUID'])
        report_dict[FeaturedNetworkReportCommand.TYPE_KEY].append(featured_entry['type'])
        report_dict[FeaturedNetworkReportCommand.TITLE_KEY].append(featured_entry['title'])

    def add_networkset_to_report(self, client=None,
                                 report_dict=None,
                                 featured_entry=None,
                                 networkset_id=None):
        """

        :param client:
        :param report_dict:
        :param featured_entry:
        :param networkset_id:
        :return:
        """
        res = client.get_networkset(networkset_id)
        for net_set_id in res['networks']:
            self.add_network_to_report(client=client, report_dict=report_dict,
                                       featured_entry=featured_entry,
                                       net_uuid=net_set_id)

    def add_user_networks_to_report(self, client=None,
                                    report_dict=None,
                                    featured_entry=None):
        """

        :param report_dict:
        :param featured_entry:
        :return:
        """

        res = client.post('/search/user', json.dumps({'searchString': featured_entry['UUID']}))
        if not isinstance(res, dict):
            logger.error('Error trying to get user from id: ' + featured_entry['UUID'])
            return
        if 'resultList' not in res:
            logger.error('Expected \'resultList\' in dict, but not found: ' +
                         str(res))
            return
        if 'userName' not in res['resultList'][0]:
            logger.error('Expected \'userName\' under \'resultList\', but '
                         'not found: ' + str(res['resultList'][0]))
            return
        user_name = res['resultList'][0]['userName']
        logger.info('Looking at networks owned by user: ' + user_name)
        res = client.post('/search/network?size=10000', json.dumps({'searchString': '',
                                                                    'accountName': user_name}))
        if 'numFound' in res and res['numFound'] > 0:
            for sub_ent in res['networks']:
                self.add_network_to_report(client=client,report_dict=report_dict,
                                           featured_entry=featured_entry,
                                           summary=sub_ent)

        # gotta check for networksets for user now
        res = client.get('/user/' + featured_entry['UUID'] + '/networksets')
        for net_set in res:
            counter = 0
            for id_for_net in net_set['networks']:
                self.add_network_to_report(client=client, report_dict=report_dict,
                                           featured_entry=featured_entry,
                                           net_uuid=id_for_net)
                if counter > 500:
                    logger.warning('Only first 500 networks of ' +
                                   str(len(net_set['networks'])) +
                                   ' networks in : ' + featured_entry['title'] +
                                   ' will be checked: ')
                    break
                counter += 1

    def add_network_to_report(self, client=None,
                              report_dict=None,
                              featured_entry=None,
                              net_uuid=None,
                              summary=None):
        """

        :param client:
        :param report_dict:
        :param featured_entry:
        :param net_uuid:
        :param summary:
        :return:
        """
        if summary is None:
            summary = client.get_network_summary(net_uuid)

        if self._args.excludehaslayout is True:
            if summary['hasLayout'] is True:
                logger.debug('Skipping since --excludehaslayout flag is set')
                return True
        report_dict[FeaturedNetworkReportCommand.OWNER_KEY].append(summary['owner'])
        report_dict[FeaturedNetworkReportCommand.NET_UUID_KEY].append(summary['externalId'])
        report_dict[FeaturedNetworkReportCommand.NUM_NODES_KEY].append(summary['nodeCount'])
        report_dict[FeaturedNetworkReportCommand.NUM_EDGES_KEY].append(summary['edgeCount'])
        report_dict[FeaturedNetworkReportCommand.HAS_LAYOUT_KEY].append(summary['hasLayout'])
        report_dict[FeaturedNetworkReportCommand.NET_NAME_KEY].append(summary['name'])

        self.append_featured_info(report_dict=report_dict,
                                  featured_entry=featured_entry)
        return True

    def get_featured_networks_as_json(self):
        """

        :return:
        """
        if os.path.isfile(self._args.featuredjson):
            with open(self._args.featuredjson, 'r') as f:
                return json.load(f)

        if not self._args.featuredjson.startswith('http'):
            raise NDExUtilError(self._args.featuredjson +
                                ' is not a file and does '
                                'not start with http')
        res = requests.get(self._args.featuredjson)
        if res.status_code != 200:
            raise NDExUtilError('Received error status code when trying'
                                'to retreive featured network json: ' +
                                str(res.status_code))
        return res.json()


    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

Version {version}

The {cmd} command queries NDEx for featured networks and generates
a summary report on those networks in following format:

{header}

Example invocation:

ndexmisctools.py {cmd} public.ndexbio.org 

WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
         ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=FeaturedNetworkReportCommand.COMMAND,
                   header=','.join(FeaturedNetworkReportCommand.HEADER_LIST))

        parser = subparsers.add_parser(FeaturedNetworkReportCommand.COMMAND,
                                       help='Generates report on Featured '
                                            'networks',
                                       description=desc,
                                       formatter_class=ArgParseFormatter)
        parser.add_argument('server', help='NDEx server, if set to - then '
                                           'value from config will be used')
        parser.add_argument('--featuredjson',
                            default='https://home.ndexbio.org/landing_page_'
                                    'content/v2_4_2/featured_networks.json',
                            help='URL to featured networks json file OR'
                                 'path to local json file')
        parser.add_argument('--output',
                            help='Path to write CSV file')
        parser.add_argument('--excludehaslayout', action='store_true',
                            help='If set, omit networks that have a layout')
        return parser
