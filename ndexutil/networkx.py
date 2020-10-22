# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import tempfile
import ndexutil
import shutil
import json
from ndexutil.config import NDExUtilConfig

from ndexutil.exceptions import NDExUtilError
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import Ndex2
from ndex2.nice_cx_network import DefaultNetworkXFactory
import ndex2
import networkx

# create logger
logger = logging.getLogger('ndexutil.networkx')


SPRING_LAYOUT = 'spring'
"""
Spring layout
"""

CIRCULAR_LAYOUT = 'circular'
"""
Circular layout
"""

KAMADA_KAWAI_LAYOUT = 'kamada_kawai'

PLANAR_LAYOUT = 'planar'

SHELL_LAYOUT = 'shell'

SPECTRAL_LAYOUT = 'spectral'
SPIRAL_LAYOUT = 'spiral'


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


def convert_networkx_pos_to_cartesian_aspect(networkx_pos):
    """
    Converts node coordinates from a pos object
    to a list of dicts with following format:
    [{'node': <node id>,
      'x': <x position>,
      'y': <y position>}]
    :param G:
    :return: coordinates
    :rtype: list
    """
    return [{'node': n,
             'x': float(networkx_pos[n][0]),
             'y': float(networkx_pos[n][1])} for n in networkx_pos]


class NetworkxLayoutCommand(object):
    """
    Updates network in NDEx with Networkx layout
    """
    COMMAND = 'networkxlayout'

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

        logger.warning('THIS IS AN UNTESTED ALPHA IMPLEMENTATION '
                       'AND MAY CONTAIN ERRORS')

        self._parse_config()
        client = self._get_client()
        self._tmpdir = tempfile.mkdtemp(prefix=self._args.tmpdir)
        try:
            input_cx_file = os.path.join(self._tmpdir, self._args.uuid + '.cx')
            download_network_from_ndex(client=client, networkid=self._args.uuid,
                                       destfile=input_cx_file)

            aspect_data = self.apply_layout(cxfile=input_cx_file)

            if self._args.skipupload is True:
                logger.info('Skipping upload to NDEx')
                return 0


            self.update_layout_aspect_on_ndex(client=client,
                                              aspect_data=aspect_data)
            return 0
        finally:
            shutil.rmtree(self._tmpdir)

    def update_layout_aspect_on_ndex(self, client=None,
                                     aspect_data=None):
        """

        :param cxfile:
        :return:
        """
        logger.info('Updating layout on NDEx for network with uuid: ' +
                    self._args.uuid)
        net = NiceCXNetwork()
        net.set_opaque_aspect('cartesianLayout', aspect_data)

        theurl = '/network/' + self._args.uuid + '/aspects'
        logger.info(theurl)
        res = client.put(theurl,
                         put_json=json.dumps(net.to_cx()))
        logger.info('Result from put: ' + str(res))

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

    def get_center_as_list(self):
        """

        :return:
        """
        if self._args.center is None:
            return None

        return self._args.center.split(',')

    def apply_layout(self, cxfile=None):
        """
        Apply layout to network in Cytoscape

        :param network_suid:
        :return:
        """

        logger.info('Loading network')
        net = ndex2.create_nice_cx_from_file(cxfile)
        netx_fac = DefaultNetworkXFactory()
        netx_graph = netx_fac.get_graph(net)

        logger.info('Applying layout Networkx layout' +
                    self._args.layout +
                    ' on network')
        center_val = self.get_center_as_list()
        if self._args.layout == SPRING_LAYOUT:
            pos = networkx.drawing.spring_layout(netx_graph,
                                                 k=self._args.spring_k,
                                                 iterations=self._args.spring_iterations,
                                                 center=center_val,
                                                 scale=self._args.scale)
        elif self._args.layout == CIRCULAR_LAYOUT:
            pos = networkx.drawing.circular_layout(netx_graph,
                                                   scale=self._args.scale,
                                                   center=center_val)
        elif self._args.layout == KAMADA_KAWAI_LAYOUT:
            pos = networkx.drawing.kamada_kawai_layout(netx_graph,
                                                       scale=self._args.scale,
                                                       center=center_val)
        elif self._args.layout == PLANAR_LAYOUT:
            pos = networkx.drawing.planar_layout(netx_graph,
                                                 scale=self._args.scale,
                                                 center=center_val)
        elif self._args.layout == SHELL_LAYOUT:
            pos = networkx.drawing.shell_layout(netx_graph,
                                                scale=self._args.scale,
                                                center=center_val)
        elif self._args.layout == SPECTRAL_LAYOUT:
            pos = networkx.drawing.spectral_layout(netx_graph,
                                                   scale=self._args.scale,
                                                   center=center_val)
        elif self._args.layout == SPIRAL_LAYOUT:
            pos = networkx.drawing.spiral_layout(netx_graph,
                                                 scale=self._args.scale,
                                                 center=center_val)
        else:
            raise NDExUtilError(self(self._args.layout) +
                                ' does not match supported layout')

        del netx_graph

        logger.debug('Converting coordinates from networkx to CX format')
        cart_aspect = convert_networkx_pos_to_cartesian_aspect(pos)
        if self._args.outputcx is not None:
            logger.info('Writing out CX file: ' + self._args.outputcx)
            net.set_opaque_aspect('cartesianLayout', cart_aspect)
            with open(self._args.outputcx, 'w') as f:
                json.dump(net.to_cx(), f)

        return cart_aspect

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

Version {version}

The {cmd} command updates layout on a network in NDEx using Networkx.
The network can be specified by NDEx UUID via --uuid flag.


Example:

ndexmisctools.py networkxlayout spring - - - --uuid XXXX-XXX

WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
         ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=NetworkxLayoutCommand.COMMAND)

        parser = subparsers.add_parser(NetworkxLayoutCommand.COMMAND,
                                       help='Updates layout of network via '
                                            'Cytoscape',
                                       description=desc,
                                       formatter_class=Formatter)
        parser.add_argument('layout', choices=[SPRING_LAYOUT, CIRCULAR_LAYOUT,
                                               KAMADA_KAWAI_LAYOUT,
                                               PLANAR_LAYOUT,
                                               SHELL_LAYOUT,
                                               SPECTRAL_LAYOUT,
                                               SPIRAL_LAYOUT],
                            help='Name of layout to run.')
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
        parser.add_argument('--scale', type=float, default=300.0,
                            help='Scale to pass to layout algorithm.')
        parser.add_argument('--center', type=str,
                            help='Comma delimited coordinate denoting'
                                 'center for layout. Should be in format'
                                 'of X,Y or Y,X not sure which way networkx'
                                 'does coordinates')
        parser.add_argument('--' + SPRING_LAYOUT + '_iterations', type=int, default=50,
                            help='Maximum number of iterations taken ')
        parser.add_argument('--' + SPRING_LAYOUT + '_k', type=float,
                            help='Optimal distance between nodes. '
                                 'If unset the distance is set to 1/sqrt(n) '
                                 'where n is the number of nodes. Increase '
                                 'this value to move nodes farther apart. ')
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
        return parser