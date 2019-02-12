#!/usr/bin/env python

import argparse
import sys
import logging
import ndexutil
from ndexutil.loaders import ncipid
from ndexutil.exceptions import NDExUtilError

logger = logging.getLogger(__name__)


def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    # add subparsers
    ncipid.get_argument_parser(subparsers)
    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' + ndexutil.__version__))

    return parser.parse_args(args)


def main(args):
    """
    Main entry point for program
    :param args:
    :return:
    """
    desc = """
    Version {version}
    
    Contains various tools to interact with NDEx (http://ndexbio.org).
    The tools are defined in the first argument passed to this program
    and are labeled as 'positional arguments' in this help documentation below. 
    
    For more information about a specific command run the following:
    
    ndexutils.py <COMMAND> -h     
    """.format(version=ndexutil.__version__)
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = ndexutil.__version__

    try:
        loglevel = logging.DEBUG
        LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
                     "%(filename)s::%(funcName)s():%(lineno)d %(message)s"
        logging.basicConfig(level=loglevel, format=LOG_FORMAT)
        logging.getLogger('ndexutil.tsv.tsv2nicecx2').setLevel(level=loglevel)
        logging.getLogger('ndexutil.loaders.ncipid').setLevel(level=loglevel)
        logger.setLevel(loglevel)
        if theargs.command == 'loadncipid':
            cmd = ncipid.NciPidContentLoader(theargs)
        else:
            raise NDExUtilError('Unable to load command: ' + theargs.command)
        return cmd.run()
    except Exception as e:
        logger.exception('Caught exception')
    finally:
        logging.shutdown()
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))