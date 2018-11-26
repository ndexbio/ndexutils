from ndex2.niceCXNetwork import NiceCXNetwork
from ndex2.cx.aspects.NodeElement import NodeElement
from ndex2.cx.aspects.EdgeElement import EdgeElement
from ndex2.metadata.MetaDataElement import MetaDataElement
from ndex2.cx.aspects.NameSpace import NameSpace
from ndex2.cx.aspects.NodeAttributesElement import NodeAttributesElement
from ndex2.cx.aspects.EdgeAttributesElement import EdgeAttributesElement


class NiceCXNetworkBuilder:
    def __init__(self):
        self._niceCX = NiceCXNetwork()
        self._nodeCounter = 0
        self._edgeCounter = 0
        self._ext_id_map = {}
        self.edgeAttr_cnt = 0
        self.nodeAttr_cnt = 0

    def create_or_get_node_by_name(self, ext_id, name, represents=None, attributes=None):
        """
            Add node object to the network using ext_id as the key and return the id of the newly created node. If node
             with the given ext_id already exists, return the id of the node and no new node will be created.

            :param ext_id: external id of the node. It is a id that can be used to uniquely identify a node thoughout
            CX network builder process.
            :type ext_id: basestring
            :param name: A node name
            :type name: string
            :param represents: represents of a node
            :type represents: string
            :return: Node ID
            :rtype: int
        """
        node_id = self._ext_id_map.get(ext_id)
        if node_id is not None:
            node = self._niceCX.get_node_by_id(node_id)
            if name:
                if node.get_name() != name:
                    raise RuntimeError("Node name mismatches between '" + name + "' and '" + node.get_name() +
                                       "' in node '" + ext_id + "'")

            if represents:
                if node.get_node_represents() != represents:
                    raise RuntimeError(
                        "Node represents mismatches between '" + represents + "' and '" + node.get_node_represents() +
                        "' in node '" + ext_id + "'")
            if attributes:
                node_attributes = self._niceCX.get_node_attributes_by_id(node_id)
                for attr in node_attributes:
                    attr_name = attr.get_name()
                    attr_value = attr.get_values()
                    attr2 = attributes.get(attr_name)
                    if attr_value != attr2.get_values():
                        raise RuntimeError("Node attribute " + attr_name + " mismatches between '" +
                                           attr2 + "' and '" + attributes.get(attr_name) + "' for node " + str(node_id))
            return node_id
        else:
            node_id = self._nodeCounter
            self._nodeCounter += 1
            self._ext_id_map[ext_id] = node_id
            self._niceCX.add_node_element(NodeElement(node_id, name, represents))
            for attr in attributes:
                self._niceCX.add_node_attribute(attr)
            self.nodeAttr_cnt += len(attributes)

    def addEdge(self, src_id, tgt_id, interaction=None, attributes=None):
        edge_id = self.edgeCounter
        self._niceCX.add_edge_element(EdgeElement(edge_id,src_id,tgt_id,interaction))
        self.edgeIdCounter +=1
        if attributes is not None:
            for attr in attributes:
                self._niceCX.add_edge_attribute(attr)
            self.edgeAttr_cnt += len(attributes)
        return id


    def set_context(self, context):
        self._niceCX.set_context(context)


    def compute_metadata(self):
        if self._niceCX.get_context() != None:
            self._niceCX.add_metadata(MetaDataElement(NameSpace.getAspectName(),1))
        node_cnt = len(self._niceCX.get_node_table())
        self._niceCX.add_metadata(MetaDataElement(NodeElement.get_aspect_name(), node_cnt, self._nodeCounter))
        edge_cnt = len(self._niceCX.get_edge_table())
        self._niceCX.add_metadata(MetaDataElement(EdgeElement.get_aspect_name(),edge_cnt,self._edgeCounter))
        self._niceCX.add_metadata(MetaDataElement(EdgeAttributesElement.get_aspect_name(),self.edgeAttr_cnt))
        self._niceCX.add_metadata(MetaDataElement(NodeAttributesElement.get_aspect_name(),self.nodeAttr_cnt))

