__author__ = 'dexter'


import csv

# convert a delimited file of identifiers and values to CX so it can be stored as a
# node-only network with properties.
# key point is to figure out which column (or later columns) has the node identifier

# This could be converted to streaming later...

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

        self.default_context = plan.get('default_context')

        self.source_plan = plan.get('source_plan')


        if self.source_plan:
            self.source_context = self.source_plan.get('context')
            if not self.source_context:
                self.source_context = self.default_context
            self.source_id_column = self.source_plan.get('id_column')
            self.source_node_name_column = self.source_plan.get('node_name_column')
            self.source_columns = self.source_plan.get('property_columns')

        self.target_plan = plan.get('target_plan')
        if self.target_plan:
            self.target_context = self.target_plan.get('context')
            if not self.target_context:
                self.target_context = self.default_context
            self.target_id_column = self.target_plan.get('id_column')
            self.target_node_name_column = self.target_plan.get('node_name_column')
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

        self.init_for_convert()

    def init_for_convert(self):
        self.identifier_to_cx_id_map = {
            "nodes": {},
            "edges": {},
            "citations": {}
        }
        self.id_counter = 1000
        self.cx_out = []

    def get_cx_id_for_identifier(self, aspect, identifier, create=True):
        map = self.identifier_to_cx_id_map.get(aspect)
        cx_id = map.get(identifier)
        if cx_id:
            return cx_id
        if create:
            cx_id = self.get_next_cx_id()
            map[identifier] = cx_id
            return cx_id
        return False

    def get_next_cx_id(self):
        self.id_counter += 1
        return '_:' + str(self.id_counter)

    def convert_tsv(self, filename, max_rows):
        self.init_for_convert()
        self.init_context(self.default_context)
        self.init_context(self.source_context)
        self.init_context(self.target_context)
        self.init_context(self.predicate_context)
        self.cx_identifier_to_citation_map = {}

        with open(filename,'rU') as tsvfile:
            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab')
            row_count = 0;
            for row in reader:
                if self.handle_row(row):       
                    row_count = row_count + 1
                if row_count > max_rows:
                    break

        # We add the citation to cx_out at the very end because
        # they may accumulate edges over the entire TSV
        for identifier, citation in self.cx_identifier_to_citation_map.iteritems():
            self.cx_out.append({'citations': [citation]})

        return self.cx_out

    def handle_row(self, row):

        # For each row, we create an edge + edge properties
        # For that edge, we may create elements if they are new
        # - source node + properties
        # - target node + properties
        # - predicate term

        source_id = row.get(self.source_id_column)
        target_id = row.get(self.target_id_column)

        #print row

        if not source_id or not target_id:
            return False

        prefix = self.source_context.get('prefix')
        source_term = self.get_term(source_id, prefix)

        if self.source_node_name_column:
            source_node_name = row.get(self.source_node_name_column)
        else:
            source_node_name = None

        source_node_cx_id = self.handle_node(row, source_id, source_term, self.source_columns, source_node_name)


        prefix = self.target_context.get('prefix')
        target_term = self.get_term(target_id, prefix)
        if self.target_node_name_column:
            target_node_name = row.get(self.target_node_name_column)
        else:
            target_node_name = None

        target_node_cx_id = self.handle_node(row, target_id, target_term, self.target_columns, target_node_name)

        self.handle_edge(row, source_node_cx_id, target_node_cx_id)
        
        return True

    def init_context(self, context):
        if not context:
            return None
        cx_context = {}
        uri = context.get('uri')
        prefix = context.get('prefix')
        cx_context = {prefix: uri}
        self.cx_out.append({"@context": [cx_context]})

    def get_term(self, identifier, context_prefix):
        return context_prefix + ":" + identifier

    def handle_node(self, row, identifier, term_string, property_columns, node_name):
        cx_id = self.get_cx_id_for_identifier('nodes', identifier, False)
        if cx_id:
            return cx_id
        # get an id and add the node aspect element
        cx_id = self.get_cx_id_for_identifier('nodes', identifier)
        cx_node = {'@id': cx_id}
        self.cx_out.append({"nodes": [cx_node]})

        # create the node identity element
        cx_node_identity = {'node': cx_id, 'represents': term_string}
        if node_name:
            cx_node_identity['name'] = node_name;
        self.cx_out.append({"nodeIdentities": [cx_node_identity]})


        # now handle the properties
        for column in property_columns:
            value = row.get(column)
            if value:
                prop = {"node": cx_id,
                        "property": column,
                        "value": value}
                self.cx_out.append({'elementProperties': [prop]})

        return cx_id

    def handle_edge(self, row, source_node_cx_id, target_node_cx_id):
        edge_cx_id = self.get_next_cx_id()

        self.cx_out.append(
            {'edges': [
                {'@id': edge_cx_id,
                 'source': source_node_cx_id,
                 'target': target_node_cx_id}]})

        if self.predicate_id_column:
            predicate = row.get(self.predicate_id_column)
        else:
            predicate = self.default_predicate

        predicate = self.get_term(predicate, self.predicate_context.get('prefix'))

        self.cx_out.append({'edgeIdentities': [{'edge': edge_cx_id, 'relationship': predicate}]})

        citation_plan = self.edge_plan.get('citation_plan')
        if citation_plan:
            self.handle_citation('edges', edge_cx_id, row, citation_plan)

        for column in self.edge_columns:
            value = row.get(column)
            if value:
                property = {"edge": edge_cx_id,
                            "property": column,
                            "value": value}
                self.cx_out.append({'elementProperties': [property]})

    def handle_citation(self, aspect, element_id, row, citation_plan):
        # iterate through possible key columns:
        identifier = None
        idType = None
        for id_column in citation_plan.get('citation_id_columns'):
            col = id_column.get('id')
            id = row.get(col)
            if id:
                identifier = id
                idType = id_column.get('type')
                break
        if identifier:
            # special handling for Pmid type
            if idType.lower() == 'pmid' :
                identifier = 'pmid:' + identifier
                idType = 'URI'

            citation = self.cx_identifier_to_citation_map.get(identifier)
            if not citation:
                # need to create a new citation
                citation_cx_id = self.get_cx_id_for_identifier('citations', identifier, False)
                citation = {"@id": citation_cx_id,
                            "identifier": identifier,
                            "idType": idType,
                            'edges': []}
                self.cx_identifier_to_citation_map[identifier] = citation
                # add title and contributors if known
                title_column = citation_plan.get('title_column')
                if title_column:
                    title = row.get(title_column)
                    if title:
                        citation['title'] = title

                # add title and contributors if known
                contributors_column = citation_plan.get('contributors_column')
                if contributors_column:
                    contributors_string = row.get(contributors_column)
                    contributors = contributors_string.split(';')
                    if contributors:
                        citation['contributors'] = contributors

            # now we need to add the edge id to the citation's edges or nodes
            citation[aspect].append(element_id)

            # we don't output the citation now.  Wait until all elements have been processed

