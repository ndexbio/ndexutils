
import os
import json
import logging

from ndex2.nice_cx_network import NiceCXNetwork
from ndexutil.exceptions import NDExUtilError

logger = logging.getLogger('ndexutil.ndex')


class NDExExtraUtils(object):
    """
    Contains some extra utilities for use
    with NDEx
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def update_network_on_ndex(self, client=None,
                               networkid=None,
                               cxfile=None):
        """
        Updates complete network on NDEx

        :param client: NDEx server client connection
        :type client: :py:class:`~ndex2.client.Ndex2`
        :param cxfile: Path to file containing network in CX
                       format to update on NDEx
        :type cxfile: str
        :return: any response from update call
        """
        if client is None:
            raise NDExUtilError('NDEx client is None')
        if networkid is None:
            raise NDExUtilError('Network UUID is None')
        if cxfile is None:
            raise NDExUtilError('cxfile is None')

        if not os.path.isfile(cxfile):
            raise NDExUtilError(str(cxfile) + ' is not a file')

        logger.debug('Updating entire network with id: ' +
                     str(networkid))
        with open(cxfile, 'rb') as f:
            res = client.update_cx_network(f, networkid)
            return res

    def update_network_aspect_on_ndex(self, client=None,
                                      networkid=None,
                                      aspect_name=None,
                                      aspect_data=None):
        """
        Updates just the aspect via PUT call on NDEx

        :param client: NDEx server client connection
        :type client: :py:class:`~ndex2.client.Ndex2`
        :return: anything returned from put call
        """
        if client is None:
            raise NDExUtilError('NDEx client is None')
        if networkid is None:
            raise NDExUtilError('Network UUID is None')
        if aspect_name is None:
            raise NDExUtilError('Aspect name is None')
        if aspect_data is None:
            raise NDExUtilError('Aspect data is None')
        logger.debug('Updating ' + str(aspect_name) +
                     ' aspect on NDEx for network with uuid: ' +
                     networkid)
        net = NiceCXNetwork()
        net.set_opaque_aspect('cartesianLayout', aspect_data)

        theurl = '/network/' + networkid + '/aspects'
        res = client.put(theurl,
                         put_json=json.dumps(net.to_cx()))
        return res

    def download_network_from_ndex(self, client=None,
                                   networkid=None,
                                   destfile=None):
        """
        Downloads network from ndex by directly streaming CX
        data to file specified by `destfile` parameter. This is
        the most memory efficient way to retrieve CX from NDEx

        :param client: NDEx 2 client
        :type client: `:py:class:~ndex2.client.Ndex2`
        :param networkid: UUID of network as
        :type networkid: str
        :param destfile: destination file for network
        :type destfile: str
        :raises NDExUtilError: if any parameter is `None` or invalid
        :raises Exception: Could be any of a number of errors raised
                           during writing of network to destfile or by
                           client
        :return: Path to destination file that was passed in via `destfile`
        :rtype: str
        """
        if client is None:
            raise NDExUtilError('NDEx client is None')
        if networkid is None:
            raise NDExUtilError('Network UUID is None')
        if destfile is None:
            raise NDExUtilError('Destfile is None')

        logger.info('Downloading ' + destfile + ' with netid: ' + networkid)
        client_resp = client.get_network_as_cx_stream(networkid)
        with open(destfile, 'wb') as f:
            for chunk in client_resp.iter_content(chunk_size=8096):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return destfile
