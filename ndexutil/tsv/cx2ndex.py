__author__ = 'dexter'

# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 22:34:42 2014

@author: dexter pratt
"""
import logging
import json


logger = logging.getLogger(__name__)

# ---------------------
# Misc utility functions
#---------------------


def blankNdexNetwork():
    return {"type": "Network",
            "namespaces": {},
            "nodes": {},
            "edges": {},
            "properties": [],
            "supports": {},
            "citations": {},
            "functionTerms": {},
            "baseTerms": {},
            "reifiedEdgeTerms": {}
    }


def blankNdexNode():
    return {"type": "Node",
            "aliases": [],
            "relatedTerms": [],
            "properties": [],
            "presentationProperties": [],
            "supportIds": []
    }


def blankNdexEdge():
    return {"type": "Edge",
            "citationIds": [],
            "presentationProperties": [],
            "properties": [],
            "supportIds": []
    }


def blankNdexBaseTerm():
    return {"type": "BaseTerm",
            "termType": "BaseTerm",
    }


def blankNdexFunctionTerm():
    return {"type": "FunctionTerm",
            "parameterIds": [],
            "termType": "FunctionTerm",
    }


def blankNdexReifiedEdgeTerm():
    return {"type": "ReifiedEdgeTerm",
            "termType": "ReifiedEdgeTerm",
    }


def blankNdexCitation():
    return {"type": "Citation",
            "contributors": [],
            "edges": [],
            "nodes": [],
            "presentationProperties": [],
            "properties": [],
    }


def blankNdexSupport():
    return {"type": "Support",
            "edges": [],
            "nodes": [],
            "presentationProperties": [],
            "properties": [],
    }


def blankNdexNamespace():
    return {"type": "Namespace",
            "presentationProperties": [],
            "properties": [],
    }


def writeAspectElements(aspectName, elements, out):
    jsonString = json.dumps({aspectName: elements})
    out.write(jsonString + "\n")


#---------------------
# CX Converter Class
#---------------------

class Cx2NdexConverter:
    def __init__(self, cx_aspect_fragment_array):
        self.functionTermBlankNodeIds = {}
        self.cx_aspect_fragments = cx_aspect_fragment_array
        self.ndex_network = blankNdexNetwork()
        self.out = None
        self.nextId = 1000
        self.prefixNamespaceIdMap = {}
        self.cx2NdexIdMap = {}
        self.termStringToIdMap = {}

    def newId(self, cx_id=None):
        id = self.nextId
        self.nextId = self.nextId + 1
        if cx_id:
            self.cx2NdexIdMap[cx_id] = id
        return id

    def getNdexId(self, cx_id, create=False):
        ndex_id = self.cx2NdexIdMap.get(cx_id)
        if not ndex_id:
            if create:
                ndex_id = self.newId(cx_id)
        return ndex_id

    def get_ndex_namespace_id_by_prefix(self, prefix, create=False):
        # do we already have a namespace corresponding to this prefix?
        ndex_namespace_id = self.prefixNamespaceIdMap.get(prefix)

        if create and not ndex_namespace_id:
            # create a namespace corresponding to the prefix
            ndex_namespace = blankNdexNamespace()
            ndex_namespace["prefix"] = prefix
            # get an id for the new namespace,  store in the map of prefix->namespace id
            ndex_namespace_id = self.newId()
            ndex_namespace["id"] = ndex_namespace_id

            self.ndex_network['namespaces'][str(ndex_namespace_id)] = ndex_namespace
            self.prefixNamespaceIdMap[prefix] = ndex_namespace_id

        return ndex_namespace_id

    def get_ndex_node_id_by_cx_id(self, cx_id, create=False):
        ndex_node_id = self.getNdexId(cx_id)
        if create and not ndex_node_id:
            ndex_node_id = self.getNdexId(cx_id, True)
            # create a node entry with no properties
            ndex_node = blankNdexNode()
            ndex_node['id'] = ndex_node_id
            self.ndex_network['nodes'][str(ndex_node_id)] = ndex_node
        return ndex_node_id

    def get_ndex_edge_id_by_cx_id(self, cx_id, create=False):
        ndex_edge_id = self.getNdexId(cx_id)
        if create and not ndex_edge_id:
            ndex_edge_id = self.getNdexId(cx_id, True)
            ndex_edge = blankNdexEdge()
            ndex_edge['id'] = ndex_edge_id
            self.ndex_network['edges'][str(ndex_edge_id)] = ndex_edge
        return ndex_edge_id

    def get_ndex_function_term_id_by_cx_id(self, cx_id, create=False):
        ndex_function_term_id = self.getNdexId(cx_id)
        if create and not ndex_function_term_id:
            ndex_function_term_id = self.getNdexId(cx_id, True)
            ndex_function_term = blankNdexFunctionTerm()
            ndex_function_term['id'] = ndex_function_term_id
            self.ndex_network['functionTerms'][str(ndex_function_term_id)] = ndex_function_term
        return ndex_function_term_id

    def get_ndex_base_term_id_for_string(self, term_string):

        ndex_base_term_id = self.termStringToIdMap.get(term_string)
        if ndex_base_term_id:
            return ndex_base_term_id

        else:
            # have not created this base term yet
            # parse term string to get prefix and identifier, split at first colon
            ndex_base_term = blankNdexBaseTerm()
            ndex_base_term_id = self.newId()
            ndex_base_term['id'] = ndex_base_term_id
            prefix, colon, identifier = term_string.partition(':')
            if colon == "":
                # no colon found, so treat the whole as the name in the base term, no namespace
                ndex_base_term['name'] = term_string

            else:
                ndex_namespace_id = self.get_ndex_namespace_id_by_prefix(prefix, True)
                ndex_base_term['namespaceId'] = ndex_namespace_id
                ndex_base_term['name'] = identifier

            # because we are creating the base term,
            # get an id for the new baseterm,
            # then store in the map where termstring->base term id

            self.termStringToIdMap[term_string] = ndex_base_term_id
            self.ndex_network['baseTerms'][str(ndex_base_term_id)] = ndex_base_term
        return ndex_base_term_id

    def get_ndex_citation_id_by_cx_id(self, cx_id, create=False):
        ndex_citation_id = self.getNdexId(cx_id)
        if create and not ndex_citation_id:
            ndex_citation_id = self.getNdexId(cx_id, True)
            ndex_citation = blankNdexCitation()
            ndex_citation['id'] = ndex_citation_id
            self.ndex_network['citations'][str(ndex_citation_id)] = ndex_citation

        return ndex_citation_id

    def get_ndex_support_id_by_cx_id(self, cx_id, create=False):
        ndex_support_id = self.getNdexId(cx_id)
        if create and not ndex_support_id:
            ndex_support_id = self.getNdexId(cx_id, True)
            ndex_support = blankNdexSupport()
            ndex_support['id'] = ndex_support_id
            self.ndex_network['supports'][str(ndex_support_id)] = ndex_support
        return ndex_support_id

    def get_ndex_reified_edge_term_id_by_ndex_edge_id(self, ndex_edge_id, create=False):
        # search the reified edge terms
        for reified_edge_term_id, term in self.ndex_network.get('reifiedEdgeTerms'):
            if term.get("edgeId") == ndex_edge_id:
                return reified_edge_term_id
        # didn't find it, so create
        id = self.newId()
        reified_edge_term = blankNdexReifiedEdgeTerm()
        reified_edge_term['id'] = id
        reified_edge_term['edgeId'] = ndex_edge_id
        self.ndex_network['reifiedEdgeTerms'][str(id)] = reified_edge_term
        return id

    def convertToNdex(self):
        for aspect_fragment in self.cx_aspect_fragments:
            self.handle_aspect_fragment(aspect_fragment)

        return self.ndex_network

    def handle_aspect_fragment(self, aspect_fragment):
        # dispatch on type of aspect_fragment
        # ignore any that are unknown
        keys = aspect_fragment.keys()
        type = keys[0]
        elements = aspect_fragment.get(type)
        for element in elements:
            if type == "@context":
                self.handle_context_aspect_fragment(element)
            elif type == "nodes":
                self.handle_nodes_aspect_fragment(element)
            elif type == "edges":
                self.handle_edges_aspect_fragment(element)
            elif type == "edgeIdentities":
                self.handle_edge_identities_aspect_fragment(element)
            elif type == "functionTerms":
                self.handle_function_terms_aspect_fragment(element)
            elif type == "nodeIdentities":
                self.handle_node_identities_aspect_fragment(element)
            elif type == "citations":
                self.handle_citations_aspect_fragment(element)
            elif type == "supports":
                self.handle_supports_aspect_fragment(element)
            elif type == "profile":
                self.handle_profile_aspect_fragment(element)
            elif type == "networkProperties":
                self.handle_network_properties_aspect_fragment(element)
            elif type == "elementProperties":
                self.handle_element_properties_aspect_fragment(element)
            elif type == "reifiedEdges":
                self.handle_reified_edges_aspect_fragment(element)
            else:
                logger.error("Unknown aspect_fragment type: " + type)

    def handle_context_aspect_fragment(self, element):
        # expecting {prefix : uri}
        # references to the namespace by prefix in previously processed aspect_fragments may already have created it.
        # but we use a method that will create it if it has not been created yet.
        prefix = element.keys()[0]
        ndex_namespace_id = self.get_ndex_namespace_id_by_prefix(prefix, True)
        ndex_namespace = self.ndex_network['namespaces'].get(str(ndex_namespace_id))

        uri = element.values()[0]
        if uri:
            ndex_namespace["uri"] = uri

    def handle_nodes_aspect_fragment(self, element):
        # expecting {"@id" : blankNodeId}
        self.get_ndex_node_id_by_cx_id(element.get('@id'), True)

    def handle_edges_aspect_fragment(self, element):
        # {"@id" : blankNodeId, "source" : blankNodeId, "target" : blankNodeId)}
        ndex_edge_id = self.get_ndex_edge_id_by_cx_id(element.get('@id'), True)
        ndex_edge = self.ndex_network['edges'].get(str(ndex_edge_id))
        cx_source_node_id = element.get('source')
        if cx_source_node_id:
            ndex_source_node_id = self.get_ndex_node_id_by_cx_id(cx_source_node_id)
            ndex_edge['subjectId'] = ndex_source_node_id

        cx_target_node_id = element.get('target')
        if cx_target_node_id:
            ndex_target_node_id = self.get_ndex_node_id_by_cx_id(cx_target_node_id)
            ndex_edge['objectId'] = ndex_target_node_id

    def handle_edge_identities_aspect_fragment(self, element):
        # {"edge" : blankNodeId, "relationship" : baseTermString}
        cx_edge_id = element.get('edge')
        predicate_string = element.get('relationship')
        if cx_edge_id and predicate_string:
            ndex_edge_id = self.get_ndex_edge_id_by_cx_id(cx_edge_id, True)
            ndex_edge = self.ndex_network['edges'].get(str(ndex_edge_id))
            ndex_base_term_id = self.get_ndex_base_term_id_for_string(predicate_string)
            ndex_edge['predicateId'] = ndex_base_term_id

    def handle_function_terms_aspect_fragment(self, element):
        # expecting {"@id" : function_term_id, "function" : cx_term_string, "parameters" : [parameters]}
        cx_function_term_id = element.get("@id")
        ndex_function_term_id = self.get_ndex_function_term_id_by_cx_id(element.get('@id'), True)
        ndex_function_term = self.ndex_network['functionTerms'].get(str(ndex_function_term_id))

        cx_function_term_string = element.get("function")
        ndex_function_id = self.get_ndex_base_term_id_for_string(cx_function_term_string)
        ndex_function_term['functionTermId'] = ndex_function_id

        cx_parameters = element.get("parameters")

        ndex_parameter_ids = []
        for cx_parameter in cx_parameters:
            # each parameter is either a cx_term_string OR a blank node id for a function term
            ndex_parameter_id, term_type = self.get_ndex_id_by_cx_id_or_term_string(cx_parameter)
            ndex_parameter_ids.append(ndex_parameter_id)

        ndex_function_term['parameterIds'] = ndex_parameter_ids


    # BUG: needs to distinguish CX blank nodes that are reified edges.
    # For those, we need to create the reified edge term and return that ndex id
    def get_ndex_id_by_cx_id_or_term_string(self, cx_parameter):
        if cx_parameter.startswith("_"):
            # its a blank node id
            return self.get_ndex_function_term_id_by_cx_id(cx_parameter, True), 'functionTerm'
        else:
            return self.get_ndex_base_term_id_for_string(cx_parameter), 'baseTerm'

    def handle_node_identities_aspect_fragment(self, element):
        # expecting {node: cx_node_id, represents: item, aliases: [items...]}
        ndex_node_id = self.get_ndex_node_id_by_cx_id(element.get("node"), True)
        ndex_node = self.ndex_network['nodes'].get(str(ndex_node_id))
        if "represents" in element:
            ndex_represents_id, term_type = self.get_ndex_id_by_cx_id_or_term_string(element['represents'])
            ndex_node["represents"] = ndex_represents_id
            ndex_node["representsTermType"] = term_type

        cx_aliases = element.get('alias')
        if cx_aliases:
            ndex_aliases = []
            for cx_alias in element.get('alias'):
                alias, term_type = self.get_ndex_id_by_cx_id_or_term_string(cx_alias)
                ndex_aliases.append(alias)
            if len(ndex_aliases) < 0:
                ndex_node['alias'] = ndex_aliases

        cx_related_terms = element.get('relatedTerms')
        if cx_related_terms:
            ndex_related_terms = []
            for cx_term in element.get('relatedTerms'):
                related_term, term_type = self.get_ndex_id_by_cx_id_or_term_string(cx_term)
                ndex_related_terms.append(related_term)
            if len(ndex_related_terms) < 0:
                ndex_node['relatedTerms'] = ndex_related_terms

        if "name" in element:
            ndex_node['name'] = element.get('name')

    def handle_reified_edges_aspect_fragment(self, element):
        ndex_node_id = self.get_ndex_node_id_by_cx_id(element.get("node"), True)
        ndex_edge_id = self.get_ndex_edge_id_by_cx_id(element.get("edge"), True)
        reified_edge_term_id = self.get_ndex_reified_edge_term_id_by_ndex_edge_id(ndex_edge_id, True)
        ndex_node = self.ndex_network['nodes'].get(str(ndex_node_id))
        ndex_node['represents'] = reified_edge_term_id
        ndex_node['representsTermType'] = 'reifiedEdgeTerm'

    def handle_citations_aspect_fragment(self, element):
        ndex_citation_id = self.get_ndex_citation_id_by_cx_id(element.get('@id'), True)
        ndex_citation = self.ndex_network['citations'].get(str(ndex_citation_id))
        for key, value in element.iteritems():
            if key == '@id':
                continue
            elif key == 'nodes':
                for cx_id in value:
                    ndex_node_id = self.get_ndex_node_id_by_cx_id(cx_id, True)
                    ndex_node = self.ndex_network['nodes'].get(str(ndex_node_id))
                    if not 'citationIds' in ndex_node:
                        ndex_node['citationIds'] = []
                    ndex_node['citationIds'].append(ndex_citation_id)

            elif key == 'edges':
                for cx_id in value:
                    ndex_edge_id = self.get_ndex_edge_id_by_cx_id(cx_id, True)
                    ndex_edge = self.ndex_network['edges'].get(str(ndex_edge_id))
                    if not 'citationIds' in ndex_edge:
                        ndex_edge['citationIds'] = []
                    ndex_edge['citationIds'].append(ndex_citation_id)

            else:
                ndex_citation[key] = value

    def handle_supports_aspect_fragment(self, element):
        ndex_support_id = self.get_ndex_support_id_by_cx_id(element.get('@id'), True)
        ndex_support = self.ndex_network['supports'].get(str(ndex_support_id))
        for key, value in element.iteritems():
            if key == '@id':
                continue
            elif key == 'nodes':
                for cx_id in value:
                    ndex_node_id = self.get_ndex_node_id_by_cx_id(cx_id, True)
                    ndex_node = self.ndex_network['nodes'].get(str(ndex_node_id))
                    if not 'supportIds' in ndex_node:
                        ndex_node['supportIds'] = []
                    ndex_node['supportIds'].append(ndex_support_id)

            elif key == 'edges':
                for cx_id in value:
                    ndex_edge_id = self.get_ndex_edge_id_by_cx_id(cx_id, True)
                    ndex_edge = self.ndex_network['edges'].get(str(ndex_edge_id))
                    ndex_edge_supports = ndex_edge.get('supports')
                    if not 'supportIds' in ndex_edge:
                        ndex_edge['supportIds'] = []
                    ndex_edge['supportIds'].append(ndex_support_id)
            elif key == 'citation':
                ndex_support[key] = self.get_ndex_citation_id_by_cx_id(value, True)
            else:
                ndex_support[key] = value

    def handle_profile_aspect_fragment(self, element):
        for key, value in element.iteritems():
            if key == "dc:title":
                self.ndex_network['name'] = value
            if key == "dc:description":
                self.ndex_network['description'] = value

    def handle_network_properties_aspect_fragment(self, element):
        self.ndex_network['properties'].append(element)

    def handle_element_properties_aspect_fragment(self, element):
        predicateString = element.get('property')
        value = element.get('value')
        predicateId = self.get_ndex_base_term_id_for_string(predicateString)
        ndex_property = {"predicateString": predicateString,
                         "predicateId" : predicateId,
                         "value": value,
                         "type" : "NdexPropertyValuePair"}
        if "edge" in element:
            ndex_edge_id = self.get_ndex_edge_id_by_cx_id(element.get('edge'), True)
            ndex_edge = self.ndex_network['edges'].get(str(ndex_edge_id))
            if "properties" in ndex_edge:
                ndex_edge['properties'].append(ndex_property)
            else:
                ndex_edge['properties'] = [ndex_property]
        elif "node" in element:
            ndex_node_id = self.get_ndex_node_id_by_cx_id(element.get('node'), True)
            ndex_node = self.ndex_network['nodes'].get(str(ndex_node_id))
            if "properties" in ndex_node:
                ndex_node['properties'].append(ndex_property)
            else:
                ndex_node['properties'] = [ndex_property]    



