# -*- coding: utf-8 -*-

import os
import sys
import logging
import tempfile
import ndexutil
import shutil
import ijson
import json
from ndexutil.config import NDExUtilConfig
from ndexutil.ndex import NDExExtraUtils
from ndexutil.argparseutil import ArgParseFormatter
from ndexutil.exceptions import NDExUtilError
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2.client import Ndex2
import ndex2


# create logger
logger = logging.getLogger('ndexutil.cytoscape')


try:
    import py4cytoscape as py4

    PY4CYTOSCAPE_LOADED = True
    py4.py4cytoscape_logger.summary_logger.setLevel(logging.FATAL)
    py4.py4cytoscape_notebook.detail_logger.setLevel(logging.FATAL)
except ImportError as ie:
    PY4CYTOSCAPE_LOADED = False
    logger.debug('Unable to load py4cytoscape. Utilities '
                 'relying on Cytoscape will not work : ' + str(ie))


DEFAULT_CYREST_API = 'http://localhost:1234/v1'
"""
Default CyREST API URL
"""


class Py4CytoscapeWrapper(object):
    """
    Wrapper for py4cytoscape calls
    """

    def __init__(self):
        """
        Constructor
        """
        self._py4loaded = PY4CYTOSCAPE_LOADED

    def is_py4cytoscape_loaded(self):
        """

        :return:
        """
        return self._py4loaded

    def cytoscape_ping(self, base_url=DEFAULT_CYREST_API):
        """

        :return:
        """
        return py4.cytoscape_ping(base_url=base_url)

    def delete_network(self, network=None,
                       base_url=DEFAULT_CYREST_API):
        return py4.delete_network(network=network,
                                  base_url=base_url)

    def export_network(self, filename=None,
                       type=None, network=None,
                       base_url=DEFAULT_CYREST_API):
        """

        :param filename:
        :param type:
        :param network:
        :param base_url:
        :return:
        """
        return py4.export_network(filename=filename,
                       type=type, network=network,
                       base_url=base_url)

    def layout_network(self, layout_name=None,
                       network=None, base_url=DEFAULT_CYREST_API):
        """

        :param layout_name:
        :param network:
        :param base_url:
        :return:
        """
        return py4.layout_network(layout_name=layout_name,
                                  network=network, base_url=base_url)

    def import_network_from_file(self, input_cx_file,
                                 base_url=DEFAULT_CYREST_API):
        """

        :param input_cx_file:
        :param base_url:
        :return:
        """
        return py4.import_network_from_file(input_cx_file,
                                            base_url=base_url)

    def get_layout_name_mapping(self, base_url=DEFAULT_CYREST_API):
        """

        :param base_url:
        :return:
        """
        return py4.get_layout_name_mapping(base_url=base_url)


class CytoscapeLayoutCommand(object):
    """
    Updates network in NDEx with Cytoscape layout
    """
    COMMAND = 'cytoscapelayout'
    LIST_LAYOUT = 'listlayout'
    LIST_LAYOUTS = LIST_LAYOUT + 's'

    def __init__(self, theargs,
                 ndexextra=NDExExtraUtils(),
                 py4cyto=Py4CytoscapeWrapper(),
                 altclient=None):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._user = self._args.username
        self._pass = self._args.password
        self._server = self._args.server
        self._tmpdir = None  # set in run() function
        self._ndexextra = ndexextra
        self._altclient = altclient
        self._py4 = py4cyto

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        if self._user != '-' and self._pass != '-' and self._server != '-':
            return
        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()
        if self._user == '-':
            self._user = con.get(self._args.profile, NDExUtilConfig.USER)

        if self._pass == '-':
            self._pass = con.get(self._args.profile, NDExUtilConfig.PASSWORD)

        if self._server == '-':
            self._server = con.get(self._args.profile, NDExUtilConfig.SERVER)

    def _get_client(self):
        """
        Gets Ndex2 client
        :return: Ndex2 python client
        :rtype: :py:class:`~ndex2.client.Ndex2`
        """
        if self._altclient is not None:
            return self._altclient
        return Ndex2(self._server, self._user, self._pass)

    def run(self):
        """
        Connects to NDEx server, gets network attributes for network
        with --uuid set on command line, updates network attributes
        with value set in --name, --value, --type and uses
        PUT network/<NETWORKID>/properties endpoint to update
        the network attributes for network
        :raises NDExUtilError if there is an error
        :return: number of attributes updated upon success
        """
        if self._py4.is_py4cytoscape_loaded() is False:
            logger.fatal('py4cytoscape library not found. cytoscapelayout '
                         'command cannot be run')
            return 1

        logger.warning('THIS IS AN UNTESTED ALPHA IMPLEMENTATION '
                       'AND MAY CONTAIN ERRORS')

        if self._args.layout == CytoscapeLayoutCommand.LIST_LAYOUT or \
                self._args.layout == CytoscapeLayoutCommand.LIST_LAYOUTS:
            sys.stdout.write(CytoscapeLayoutCommand.
                             get_supported_layouts(self._args.cyresturl))
            return 0

        if self._args.layout == '-':
            self._args.layout = 'force-directed-cl'

        self._parse_config()
        client = self._get_client()
        self._tmpdir = tempfile.mkdtemp(prefix=self._args.tmpdir)
        net_suid = None
        try:
            input_cx_file = os.path.join(self._tmpdir, self._args.uuid + '.cx')
            self._ndexextra.download_network_from_ndex(client=client,
                                                       networkid=self._args.uuid,
                                                       destfile=input_cx_file)

            if self._args.updatefullnetwork is False:
                self.add_node_id_node_attribute(input_cx_file=input_cx_file)

            net_dict = self.load_network_in_cytoscape(input_cx_file)
            if 'networks' not in net_dict:
                logger.fatal('Error network view could not '
                             'be created, this could be cause '
                             'this network is larger then '
                             '100,000 edges. Try increasing '
                             'viewThreshold property in '
                             'Cytoscape preferences')
                return 1
            net_suid = net_dict['networks'][0]

            self.apply_layout(network_suid=net_suid)

            res_cx_file = self.export_network_to_tmpdir(network_suid=net_suid)

            if self._args.skipupload is True:
                return 0

            if os.path.isfile(res_cx_file) and \
                    os.path.getsize(res_cx_file) > 0:
                if self._args.updatefullnetwork is True:
                    self.update_network_on_ndex(client=client,
                                                cxfile=res_cx_file)
                else:
                    u_cx_file = self.\
                        extract_layout_aspect_from_cx(input_cx_file=res_cx_file)
                    self.update_layout_aspect_on_ndex(client=client,
                                                      cxfile=u_cx_file)

            return 0
        finally:
            # remove network from Cytoscape
            self.delete_network(network_suid=net_suid)
            shutil.rmtree(self._tmpdir)

    def delete_network(self, network_suid=None):
        """
        Deletes network from Cytoscape

        :param network_suid: id of network
        :return:
        """
        if network_suid is None:
            return

        if self._args.skipdelete is True:
            return

        try:
            logger.info('Deleting network with id ' +
                        str(network_suid) + ' from Cytoscape')
            self._py4.delete_network(network=network_suid,
                                     base_url=self._args.cyresturl)
        except Exception as e:
            logger.error('Caught exception trying to delete network: ' +
                         str(e))

    def update_layout_aspect_on_ndex(self, client=None,
                                     cxfile=None):
        """

        :param cxfile:
        :return:
        """
        with open(cxfile, 'r') as f:
            jdata = json.load(f)

        res = self._ndexextra.update_network_aspect_on_ndex(client=client,
                                                            networkid=self._args.uuid,
                                                            aspect_name='cartesianLayout',
                                                            aspect_data=jdata)
        logger.info('Result from aspect update: ' + str(res))

        return

    def update_network_on_ndex(self, client=None,
                               cxfile=None):
        """

        :param client:
        :param cxfile:
        :return:
        """
        logger.info('Update network with id: ' +
                    str(self._args.uuid) + ' on NDEx server: ' +
                    str(self._server))
        with open(cxfile, 'rb') as f:
            res = client.update_cx_network(f, self._args.uuid)
            logger.debug('Result from update: ' + str(res))
            return res

    def export_network_to_tmpdir(self, network_suid=None):
        """
        Exports network with id `network_suid` to temp directory
        in CX format.

        :param network_suid:
        :return: path to exported file
        :rtype: str
        """
        if self._args.outputcx is not None:
            destfile = os.path.abspath(self._args.outputcx)
        else:
            destfile = os.path.join(self._tmpdir,
                                    self._args.uuid + '.wlayout.cx')

        if os.path.isfile(destfile):
            logger.debug(destfile + ' exists. Removing so '
                                    'Cytoscape does not hang'
                                    'asking if user wants'
                                    'to remove file')
            os.unlink(destfile)

        logger.info('Writing cx to: ' + destfile)
        res = self._py4.export_network(filename=destfile, type='CX',
                                       network=network_suid,
                                       base_url=self._args.cyresturl)
        logger.info(res)
        return destfile

    def apply_layout(self, network_suid=None):
        """
        Apply layout to network in Cytoscape

        :param network_suid:
        :return:
        """
        logger.info('Applying layout ' + self._args.layout +
                    ' on network with suid: ' +
                    str(network_suid) + ' in Cytoscape')
        res = self._py4.layout_network(layout_name=self._args.layout,
                                       network=network_suid,
                                       base_url=self._args.cyresturl)
        logger.debug(res)
        return None

    def add_node_id_node_attribute(self, input_cx_file):
        """

        :param input_cx_file:
        :return:
        """
        self._ndexextra.add_node_id_as_node_attribute(cxfile=input_cx_file,
                                                      outcxfile=input_cx_file)
        shutil.copyfile(input_cx_file, '/Users/churas/Desktop/well.cx')

    def load_network_in_cytoscape(self, input_cx_file):
        """
        Loads network from file into Cytoscape

        :param input_cx_file:
        :return:
        """
        file_size = os.path.getsize(input_cx_file)

        logger.info('Importing network from file: ' + input_cx_file +
                    ' (' + str(file_size) + ' bytes) into Cytoscape')
        return self._py4.import_network_from_file(input_cx_file,
                                                  base_url=self._args.cyresturl)

    def extract_layout_aspect_from_cx(self, input_cx_file):
        """
        Given a CX file, this method find the, cartesianLayout,
        if any, and writes it to a file in the temp directory.

        :param input_cx_file:
        :type input_cx_file: str
        :return: path to file containing cartesianLayout aspect
                 or `None` if that aspect is NOT found
        :rtype: str
        """
        res = self._ndexextra.extract_layout_aspect_from_cx(input_cx_file=input_cx_file)
        output_cx_file = os.path.join(self._tmpdir, 'cartlayout.json')
        if res is not None:
            with open(output_cx_file, 'w') as outfp:
                json.dump(res, outfp)
            return output_cx_file
        return None

    @staticmethod
    def get_cytoscape_check_message(py4_wrapper=Py4CytoscapeWrapper()):
        """

        :return:
        """
        if py4_wrapper.is_py4cytoscape_loaded() is False:
            return '\nERROR: It appears py4cytoscape is NOT installed ' \
                   'to use this tool run pip install py4cytoscape ' \
                   'and run this tool again.\n'

        try:
            py4_wrapper.cytoscape_ping()
        except Exception as e:
            return '\nWARNING: A locally running Cytoscape was not found ' \
                   'so unable to list layouts. Please start ' \
                   'Cytoscape on this machine or ignore this ' \
                   'message if --cyresturl is set since this ' \
                   'help tool is run before command line options ' \
                   'are parsed\n'
        return ''

    @staticmethod
    def get_supported_layouts(cyresturl=DEFAULT_CYREST_API,
                              py4_wrapper=Py4CytoscapeWrapper()):
        """
        Gets supported layouts as list of `str`
        :return: list of supported layouts or `None` if unable to
                 query cytoscape or if py4cytoscape library is not
                 found
        :rtype: list
        """
        try:
            py4_wrapper.cytoscape_ping(base_url=cyresturl)
        except Exception as e:
            return '\nA running Cytoscape was not found at: ' + \
                   cyresturl + ' Please start Cytoscape or ' \
                               'check value of --cyresturl : ' + str(e) + '\n'
        try:
            layout_mapping = py4_wrapper.get_layout_name_mapping(base_url=cyresturl)
            if layout_mapping is None:
                logger.debug('Layout mapping was None')
                return '\nNo layouts found\n'
            if len(layout_mapping.keys()) == 0:
                logger.debug('Layout mapping was empty')
                return '\nNo layouts found\n'
            res = '\nLayout Name\n\t-- Layout Name as seen in Cytoscape\n\n'
            for key in layout_mapping:
                res = res + '' + layout_mapping[key] + '\n\t-- '\
                      + key + '\n\n'
            return res + '\n'
        except Exception as e:
            logger.info('Unable to get layout names : ' + str(e))
        return '\nUnable to get list of layouts\n'

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

Version {version}

The {cmd} command updates layout on a network in NDEx using Cytoscape.
The network can be specified by NDEx UUID via --uuid flag.

{cytocheck}

Example:

ndexmisctools.py cytoscapelayout perforce - - - --uuid XXXX-XXX

WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
         ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=CytoscapeLayoutCommand.COMMAND,
                   cytocheck=CytoscapeLayoutCommand.get_cytoscape_check_message())

        parser = subparsers.add_parser(CytoscapeLayoutCommand.COMMAND,
                                       help='Updates layout of network via '
                                            'Cytoscape',
                                       description=desc,
                                       formatter_class=ArgParseFormatter)
        parser.add_argument('layout',
                            help='Name of layout to run. Set layout name '
                                 'to ' +
                                 CytoscapeLayoutCommand.LIST_LAYOUT +
                                 ' to see all options. If set to - '
                                 'default layout of force-directed-cl '
                                 'will be used')
        parser.add_argument('username', help='NDEx username, if set to - '
                                             'then value from config will '
                                             'be used')
        parser.add_argument('password', help='NDEx password, if set to - '
                                             'then value from config will '
                                             'be used')
        parser.add_argument('server', help='NDEx server, if set to - then '
                                           'value from config will be used')
        parser.add_argument('--uuid',
                            help='The UUID of network in NDEx to update',
                            required=True)
        parser.add_argument('--layoutoptions',
                            help='Options to pass to layout. NOT supported '
                                 'yet')
        parser.add_argument('--tmpdir',
                            help='Sets temp directory used for processing. If '
                                 'not set, then directory used is the '
                                 'default for Python\'s '
                                 'tempfile.mkdtemp() function')
        parser.add_argument('--skipupload', action='store_true',
                            help='If set, layout will NOT updated for '
                                 'network in NDEx')
        parser.add_argument('--skipdelete', action='store_true',
                            help='If set, skips delete of network from '
                                 'Cytoscape')
        parser.add_argument('--outputcx',
                            help='If set, CX will be written to this file')
        parser.add_argument('--cyresturl',
                            default=DEFAULT_CYREST_API,
                            help='URL of CyREST API. Default value'
                                 'is default for locally running Cytoscape')
        parser.add_argument('--updatefullnetwork', action='store_true',
                            help='If set, Update entire network on NDEx instead of '
                                 'just the cartesianLayout aspect')
        return parser