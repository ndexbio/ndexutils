
import os
import json
import logging
import ijson
import ndex2
from ndex2.nice_cx_network import NiceCXNetwork
from ndexutil.exceptions import NDExUtilError

logger = logging.getLogger('ndexutil.ndex')


class NDExExtraUtils(object):
    """
    Contains some extra utilities for use
    with NDEx
    """

    ORIG_NODE_ID_ATTR = 'NDExExtraUtils::original_nodeid'
    """
    Name of column to hold the original node ids in Cytoscape
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def get_node_id_mapping_from_node_attribute(self, cxfile=None,
                                                nodeid_attr_name=ORIG_NODE_ID_ATTR):
        """

        :param cxfile:
        :param nodeid_attr_name:
        :return:
        """
        if cxfile is None:
            raise NDExUtilError('cxfile is None')
        if not os.path.isfile(cxfile):
            raise NDExUtilError(cxfile + ' file not found')

        net = ndex2.create_nice_cx_from_file(cxfile)
        node_mapping_dict = {}
        for node_id, node_obj in net.get_nodes():
            n_attr = net.get_node_attribute(node_id,
                                            attribute_name=nodeid_attr_name)
            if n_attr is None:
                continue
            node_mapping_dict[node_id] = n_attr['v']
        return node_mapping_dict

    def add_node_id_as_node_attribute(self, cxfile=None,
                                      outcxfile=None,
                                      nodeid_attr_name=ORIG_NODE_ID_ATTR):
        """
        Loads 'cxfile' adding a new node attribute named value
        of 'nodeid_attr_name' with a value set to id of node.
        The result is then saved to 'outcxfile'

        :param cxfile:
        :return: None
        """
        net = ndex2.create_nice_cx_from_file(cxfile)

        for node_id, node_obj in net.get_nodes():
            net.add_node_attribute(property_of=node_id, name=nodeid_attr_name,
                                   values=node_id,
                                   type='long')

        with open(outcxfile, 'w') as f:
            json.dump(net.to_cx(), f)

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
        :type client: :py:class:`~ndex2.client.Ndex2`
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

    def extract_layout_aspect_from_cx(self, input_cx_file=None):
        """
        Given a CX file, this method find the, cartesianLayout,
        if any, and writes it to a file in the temp directory.

        :param input_cx_file: path to CX file
        :type input_cx_file: str
        :return: cartesianLayout aspect or None if that aspect is NOT found
        :rtype: list
        """
        node_mapping = self.get_node_id_mapping_from_node_attribute(cxfile=input_cx_file)
        with open(input_cx_file, 'rb') as f:
            for object in ijson.items(f, 'item.cartesianLayout'):
                # an inefficient fix to ijson setting the node
                # coordinates to type Decimal which breaks json.dump
                for node in object:
                    # need to remap node ids
                    node['node'] = node_mapping[node['node']]
                    if 'x' in node:
                        node['x'] = float(node['x'])
                    if 'y' in node:
                        node['y'] = float(node['y'])
                    if 'z' in node:
                        node['z'] = float(node['z'])
                return object
