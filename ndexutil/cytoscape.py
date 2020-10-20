# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import tempfile
import ndexutil
import shutil
from ndexutil.config import NDExUtilConfig
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
    logger.warning('Unable to load py4cytoscape. Utilities '
                   'relying on Cytoscape will not work')


DEFAULT_CYREST_API = 'http://localhost:1234/v1'
"""
Default CyREST API URL
"""


def is_py4cytoscape_loaded():
    """

    :return:
    """
    return PY4CYTOSCAPE_LOADED


class Formatter(argparse.ArgumentDefaultsHelpFormatter,
                argparse.RawDescriptionHelpFormatter):
    pass


def download_network_from_ndex(client=None,
                               networkid=None,
                               destfile=None):
    """
    Downloads network from ndex storing in `destfile` in CX
    format
    :param client: NDEx 2 client
    :type client: `:py:class:~ndex2.client.Ndex2`
    :param networkid: UUID of network as
    :type networkid: str
    :param destfile: destination file for network
    :type destfile: str
    :return: None
    """
    logger.info('Downloading ' + destfile + ' with netid: ' + networkid)
    client_resp = client.get_network_as_cx_stream(networkid)
    with open(destfile, 'wb') as f:
        for chunk in client_resp.iter_content(chunk_size=8096):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return destfile


class CytoscapeLayoutCommand(object):
    """
    Updates network in NDEx with Cytoscape layout
    """
    COMMAND = 'cytoscapelayout'
    LIST_LAYOUT = 'listlayout'
    LIST_LAYOUTS = LIST_LAYOUT + 's'

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._user = self._args.username
        self._pass = self._args.password
        self._server = self._args.server
        self._tmpdir = None  # set in run() function

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
        if is_py4cytoscape_loaded() is False:
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

        self._parse_config()
        client = self._get_client()
        self._tmpdir = tempfile.mkdtemp(prefix=self._args.tmpdir)
        try:
            input_cx_file = os.path.join(self._tmpdir, self._args.uuid + '.cx')
            download_network_from_ndex(client=client, networkid=self._args.uuid,
                                       destfile=input_cx_file)
            net_dict = self.load_network_in_cytoscape(input_cx_file)
            self.apply_layout(network_suid=net_dict['networks'][0])
            res_cx_file = self.export_network_to_tmpdir(network_suid=net_dict['networks'][0])

            # remove network from Cytoscape
            self.delete_network(network_suid=net_dict['networks'][0])

            if self._args.skipupload is True:
                return 0

            self.update_layout_aspect_on_ndex(cxfile=res_cx_file)

            return 0
        finally:
            shutil.rmtree(self._tmpdir)

    def delete_network(self, network_suid=None):
        """

        :param network_suid:
        :return:
        """
        py4.delete_network(network=network_suid,
                           base_url=self._args.cyresturl)

    def update_layout_aspect_on_ndex(self, cxfile=None):
        """

        :param cxfile:
        :return:
        """
        return

    def export_network_to_tmpdir(self, network_suid=None):
        """

        :param network_suid:
        :return:
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
        res = py4.export_network(filename=destfile, type='CX',
                                 network=network_suid,
                                 base_url=self._args.cyresturl)
        logger.info(res)
        return destfile

    def apply_layout(self, network_suid=None):
        """

        :param network_suid:
        :return:
        """
        res = py4.layout_network(layout_name=self._args.layout,
                                 network=network_suid,
                                 base_url=self._args.cyresturl)
        logger.debug(res)
        return None

    def load_network_in_cytoscape(self, input_cx_file):
        """

        :param input_cx_file:
        :return:
        """
        return py4.import_network_from_file(input_cx_file,
                                            base_url=self._args.cyresturl)

    @staticmethod
    def get_cytoscape_check_message():
        """

        :return:
        """
        if is_py4cytoscape_loaded() is False:
            return '\nERROR: It appears py4cytoscape is NOT installed ' \
                   'to use this tool run pip install py4cytoscape ' \
                   'and run this tool again.\n'

        try:
            py4.cytoscape_ping()
        except Exception as e:
            return '\nWARNING: A locally running Cytoscape was not found ' \
                   'so unable to list layouts. Please start ' \
                   'Cytoscape on this machine or ignore this ' \
                   'message if --cyresturl is set since this ' \
                   'help tool is run before command line options ' \
                   'are parsed\n'
        return ''

    @staticmethod
    def get_supported_layouts(cyresturl=DEFAULT_CYREST_API):
        """
        Gets supported layouts as list of `str`
        :return: list of supported layouts or `None` if unable to
                 query cytoscape or if py4cytoscape library is not
                 found
        :rtype: list
        """

        try:
            py4.cytoscape_ping(base_url=cyresturl)
        except Exception as e:
            return '\nA running Cytoscape was not found at: ' + \
                   cyresturl + ' Please start Cytoscape or ' \
                               'check value of --cyresturl\n'
        try:
            layout_mapping = py4.get_layout_name_mapping(base_url=cyresturl)
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
                                       formatter_class=Formatter)
        parser.add_argument('layout',
                            help='Name of layout to run. Set layout name'
                                 'to ' +
                                 CytoscapeLayoutCommand.LIST_LAYOUT +
                                 ' to see all options')
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
        parser.add_argument('--outputcx',
                            help='If set, CX will be written to this file')
        parser.add_argument('--cyresturl', default=DEFAULT_CYREST_API,
                            help='URL of CyREST API. Default value'
                                 'is default for locally running Cytoscape')

        return parser