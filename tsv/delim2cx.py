__author__ = 'dexter'


import csv
import io
import json
import ntpath

# convert a delimited file of CX based on a JSON 'plan' specifying mapping of
# column values to edges, source nodes, and target nodes

def convert_tsv_to_cx_annotated_nodes(filename, identifier_column, default_namespace=None):
    cx_out = []
    identifierToNodeIdMap = {}
    id_counter = 1000
    with open(filename) as tsvfile:
        reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab')
        for row in reader:
            print row
            identifier = row.get(identifier_column)

            if identifier:
                cx_identifier = identifier
                if default_namespace:
                    cx_identifier = default_namespace + ":" + identifier

                # if there is no entry in the identifier column, then skip
                # if we have a duplicate identifer, we skip it
                node_id = identifierToNodeIdMap.get(cx_identifier)
                if not node_id:
                    node_id = "_:" + str(id_counter)
                    id_counter = id_counter + 1
                    print "making node " + node_id + " for cx_identifier " + cx_identifier
                    identifierToNodeIdMap[cx_identifier] = node_id
                    cx_out.append({"nodes": [{"@id": node_id}]})
                    cx_out.append({"nodeIdentities": [{"node": node_id, "represents": identifier}]})


                # for each key in the row (except the identifier),
                # we add a node property aspic
                for key, value in row.iteritems():

                    if not key == identifier:
                        val = str(value).strip()
                        if val is not "":
                            cx_out.append({"elementProperties": [{"node": node_id,
                                                                  "property": key,
                                                                  "value": val}]})
    return cx_out


default_specs = {
    "source_id_column": "source",
    "source_columns": [],
    "predicate_id_column": "predicate",
    "target_id_column": "target",
    "target_columns": [],
    "edge_id_column": "edge",
    "edge_columns": [],
    "edge_citation_column": "citation",
    "source_context": None,
    "target_context": None,
    "predicate_context": None,
    "default_context": {"uri": "http://www.example.com/",
                        "prefix": "example"},
}


class TSV2CXConverter:
    def __init__(self, plan):

        self.plan = plan
        self.default_context = plan.get('default_context')
        self.source_plan = plan.get('source_plan')
        self.source_use_names_as_identifiers = False
        self.target_use_names_as_identifiers = False

        self.node_count = 0
        self.edge_count = 0
        self.citation_count = 0

        self.context_map = {}

        if self.source_plan:

            self.source_context = self.source_plan.get('context')
            if not self.source_context:
                self.source_context = self.default_context
            self.source_id_column = self.source_plan.get('id_column')
            self.source_node_name_column = self.source_plan.get('node_name_column')
            if not self.source_id_column and not self.source_node_name_column:
                raise Exception("Invalid Plan: no source id or source name column")
            if not self.source_id_column:
                self.source_use_names_as_identifiers = True
            self.source_columns = self.source_plan.get('property_columns')

        self.target_plan = plan.get('target_plan')
        if self.target_plan:

            self.target_context = self.target_plan.get('context')
            if not self.target_context:
                self.target_context = self.default_context
            self.target_id_column = self.target_plan.get('id_column')
            self.target_node_name_column = self.target_plan.get('node_name_column')
            if not self.target_id_column and not self.target_node_name_column:
                raise Exception("Invalid Plan: no target id or target name column")
            if not self.target_id_column:
                self.target_use_names_as_identifiers = True
            self.target_columns = self.target_plan.get('property_columns')

        self.edge_plan = plan.get('edge_plan')
        if self.edge_plan:
            self.edge_id_column = self.edge_plan.get('id_column')
            self.edge_columns = self.edge_plan.get('property_columns')
            self.predicate_id_column = self.edge_plan.get('predicate_id_column')
            self.default_predicate = self.edge_plan.get('default_predicate')
            self.predicate_context = self.edge_plan.get('context')
            if not self.predicate_context:
                self.predicate_context = self.default_context

        self.cx_identifier_to_citation_map = {}

        self.identifier_to_cx_id_map = {
            "nodes": {},
            "edges": {},
            "citations": {}
        }
        self.id_counter = 1000
        self.cx_out = []

    def get_cx_id_for_identifier(self, aspect, identifier, create=True):
        aspect_map = self.identifier_to_cx_id_map.get(aspect)
        cx_id = aspect_map.get(identifier)
        if cx_id:
            return cx_id
        if create:
            cx_id = self.get_next_cx_id()
            aspect_map[identifier] = cx_id
            return cx_id
        return False

    def get_next_cx_id(self):
        self.id_counter += 1
        return self.id_counter

    def convert_tsv_to_cx_stream(self, filename, max_rows = None):
        cx = self.convert_tsv_to_cx(filename, max_rows)
        return self.convert_cx_to_stream(cx)

    def convert_cx_to_stream(self, cx):
        stream = io.BytesIO(json.dumps(cx))
        return stream

    def check_header_vs_plan(self, header):
        # each column name referenced in the plan must be in the header, otherwise raise an exception
        if self.source_plan:
            self.check_column(self.source_plan.get('id_column'), header)
            self.check_column(self.source_plan.get('node_name_column'), header)
            for column_name in self.source_plan.get('property_columns'):
                self.check_column(column_name, header)

        if self.target_plan:
            self.check_column(self.target_plan.get('id_column'), header)
            self.check_column(self.target_plan.get('node_name_column'), header)
            for column_name in self.target_plan.get('property_columns'):
                self.check_column(column_name, header)

        if self.edge_plan:
            self.check_column(self.edge_plan.get('id_column'), header)
            self.check_column(self.edge_plan.get('predicate_id_column'), header)
            for column_name in self.edge_plan.get('property_columns'):
                self.check_column(column_name, header)

    def check_column(self, column_name, header):
        if column_name:
            if not column_name in header:
                raise Exception("Error in import plan: column name " + column_name + " in import plan is not in header " + str(header))

    def convert_tsv_to_cx(self, filename, max_rows = None):
        self.identifier_to_cx_id_map = {
            "nodes": {},
            "edges": {},
            "citations": {}
        }
        self.id_counter = 1000
        self.node_count = 0
        self.edge_count = 0
        self.cx_out = []
        self.emit_number_verification()
        self.add_context(self.default_context)
        self.add_context(self.source_context)
        self.add_context(self.target_context)
        self.add_context(self.predicate_context)
        self.emit_context()
        self.cx_identifier_to_citation_map = {}

        network_name = ntpath.basename(filename)

        self.cx_out.append({"networkAttributes" : [ {"n" : "name", "v" : network_name} ]})

        with open(filename, 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]
            self.check_header_vs_plan(header);
            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab', fieldnames=header)
            row_count = 0
            for row in reader:
                if self.handle_row(row):
                    row_count = row_count + 1
                if max_rows and row_count > max_rows:
                    break

        self.emit_post_metadata()
        return self.cx_out

    def emit_number_verification(self):
        self.cx_out.append({'numberVerification': [{'longNumber': 281474976710655}]})

    def emit_post_metadata(self):
        self.cx_out.append( {'metaData': [
            {'idCounter': self.node_count, 'name': 'nodes'},
            {'idCounter': self.edge_count, 'name': 'edges'}
        ]})

    def check_string(self, my_string, context = ""):
        if my_string:
            if my_string == "":
                print "Skipping Blank String"
                return False
            try:
                my_string.decode('ascii')
            except UnicodeDecodeError:
                print "Skipping Non-Ascii String: " + my_string
                #print "type: " + str(type(my_string))
                #print "could try  " + my_string.decode('utf-8')
                return False
            else:
                return True
        else:
            print "Skipping Null String " + context
            return False

    def handle_row(self, row):

        # For each row, we create an edge + edge properties
        # For that edge, we may create elements if they are new
        # - source node + properties
        # - target node + properties
        # - predicate term
        source_node_cx_id = self.handle_row_source(row)
        if not source_node_cx_id:
            print "Skipping Bad Row (source problem) :" + str(row)
            return False

        target_node_cx_id = self.handle_row_target(row)
        if not target_node_cx_id:
            print "Skipping Bad Row (target problem) :" + str(row)
            return False

        self.handle_edge(row, source_node_cx_id, target_node_cx_id)

        return True

    # returns either the cx_id of the source node or False
    def handle_row_source(self, row):

        if self.source_use_names_as_identifiers:
            source_node_name = row.get(self.source_node_name_column)
            if not self.check_string(source_node_name):
                return False
            return self.handle_node(row, source_node_name, None, self.source_columns, source_node_name)

        else:
            source_id = row.get(self.source_id_column)
            if not self.check_string(source_id):
                return False

            prefix = None
            if self.source_context:
                prefix = self.source_context.get('prefix')

            source_term = self.get_term(source_id, prefix)

            if self.source_node_name_column:
                source_node_name = row.get(self.source_node_name_column)
                if not self.check_string(source_node_name):
                    return False
            else:
                source_node_name = None

            return self.handle_node(row, source_id, source_term, self.source_columns, source_node_name)

    # returns either the cx_id of the target node or False
    def handle_row_target(self, row):

        if self.target_use_names_as_identifiers:
            target_node_name = row.get(self.target_node_name_column)
            if not self.check_string(target_node_name):
                    return False
            return self.handle_node(row, target_node_name, None, self.target_columns, target_node_name)

        else:
            target_id = row.get(self.target_id_column)
            if not self.check_string(target_id, 'target_id in ' + self.target_id_column):
                return False

            prefix = None
            if self.target_context:
                prefix = self.target_context.get('prefix')

            target_term = self.get_term(target_id, prefix)

            if self.target_node_name_column:
                target_node_name = row.get(self.target_node_name_column)
                if not self.check_string(target_node_name):
                    return False
            else:
                target_node_name = None

            return self.handle_node(row, target_id, target_term, self.target_columns, target_node_name)

    def emit_context(self):
        if len(self.context_map.values()) > 0:
            self.cx_out.append({"@context": [self.context_map]})

    def add_context(self, context):
        if not context:
            return None
        prefix = context.get('prefix')
        mapped_uri = self.context_map.get(prefix)
        if not mapped_uri:
            self.context_map[prefix] = context.get('uri')
        else:
            if not mapped_uri == context.get('uri'):
                raise Exception("Context conflict: prefix " + prefix + ' maps to both ' + mapped_uri + ' and ' + context.get('uri'))

    def get_term(self, identifier, context_prefix):
        if context_prefix:
            return context_prefix + ":" + identifier
        else:
            return identifier

    def handle_node(self, row, identifier, term_string, property_columns, node_name):
        cx_id = self.get_cx_id_for_identifier('nodes', identifier, False)
        if cx_id:
            return cx_id
        # get an id and add the node aspect element
        cx_id = self.get_cx_id_for_identifier('nodes', identifier)
        cx_node = {'@id': cx_id}

        if term_string:
            cx_node['r'] = term_string
        if node_name:
            cx_node['n'] = node_name

        self.cx_out.append({"nodes": [cx_node]})
        self.node_count += 1

        # now handle the properties, if any
        if property_columns:
            for column in property_columns:
                value = row.get(column)
                if value:
                    attribute = {"po": cx_id,
                            "n": column,
                            "v": value}
                    self.cx_out.append({'nodeAttributes': [attribute]})

        return cx_id

    def handle_edge(self, row, source_node_cx_id, target_node_cx_id):
        edge_cx_id = self.get_next_cx_id()

        if self.predicate_id_column:
            predicate_string = row.get(self.predicate_id_column)
        else:
            predicate_string = self.default_predicate

        if self.predicate_context and self.predicate_context.get('prefix'):
            predicate_prefix = self.predicate_context.get('prefix')

        else:
            predicate_prefix = None

        predicate = self.get_term(predicate_string, predicate_prefix)

        self.cx_out.append(
            {'edges': [
                {'@id': edge_cx_id,
                 's': source_node_cx_id,
                 't': target_node_cx_id,
                 'i': predicate}]})
        self.edge_count += 1

        citation_plan = self.edge_plan.get('citation_plan')

        if citation_plan:
             self.handle_citation('edges', edge_cx_id, row, citation_plan)

        if self.edge_columns:
            for column in self.edge_columns:
                value = row.get(column)
                if value:
                    attribute = {"po": edge_cx_id,
                                "n": column,
                                "v": value}
                    self.cx_out.append({'edgeAttributes': [attribute]})

    def handle_citation(self, aspect, element_id, row, citation_plan):

#         {
#   "citations" : [ {
#     "@id" : 91477479,
#     "dc:title" : "",
#     "dc:contributor" : null,
#     "dc:identifier" : "pmid:11163242",
#     "dc:type" : "URI",
#     "dc:description" : null,
#     "attributes" : [ ]
#   } ]
# }

# "edgeCitations": [
# {
# "citations": [590],
# "po": [24]
# }
# ]

        # iterate through possible key columns:
        identifiers = []
        idType = None

        for id_column in citation_plan.get('citation_id_columns'):
            col = id_column.get('id')
            delimiter = id_column.get('delimiter')
            id_string = row.get(col)
            if id_string:
                if delimiter:
                    for id in id_string.split(delimiter):
                        trimmed = id.strip()
                        identifiers.append(trimmed)
                else:
                    identifiers.append(id_string)
                idType = id_column.get('type')
                break

        for identifier in identifiers:
            # special handling for Pmid type
            citation_id_type = idType
            if idType.lower() == 'pmid' :
                identifier = 'pmid:' + identifier
                citation_id_type = 'URI'
                # print identifier

            citation = self.cx_identifier_to_citation_map.get(identifier)

            if not citation:
                # no citation found by that identifier. create a new citation
                citation_cx_id = self.get_cx_id_for_identifier('citations', identifier, True)
                citation = {"@id": citation_cx_id,
                            "dc:identifier": identifier,
                            "dc:type": citation_id_type
                            }
                self.cx_identifier_to_citation_map[identifier] = citation
                # add title and contributors if known
                title_column = citation_plan.get('title_column')
                if title_column:
                    title = row.get(title_column)
                    if title:
                        citation['dc:title'] = title

                # add title and contributors if known
                contributors_column = citation_plan.get('contributors_column')
                if contributors_column:
                    contributors_string = row.get(contributors_column)
                    contributors = contributors_string.split(';')
                    if contributors:
                        citation['dc:contributors'] = contributors

                self.cx_out.append({'citations': [citation]})

            citation_id = citation.get('@id')
            # now we need to output the edgeCitation or nodeCitation aspect
            if aspect == 'edges':
                self.cx_out.append({'edgeCitations': [{'po': [element_id], 'citations' : [citation_id]}]})




