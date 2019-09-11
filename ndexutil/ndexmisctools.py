#! /usr/bin/env python

import sys
import argparse
import logging
import json
from requests.exceptions import HTTPError
import ndexutil
from ndexutil.config import NDExUtilConfig
from ndexutil.exceptions import NDExUtilError
from ndex2.exceptions import NDExError
from ndex2.client import Ndex2
import ndex2

# create logger
logger = logging.getLogger('ndexutil.ndexmisctools')


LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"


class CopyNetwork(object):
    """
    Copies NDEx network from one account to another
    account
    """
    COMMAND = 'copynetwork'

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._srcuser = None
        self._srcpass = None
        self._srcserver = None
        self._destuser = None
        self._destpass = None
        self._destserver = None

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()
        self._srcuser = con.get(self._args.profile,
                                'source_' + NDExUtilConfig.USER)
        self._srcpass = con.get(self._args.profile,
                                'source_' + NDExUtilConfig.PASSWORD)
        self._srcserver = con.get(self._args.profile,
                                  'source_' + NDExUtilConfig.SERVER)
        self._destuser = con.get(self._args.profile,
                                 'dest_' + NDExUtilConfig.USER)
        self._destpass = con.get(self._args.profile,
                                 'dest_' + NDExUtilConfig.PASSWORD)
        self._destserver = con.get(self._args.profile,
                                   'dest_' + NDExUtilConfig.SERVER)

    def run(self):
        """
        Downloads network from source and copies to destination
        :return:
        """
        self._parse_config()
        net = ndex2.create_nice_cx_from_server(self._srcserver,
                                               self._srcuser,
                                               self._srcpass,
                                               self._args.uuid)
        net.upload_to(self._destserver, self._destuser,
                      self._destpass)

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

            Version {version}

            The copynetwork command copies an NDEx network specified by --uuid 
            to another user account. 
            
            The source and destination accounts are specified by configuration
            in --conf under section set via --profile field
            
            Expected format in configuration file:
            [<value of --profile>]
            source_user = <user>
            source_pass = <password>
            source_server = <server>
            dest_user = = <user>
            dest_pass = <password>
            dest_server = <server>
            
            WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
                     ERRORS. YOU HAVE BEEN WARNED.

            """.format(version=ndexutil.__version__)
        help_formatter = argparse.RawDescriptionHelpFormatter

        parser = subparsers.add_parser(CopyNetwork.COMMAND,
                                       help='Copies network '
                                            'from one user to another',
                                       description=desc,
                                       formatter_class=help_formatter)

        parser.add_argument('--uuid',
                            help='The UUID of network in NDEx to update')
        return parser


class NetworkAttributeSetter(object):
    """
    Sets network attributes on a network in NDEx
    """
    COMMAND = 'networkattribupdate'

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._user = None
        self._pass = None
        self._server = None

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()
        self._user = con.get(self._args.profile, NDExUtilConfig.USER)
        self._pass = con.get(self._args.profile, NDExUtilConfig.PASSWORD)
        self._server = con.get(self._args.profile, NDExUtilConfig.SERVER)

    def _get_client(self):
        """
        Gets Ndex2 client
        :return: Ndex2 python client
        :rtype: :py:class:`~ndex2.client.Ndex2`
        """
        return Ndex2(self._server, self._user, self._pass)

    def _remove_existing_attribute(self, net_attribs):
        """
        Removes from net_attribs any dicts whose value of 'n'
        matches self._args.name
        :param net_attribs: network attributes
        :type net_attribs: list of dicts
        :return: None
        """
        items_to_delete = []
        for theindex, entry in enumerate(net_attribs):
            if entry['n'] == self._args.name:
                items_to_delete.append(theindex)

        items_to_delete.sort(reverse=True)
        for theindex in items_to_delete:
            del net_attribs[theindex]

    def _remove_name_description_summary(self, net_attribs):
        """
        Removes from net_attribs any dicts whose value of 'n'
        matches self._args.name
        :param net_attribs: network attributes
        :type net_attribs: list of dicts
        :return: None
        """
        excludelist = ['name', 'description', 'version']
        items_to_delete = []
        for theindex, entry in enumerate(net_attribs):
            if entry['n'] in excludelist:
                items_to_delete.append(theindex)
        items_to_delete.sort(reverse=True)
        for theindex in items_to_delete:
            del net_attribs[theindex]

    def _convert_attributes_to_ndexpropertyvaluepair(self, net_attribs):
        """
        The NDEx REST endpoint used in this class
        http://openapi.ndextools.org/#/Network/put_network__networkid__properties
        actually follows a legacy implementation that differs from CX format.

        This function converts the list of dicts into structure that will
        work with the REST service endpoint
        :return: updated list
        :rtype list of dicts
        """
        new_attribs = []
        for entry in net_attribs:
            newentry = {'predicateString': entry['n']}
            if 'd' in entry:
                newentry['dataType'] = entry['d']
                if entry['d'].startswith('list'):
                    newentry['value'] = json.dumps(entry['v'])
                else:
                    newentry['value'] = entry['v']
            else:
                newentry['value'] = entry['v']
            new_attribs.append(newentry)
        return new_attribs

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
        if self._args.name in ['name', 'description', 'version']:
            raise NDExUtilError('Sorry, but name, description, and version'
                                'CANNOT be updated by this call.')
        self._parse_config()

        client = self._get_client()
        res = client.get_network_aspect_as_cx_stream(self._args.uuid,
                                                     'networkAttributes')
        if res.status_code != 200:
            raise NDExUtilError('Received error status when querying'
                                'NDEx: ' + str(res.status_code) +
                                ' : ' + str(res.text))

        net_attribs = json.loads(res.text)

        # remove name description summary
        self._remove_name_description_summary(net_attribs)

        # remove existing attribute if found
        self._remove_existing_attribute(net_attribs)

        new_attribs = self._convert_attributes_to_ndexpropertyvaluepair(net_attribs)

        if self._args.value is not None:
            new_entry = {'predicateString': self._args.name}
            if self._args.type != 'string':
                new_entry['dataType'] = self._args.type
            new_entry['value'] = self._args.value
            new_attribs.append(new_entry)

        logger.debug(str(new_attribs))
        res = client.set_network_properties(self._args.uuid, new_attribs)
        return res

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """
        
        Version {version}
        
        The {cmd} command updates network attributes on a network
        specified by --uuid with values set in --name, --type, and --value
        
        NOTE: Currently only 1 attribute can be updated at a time. Invoke
              multiple times to update several attributes at once.
        
        BIGPROBLEM: Due to issues on server (we would need to make different call)
                    the network attributes name, version, and description CANNOT
                    be updated by this call and will currently return an error

        WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
                 ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=NetworkAttributeSetter.COMMAND)
        help_formatter = argparse.RawDescriptionHelpFormatter

        parser = subparsers.add_parser(NetworkAttributeSetter.COMMAND,
                                       help='Updates network attributes',
                                       description=desc,
                                       formatter_class=help_formatter)

        parser.add_argument('--uuid',
                            help='The UUID of network in NDEx to update')
        parser.add_argument('--name',
                            help='Name of attribute')
        parser.add_argument('--type',
                            help='Type of attribute (default string),'
                                 'can be one of following'
                                 'https://ndex2.readthedocs.io/en/'
                                 'latest/ndex2.html?highlight='
                                 'list_of_string#supported-'
                                 'data-types',
                            default='string')
        parser.add_argument('--value',
                            help='Value of attribute, if unset then '
                                 'attribute is removed. NOTE: '
                                 'If --type is list.. then quote and escape '
                                 'list like so: '
                                 '"[\\"pathway\\",\\"interactome\\"]"')
        return parser


class StyleUpdator(object):
    """
    Updates style on a network in NDEx
    """
    COMMAND = 'styleupdate'

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._user = None
        self._pass = None
        self._server = None

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()
        self._user = con.get(self._args.profile, NDExUtilConfig.USER)
        self._pass = con.get(self._args.profile, NDExUtilConfig.PASSWORD)
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
        Connects to NDEx server, downloads network(s) specified by --uuid
        or by --networkset and applies style specified by --style flag
        updating those networks in place on the server.
        WARNING: This is very inefficient method since the full network
                 is downloaded and uploaded. YOU HAVE BEEN WARNED.

        :raises NDExUtilError if there is an error
        :return: number of networks updated
        """
        logger.warning('THIS IS AN UNTESTED ALPHA IMPLEMENTATION '
                       'AND MAY CONTAIN ERRORS')

        self._parse_config()
        raise NDExUtilError('Does not work yet!!!!')

        client = self._get_client()
        return 1

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

        Version {version}

        The {cmd} command updates network attributes on a network
        specified by --uuid with values set in --name, --type, and --value

        NOTE: Currently only 1 attribute can be updated at a time. Invoke
              multiple times to update several attributes at once.

        BIGPROBLEM: Due to issues on server (we would need to make different call)
                    the network attributes name, version, and description CANNOT
                    be updated by this call and will currently return an error

        WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
                 ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=NetworkAttributeSetter.COMMAND)
        help_formatter = argparse.RawDescriptionHelpFormatter

        parser = subparsers.add_parser(NetworkAttributeSetter.COMMAND,
                                       help='Updates network attributes',
                                       description=desc,
                                       formatter_class=help_formatter)

        parser.add_argument('--uuid',
                            help='The UUID of network in NDEx to update')
        parser.add_argument('--name',
                            help='Name of attribute')
        parser.add_argument('--type',
                            help='Type of attribute (default string),'
                                 'can be one of following'
                                 'https://ndex2.readthedocs.io/en/'
                                 'latest/ndex2.html?highlight='
                                 'list_of_string#supported-'
                                 'data-types',
                            default='string')
        parser.add_argument('--value',
                            help='Value of attribute, if unset then '
                                 'attribute is removed. NOTE: '
                                 'If --type is list.. then quote and escape '
                                 'list like so: '
                                 '"[\\"pathway\\",\\"interactome\\"]"')
        return parser


class UpdateNetworkSystemProperties(object):
    """
    Updates system properties on network in NDEx
    """
    COMMAND = 'systemproperty'

    def __init__(self, theargs):
        """
        Constructor
        :param theargs: command line arguments ie theargs.name theargs.type
        """
        self._args = theargs
        self._user = None
        self._pass = None
        self._server = None

    def _parse_config(self):
        """
        Parses config extracting the following fields:
        :py:const:`~ndexutil.config.NDExUtilConfig.USER`
        :py:const:`~ndexutil.config.NDExUtilConfig.PASSWORD`
        :py:const:`~ndexutil.config.NDExUtilConfig.SERVER`
        :return: None
        """
        ncon = NDExUtilConfig(conf_file=self._args.conf)
        con = ncon.get_config()
        self._user = con.get(self._args.profile, NDExUtilConfig.USER)
        self._pass = con.get(self._args.profile, NDExUtilConfig.PASSWORD)
        self._server = con.get(self._args.profile, NDExUtilConfig.SERVER)

    def _get_client(self):
        """
        Gets Ndex2 client
        :return: Ndex2 python client
        :rtype: :py:class:`~ndex2.client.Ndex2`
        """
        return Ndex2(self._server, self._user, self._pass)

    def _get_uuid_list_from_args(self, client):
        """
        Looks at command line args in self._args and
        if self._args.uuid is set grabs that otherwise
        looks at self._args.networksetid and queries for all
        networks in that networkset
        :return: list of network UUIDs as strings
        :rtype: list
        """
        # if uuid is set then just return that in a list
        try:
            if isinstance(self._args.uuid, str):
                return [self._args.uuid]
        except AttributeError:
            pass

        # if networksetid is set then query
        # ndex for all uuids and return them in a list
        try:
            res = client.get_networkset(self._args.networksetid)
            logger.debug('networks: ' + str(res['networks']))
            return res['networks']
        except HTTPError:
            logger.exception('Caught exception querying for networks in networkset')
            return None

    def run(self):
        """
        Connects to NDEx server, downloads network(s) specified by --uuid
        or by --networkset and applies style specified by --style flag
        updating those networks in place on the server.
        WARNING: This is very inefficient method since the full network
                 is downloaded and uploaded. YOU HAVE BEEN WARNED.

        :raises NDExUtilError if there is an error
        :return: number of networks updated
        """
        logger.warning('THIS IS AN UNTESTED ALPHA IMPLEMENTATION '
                       'AND MAY CONTAIN ERRORS')

        self._parse_config()

        client = self._get_client()
        uuidlist = self._get_uuid_list_from_args(client)
        if uuidlist is None:
            return 1
        prop_dict = {}
        try:
            if self._args.showcase is True:
                prop_dict['showcase'] = True
        except AttributeError:
            pass

        try:
            if self._args.disableshowcase is True:
                prop_dict['showcase'] = False
        except AttributeError:
            pass

        try:
            if self._args.indexlevel is not None:
                prop_dict['index_level'] = self._args.indexlevel.upper()
        except AttributeError:
            pass

        try:
            if self._args.visibility is not None:
                prop_dict['visibility'] = self._args.visibility.upper()
        except AttributeError:
            pass
        error_count = 0
        for netid in uuidlist:
            try:
                logger.debug('Updating network: ' + str(netid) +
                             ' sysprops:  ' + str(prop_dict))
                res = client.set_network_system_properties(netid, prop_dict)
                if res != '':
                    error_count += 1
            except NDExError:
                logger.exception('Caught NDExError trying to set network props')
                error_count += 1
            except HTTPError:
                logger.exception('Caught HTTPError trying to set network props')
                error_count += 1
        if error_count > 0:
            return 1
        return 0

    @staticmethod
    def add_subparser(subparsers):
        """
        adds a subparser
        :param subparsers:
        :return:
        """
        desc = """

        Version {version}

        The {cmd} command updates system properties on a network 
        specified by --uuid, or all networks under a given 
        networkset via --networksetid 

        Currently this command supports updating the following
        attributes: showcase, visibility, and indexing.
        
        If no flags are set for a given attribute then that value is NOT
        modified
        
        WARNING: THIS IS AN UNTESTED ALPHA IMPLEMENTATION AND MAY CONTAIN
                 ERRORS. YOU HAVE BEEN WARNED.

        """.format(version=ndexutil.__version__,
                   cmd=NetworkAttributeSetter.COMMAND)
        help_formatter = argparse.RawDescriptionHelpFormatter

        parser = subparsers.add_parser(UpdateNetworkSystemProperties.COMMAND,
                                       help='Updates system properties on '
                                            'network in NDEx',
                                       description=desc,
                                       formatter_class=help_formatter)

        id_grp = parser.add_mutually_exclusive_group()

        id_grp.add_argument('--uuid',
                            help='The UUID of network in NDEx to update')
        id_grp.add_argument('--networksetid',
                            help='The UUID of networkset which will '
                                 'update all networks within set')
        showcase_grp = parser.add_mutually_exclusive_group()
        showcase_grp.add_argument('--showcase', action='store_true',
                                  help='If set, network will be showcased')
        showcase_grp.add_argument('--disableshowcase', action='store_true',
                                  help='If set, network will NOT be showcased')
        parser.add_argument('--indexlevel',
                            choices=['none', 'meta', 'all'],
                            help='If set, network indexing will be updated')
        parser.add_argument('--visibility',
                            choices=['public', 'private'],
                            help='If set, updates visibility of network')
        return parser


def _parse_arguments(desc, args):
    """Parses command line arguments using argparse.
    """

    help_formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_formatter)

    subparsers = parser.add_subparsers(dest='command', required=True,
                                       help='Command to run. '
                                            'Type <command> -h for '
                                            'more help')

    NetworkAttributeSetter.add_subparser(subparsers)
    CopyNetwork.add_subparser(subparsers)
    UpdateNetworkSystemProperties.add_subparser(subparsers)

    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module and '
                             '. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default is to '
                             'log CRITICAL)')
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'format consumable by fileConfig. See '
                             'https://docs.python.org/3/library/logging.html '
                             'for more information. '
                             'Setting this overrides -v|--verbose parameter '
                             'which uses default logger. (default None)')
    parser.add_argument('--conf', help='Configuration file to load '
                                       '(default ~/' +
                                       NDExUtilConfig.CONFIG_FILE)
    parser.add_argument('--profile', help='Profile in configuration '
                                          'file to use to load '
                                          'NDEx credentials which means'
                                          'configuration under [XXX] will be'
                                          'used '
                                          '(default '
                                          'ndexmisctools)',
                        default='ndexmisctools')
    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' + ndexutil.__version__))

    return parser.parse_args(args)


def _setup_logging(args):
    """
    Sets up logging based on parsed command line arguments.
    If args.logconf is set use that configuration otherwise look
    at args.verbose and set logging for this module and the one
    in ndexutil specified by TSV2NICECXMODULE constant
    :param args: parsed command line arguments from argparse
    :raises AttributeError: If args is None or args.logconf is None
    :return: None
    """

    if args.logconf is None:
        level = (50 - (10 * args.verbose))
        logging.basicConfig(format=LOG_FORMAT,
                            level=level)
        logger.setLevel(level)
        return

    # logconf was set use that file
    logging.config.fileConfig(args.logconf,
                              disable_existing_loggers=False)


def main(arglist):
    desc = """
              Version {version}
              """.format(version=ndexutil.__version__)

    theargs = _parse_arguments(desc, arglist[1:])
    theargs.program = arglist[0]
    theargs.version = ndexutil.__version__
    _setup_logging(theargs)
    try:
        logger.debug('Command is: ' + str(theargs.command))
        if theargs.command == NetworkAttributeSetter.COMMAND:
            cmd = NetworkAttributeSetter(theargs)
        if theargs.command == CopyNetwork.COMMAND:
            cmd = CopyNetwork(theargs)
        if theargs.command == UpdateNetworkSystemProperties.COMMAND:
            cmd = UpdateNetworkSystemProperties(theargs)

        if cmd is None:
            raise NDExUtilError('Invalid command: ' + str(theargs.command))

        return cmd.run()
    finally:
        logging.shutdown()
    return 100


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
