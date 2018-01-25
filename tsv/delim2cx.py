
import csv
import json
from ndex.networkn import data_to_type
from os import path
from jsonschema import validate
from ndex.ndexGraphBuilder import ndexGraphBuilder
import pandas as pd
import ndex2
import time
import re
import numpy as np
import types
import six
import gspread
from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE



# convert a delimited file to CX based on a JSON 'plan' which specifies the mapping of
# column values to edges, source nodes, and target nodes

version="0.1"

class TSVLoadingPlan:
    def __init__ (self,plan_filename):

        #open the schema first
        here = path.abspath(path.dirname(__file__))
        with open(path.join(here, 'loading_plan_schema.json')) as json_file:
            plan_schema = json.load(json_file)

        with open(plan_filename) as json_file:
            import_plan = json.load(json_file)

        validate(import_plan,plan_schema)

        #Need documentation for this field. Looks like this will be applied to both source and
        #target nodes if no 'context' is applied to them.
        self.context = import_plan.get('context')

        #Defines the mappings of source nodes of edges
        #If id_column is defined, use it as represent, otherwise use name_column as identifier.
        #If both are defined, what would be the expected behaviour?
        self.source_plan = import_plan.get('source_plan')

        #Defines the mappings of target nodes of edges
        self.target_plan = import_plan.get('target_plan')

        self.edge_plan = import_plan.get('edge_plan')


class TSV2CXConverter:
    def __init__(self, plan):

        # the plan specifying the parsing of rows
        self.plan = plan
        self.ng_builder = ndexGraphBuilder() #   Graph()


    def check_header_vs_plan(self, header):
        # each column name referenced in the plan must be in the header, otherwise raise an exception
        self.check_column(self.plan.source_plan.get('id_column'), header)
        self.check_column(self.plan.source_plan.get('node_name_column'), header)
        self.check_column(self.plan.source_plan.get('alias_column'),header)
        self.check_plan_property_columns(self.plan.source_plan,header)

        self.check_column(self.plan.target_plan.get('id_column'), header)
        self.check_column(self.plan.target_plan.get('node_name_column'), header)
        self.check_plan_property_columns(self.plan.target_plan, header)

        self.check_column(self.plan.edge_plan.get('id_column'), header)
        self.check_column(self.plan.edge_plan.get('predicate_id_column'), header)
        self.check_column(self.plan.edge_plan.get('citation_id_column'), header)
        self.check_plan_property_columns(self.plan.edge_plan, header)


    def check_plan_property_columns (self, comp_plan, header) :
        props = comp_plan.get('property_columns')
        if props:
            for column_name in props:
                if isinstance(column_name,six.string_types):
                    self.check_property_column(column_name, header)
                elif hasattr(column_name, 'column_name'):
                    self.check_column(column_name['column_name'],header)

    def check_column(self, column_name, header):
        if column_name:
            if not column_name in header:
                raise Exception("Error in import plan: column name " + column_name + " in import plan is not in header " + str(header))

    def check_property_column(self, column_name_raw, header):
        if column_name_raw:
            col_list = column_name_raw.split("::")
            if len(col_list) > 2:
                    raise Exception("Column name '" + column_name_raw + "' has too many :: in it")
            else:
                column_name = col_list[0]
                if not column_name in header:
                    raise Exception(
                        "Error in import plan: column name " + column_name + " in import plan is not in header " + str(
                            header))

    #==================================
    # CONVERT TSV TO CX USING Network_n
    #==================================
    def convert_tsv_to_cx(self, filename, max_rows = None,  name=None, description=None, network_attributes=None, provenance=None):

        t1 = long(time.time()*1000)
        #Add context if they are defined
        if self.plan.context:
            self.ng_builder.addNamespaces(self.plan.context)

        with open(filename, 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]
            self.check_header_vs_plan(header)

            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab', fieldnames=header)
            row_count = 2
            # for debugging purposes, max_rows can be set so that only a subset of a large file is processed
            for row in reader:
                # As each row is processed, self.G_nx is updated
                try :
                    self.process_row(row)
                    row_count = row_count + 1
                    if max_rows and row_count > max_rows+2:
                        break
                except RuntimeError as err1:
                    print "Error occurred in line " + str(row_count) + ". Message: " + err1.message
                    raise err1
                except Exception as err2:
                    print "Error occurred in line " + str(row_count) + ". Message: " + err2.message
                    raise err2

        ndexGraph = self.ng_builder.getNdexGraph()
        if network_attributes:
            for attribute in network_attributes:
                if attribute.get("n") == "name":
                    ndexGraph.set_name(attribute.get("v"))
                else:
                    ndexGraph.set_network_attribute(attribute.get("n"), attribute.get("v"))

        tsv_data_event = {
                "inputs": None,
                "startedAtTime": t1,
                "endedAtTime": long(time.time()*1000),
                "eventType": "TSV network generation",
                "properties": [{
                                "name": "TSV loader version",
                                "value": version
                            }]
            }
        if False:
            ndexGraph.set_provenance({
                                        "entity":provenance
                                    })
            #ndexGraph.update_provenance("creationEvent", tsv_data_event)
        else:
            ndexGraph.set_provenance({
                                        "entity": {
                                                    "creationEvent": tsv_data_event
                                                    }
                                     })

        # name and description take precedence over any prior values
        if name:
            ndexGraph.set_name(name)
        if description:
            ndexGraph.set_network_attribute('description', description)

        return ndexGraph

    #==================================
    # CONVERT GOOGLE SHEET TO CX USING Network_n
    #==================================
    def convert_google_worksheet_to_cx(self, worksheet, max_rows = None,  name=None, description=None):

        t1 = long(time.time()*1000)
        #Add context if they are defined
        if self.plan.context:
            self.ng_builder.addNamespaces(self.plan.context)

        # Get records - list of dicts with column names as keys
        records = worksheet.get_all_records()
        # count the rows as shown in sheet, i.e. first data row is #2
        row_count = 2
        for row in records:
            try:
                self.process_row(row)
                row_count = row_count + 1
                if max_rows and row_count > max_rows+2:
                    break
            except RuntimeError as err1:
                print "Error occurred in line " + str(row_count) + ". Message: " + err1.message
                raise err1
            except Exception as err2:
                print "Error occurred in line " + str(row_count) + ". Message: " + err2.message
                raise err2

        ndexGraph = self.ng_builder.getNdexGraph()

        ndexGraph.set_name(name)
        ndexGraph.set_network_attribute('description', description)
        ndexGraph.set_provenance(
            {
                "entity": {
                    "creationEvent": {
                        "inputs": None,
                        "startedAtTime": t1,
                        "endedAtTime": long(time.time()*1000),
                        "eventType": "TSV network generation",
                        "properties": [{
                            "name": "TSV loader version",
                            "value": version
                        }]
                    }
                }
            }
        )
        return ndexGraph

    #==================================
    # Process Row USING Networkn
    # Added by Aaron G
    #==================================
    def process_row(self, row):
        # For each row, we create an edge + edge properties
        # For that edge, we may create elements if they are new
        # - source node + properties
        # - target node + properties
        # - predicate term

        source_node_id = self.create_node(row, self.plan.source_plan)
        target_node_id = self.create_node(row, self.plan.target_plan)

        self.create_edge(source_node_id, target_node_id, row)


    def create_node(self, row, node_plan):

        nodeName = None
        nodeRepresent = None
        ext_id = None
        use_name_as_id = False

        if not node_plan.get('id_column'):
            use_name_as_id = True

        if use_name_as_id and node_plan.get('id_prefix'):
            raise RuntimeError("Id column needs to be defined if id_prefix is defined in your query plan.")

        if 'node_name_column' in node_plan:
            nodeName = row.get(node_plan['node_name_column'])

        if use_name_as_id:
            ext_id = nodeName
        else:
            ext_id = row.get(node_plan['id_column'])

        if not ext_id:
            raise RuntimeError("Id value is missing.")

        if  node_plan.get('id_prefix'):
            ext_id = node_plan['id_prefix'] + ":" + ext_id

        node_attr = self.create_attr_obj(node_plan, row)

     #   if 'alias_column' in node_plan:
        if use_name_as_id:
            return self.ng_builder.addNode(ext_id, nodeName, None, node_attr)
        else:
            return self.ng_builder.addNode(ext_id,nodeName,ext_id,node_attr)

    def create_attr_obj (self, comp_plan, row):
        attr = {}
        if comp_plan.get('property_columns'):
            for column_raw in comp_plan['property_columns']:
                if isinstance(column_raw, six.string_types):
                    col_list = column_raw.split("::")
                    if len(col_list) == 1:
                        column = col_list[0]
                        value = row.get(column)
                        if value:
                            attr[column] = value
                    elif len(col_list) > 2:
                        raise Exception("Column name '" + column_raw + "' has too many :: in it")

                    else:
                        data_type = col_list[len(col_list) - 1]
                        column = col_list[0]
                        value = row.get(column)
                        if value:
                            attr[column] = data_to_type(value, data_type)
                else:
                    value = None

                    if column_raw.get('column_name'):
                        value = row.get(column_raw['column_name'])

                    if (value is None) and column_raw.get('default_value'):
                        value = column_raw['default_value']

                    if value:
                        if column_raw.get('data_type'):
                            value = data_to_type(value, column_raw['data_type'])

                        if column_raw.get('value_prefix'):
                            value = column_raw.get('value_prefix') + ":"+ value


                        if column_raw.get('attribute_name'):
                            attr[column_raw['attribute_name']] = value
                        else:
                            attr[column_raw['column_name']] = value

        return attr

    def create_edge(self, src_node_id, tgt_node_id, row):

        predicate_str = None
        if  self.plan.edge_plan.get('predicate_id_column'):
            predicate_str = row.get(self.plan.edge_plan['predicate_id_column'])

        if not predicate_str and self.plan.edge_plan.get('default_predicate'):
            predicate_str = self.plan.edge_plan['default_predicate']

        if not predicate_str :
            raise RuntimeError("Value for predicate string is not found this row.")

        if self.plan.edge_plan.get("predicate_prefix"):
            predicate_str = self.plan.edge_plan['predicate_prefix']+ ":"+ predicate_str

        edge_attr = self.create_attr_obj(self.plan.edge_plan, row)

        #Deal with citiations
        citation_id = None
        if  self.plan.edge_plan.get("citation_id_column"):
            citation_id = row.get(self.plan.edge_plan['citation_id_column'])

        if citation_id is not None:
            citation_id = citation_id.replace(';', ',')
            citation_id = citation_id.replace('|', ',')
            citation_id = re.split('\s*,\s*',citation_id)

        if citation_id and self.plan.edge_plan.get("citation_id_prefix"):
                newList = []
                for cid in citation_id:
                    newList.append(self.plan.edge_plan["citation_id_prefix"] + ":" + cid)
                citation_id = newList

        if citation_id :
            edge_attr['citation_ids'] = citation_id

        self.ng_builder.addEdge(src_node_id,tgt_node_id,predicate_str, edge_attr)


#=====================
# NON-CLASS FUNCTIONS
#=====================
def convert_pandas_to_nice_cx_with_load_plan(pandas_dataframe, load_plan, max_rows=None,
                                            name=None, description=None,
                                            network_attributes=None, provenance=None):
    node_lookup = {}
    nice_cx = ndex2.NiceCXNetwork()
    row_count = 0
    t1 = long(time.time()*1000)
    #Add context if they are defined
    if load_plan.get('context'):
        nice_cx.set_context([load_plan.get('context')])
        #self.ng_builder.addNamespaces(self.plan.context)

    for index, row in pandas_dataframe.iterrows():
        # As each row is processed, self.G_nx is updated
        process_row(nice_cx, load_plan, row, node_lookup)
        row_count = row_count + 1
        if max_rows and row_count > max_rows + 2:
            break

        #try :
        #    process_row(nice_cx, load_plan, row, , node_lookup)
        #    row_count = row_count + 1
        #    if max_rows and row_count > max_rows+2:
        #        break
        ##except RuntimeError as err1:
        #    print "Error occurred in line " + str(row_count) + ". Message: " + err1.message
        #    raise err1
        #except Exception as err2:
        #    print "Error occurred in line " + str(row_count) + ". Message: " + err2.message
        #    raise err2

    #ndexGraph = self.ng_builder.getNdexGraph()
    if network_attributes:
        for attribute in network_attributes:
            if attribute.get("n") == "name":
                nice_cx.set_name(attribute.get("v"))
            else:
                nice_cx.set_network_attribute(name=attribute.get("n"), values=attribute.get("v"), type=attribute.get("d"))

    tsv_data_event = {
            "inputs": None,
            "startedAtTime": t1,
            "endedAtTime": long(time.time()*1000),
            "eventType": "TSV network generation",
            "properties": [{
                            "name": "TSV loader version",
                            "value": version
                        }]
        }

    # name and description take precedence over any prior values
    if name:
        nice_cx.set_name(name)
    if description:
        nice_cx.set_network_attribute(name='description', values=description)

    return nice_cx

#==================================
# Process Row USING NiceCX
# Added by Aaron G
#==================================
def process_row(nice_cx, load_plan, row, node_lookup):
    # For each row, we create an edge + edge properties
    # For that edge, we may create elements if they are new
    # - source node + properties
    # - target node + properties
    # - predicate term

    source_node = create_node(row, load_plan.get('source_plan'), nice_cx, node_lookup)
    target_node = create_node(row, load_plan.get('target_plan'), nice_cx, node_lookup)

    create_edge(nice_cx, source_node.get_id(), target_node.get_id(), row, load_plan)

def create_node(row, node_plan, nice_cx, node_lookup):

    nodeName = None
    nodeRepresent = None
    ext_id = None
    use_name_as_id = False

    if not node_plan.get('rep_column'):
        raise Exception("Represents is a required element of the plan")

    if not node_plan.get('node_name_column'):
        raise Exception("Node name is a required element of the plan")

    if use_name_as_id and node_plan.get('rep_prefix'):
        raise RuntimeError("Id column needs to be defined if id_prefix is defined in your query plan.")

    node_name = row[node_plan['node_name_column']]

    if not node_name:
        raise RuntimeError("Id value is missing.")

    ext_id = row[node_plan['rep_column']]

    if not ext_id:
        raise RuntimeError("Id value is missing.")

    if node_plan.get('rep_prefix'):
        ext_id = node_plan['rep_prefix'] + ":" + str(ext_id)

    node_element = find_or_create_node(nice_cx, node_name, ext_id, node_lookup)

    # ATTRIBUTES
    add_node_attributes(nice_cx, node_element, node_plan, row)

    return node_element


def create_edge(nice_cx, src_node_id, tgt_node_id, row, import_plan):
    predicate_str = None
    edge_plan = import_plan.get('edge_plan')
    if edge_plan.get('predicate_id_column'):
        predicate_str = row[edge_plan['predicate_id_column']]

    if not predicate_str and edge_plan.get('default_predicate'):
        predicate_str = edge_plan['default_predicate']

    if not predicate_str:
        raise RuntimeError("Value for predicate string is not found in this row.")

    if edge_plan.get("predicate_prefix"):
        predicate_str = edge_plan['predicate_prefix'] + ":" + predicate_str

    edge_id = nice_cx.create_edge(edge_source=src_node_id, edge_target=tgt_node_id, edge_interaction=predicate_str)

    add_edge_attributes(nice_cx, edge_id, edge_plan, row)

    # Deal with citiations
    citation_id = None
    if edge_plan.get("citation_id_column"):
        citation_id = str(row[edge_plan['citation_id_column']])

    if citation_id is not None:
        citation_id = citation_id.replace(';', ',')
        citation_id = citation_id.replace('|', ',')
        citation_id = re.split('\s*,\s*', citation_id)

    if citation_id and edge_plan.get("citation_id_prefix"):
        newList = []
        for cid in citation_id:
            newList.append(edge_plan["citation_id_prefix"] + ":" + cid)
        citation_id = newList

    if citation_id:
        nice_cx.set_edge_attribute(edge_id, 'citation_ids', citation_id, type='list_of_string')


valid_cx_data_types = ['boolean', 'byte', 'char', 'double', 'float', 'integer', 'long', 'short', 'string', 'list_of_boolean',
 'list_of_byte', 'list_of_char', 'list_of_double', 'list_of_float', 'list_of_integer', 'list_of_long',
 'list_of_short','list_of_string']

def add_node_attributes(nice_cx, node_element, load_plan, row):
    if load_plan.get('property_columns'):
        for column_raw in load_plan['property_columns']:
            value = None

            if column_raw.get('column_name'):
                value = row.get(column_raw['column_name'])

            if (value is None) and column_raw.get('default_value'):
                value = column_raw['default_value']

            if value:
                if column_raw.get('data_type'):
                    if column_raw['data_type'] not in valid_cx_data_types:
                        raise Exception('data_type: ' + column_raw['data_type'] + ' is not valid')

                    value = data_to_type(value, column_raw['data_type'])

                if column_raw.get('value_prefix'):
                    value = column_raw.get('value_prefix') + ":" + str(value)

                if column_raw.get('attribute_name'):
                    # create
                    nice_cx.set_node_attribute(node_element, column_raw['attribute_name'], value, type=column_raw.get('data_type'))
                else:
                    nice_cx.set_node_attribute(node_element, column_raw['column_name'], value, type=column_raw.get('data_type'))

def add_edge_attributes(nice_cx, edge_id, load_plan, row):
    if load_plan.get('property_columns'):
        for column_raw in load_plan['property_columns']:
            value = None

            if column_raw.get('column_name'):
                value = row.get(column_raw['column_name'])

            if pd.isnull(value):
                if column_raw.get('default_value'):
                    value = column_raw['default_value']
                else:
                    continue

            if value:
                dt = None
                if column_raw.get('data_type'):
                    dt = str(column_raw.get('data_type'))
                    if dt not in valid_cx_data_types:
                        raise Exception('data_type: ' + dt + ' is not valid')

                    value = data_to_type(value, dt)

                if column_raw.get('value_prefix'):
                    value = column_raw.get('value_prefix') + ":" + str(value)

                if column_raw.get('attribute_name'):
                    nice_cx.set_edge_attribute(edge_id, column_raw['attribute_name'], value, type=dt)
                else:
                    nice_cx.set_edge_attribute(edge_id, column_raw['column_name'], value, type=dt)




def data_to_type(data, data_type):
    return_data = None

    if(type(data) is str):
        data = data.replace('[', '').replace(']','')
        if('list_of' in data_type):
            data = data.split(',')

    if data_type == "boolean":
        if(type(data) is str):
            return_data = data.lower() == 'true'
        else:
            return_data = bool(data)
    elif data_type == "byte":
        return_data = str(data).encode()
    elif data_type == "char":
        return_data = str(data)
    elif data_type == "double":
        return_data = float(data)
    elif data_type == "float":
        return_data = float(data)
    elif data_type == "integer":
        return_data = int(data)
    elif data_type == "long":
        return_data = int(data)
    elif data_type == "short":
        return_data = int(data)
    elif data_type == "string":
        return_data = str(data)
    elif data_type == "list_of_boolean":
        # Assumption: if the first element is a string then so are the rest...
        if(type(data[0]) is str):
            return_data = [s.lower() == 'true' for s in data]
        else:
            return_data = [bool(s) for s in data]
    elif data_type == "list_of_byte":
        return_data = [bytes(s) for s in data]
    elif data_type == "list_of_char":
        return_data = [str(s) for s in data]
    elif data_type == "list_of_double":
        return_data = [float(s) for s in data]
    elif data_type == "list_of_float":
        return_data = [float(s) for s in data]
    elif data_type == "list_of_integer":
        return_data = [int(s) for s in data]
    elif data_type == "list_of_long":
        return_data = [int(s) for s in data]
    elif data_type == "list_of_short":
        return_data = [int(s) for s in data]
    elif data_type == "list_of_string":
        return_data = [str(s) for s in data]
    else:
        return_data = str(data)

    return return_data

'''
def create_edge(src_node_id, tgt_node_id, row, plan, nice_cx):

    predicate_str = None
    if  plan.edge_plan.get('predicate_id_column'):
        predicate_str = row.get(plan.edge_plan['predicate_id_column'])

    if not predicate_str and plan.edge_plan.get('default_predicate'):
        predicate_str = plan.edge_plan['default_predicate']

    if not predicate_str :
        raise RuntimeError("Value for predicate string is not found this row.")

    if plan.edge_plan.get("predicate_prefix"):
        predicate_str = plan.edge_plan['predicate_prefix']+ ":"+ predicate_str

    edge_attr = create_attr_obj(plan.edge_plan, row)

    #Deal with citiations
    citation_id = None
    if  self.plan.edge_plan.get("citation_id_column"):
        citation_id = row.get(self.plan.edge_plan['citation_id_column'])

    if citation_id is not None:
        citation_id = citation_id.replace(';', ',')
        citation_id = citation_id.replace('|', ',')
        citation_id = re.split('\s*,\s*',citation_id)

    if citation_id and plan.edge_plan.get("citation_id_prefix"):
            newList = []
            for cid in citation_id:
                newList.append(plan.edge_plan["citation_id_prefix"] + ":" + cid)
            citation_id = newList

    if citation_id :
        edge_attr['citation_ids'] = citation_id

    ng_builder.addEdge(src_node_id,tgt_node_id,predicate_str, edge_attr)
'''

def find_or_create_node(nice_cx, name, represents, node_lookup):
    if node_lookup.get(represents):
        return nice_cx.nodes.get(node_lookup.get(represents))
    else:
        new_node_id = nice_cx.create_node(node_name=name, node_represents=represents)
        node_lookup[represents] = new_node_id
        return nice_cx.nodes.get(new_node_id)

if __name__ == '__main__':
    print('made it')

