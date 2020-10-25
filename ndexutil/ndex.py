
import logging
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
