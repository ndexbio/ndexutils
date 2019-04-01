
import json
import csv
from os import path
import jsonschema
import logging
from ndexutil.exceptions import NDExUtilError

version = "0.1"

logger = logging.getLogger(__name__)


class CXStreamWriter:
    """Writes CX data to stream
    """

    def __init__(self, f):
        """
        Constructor
        :param f: Output stream
        """
        self._outputstream = f
        #  0 -- begining of a stream
        #  1 -- after premetadata, outside a fragment
        #  2 -- after postmetadata
        self._state = 0  # beginning of a stream

    def write_pre_metadata(self, metadata):
        """
        Writes the pre meta data aspect
        :param metadata:
        :raises NdexUtilError: if write_aspect_fragment or
                               write_post_metadata has already been called or
                               if output stream set in constructor is None
        :return: None
        """
        if self._outputstream is None:
            raise NDExUtilError("Output stream is None")
        if self._state != 0:
            raise NDExUtilError("PreMetadata has already been written, you can only write it once.")
        self._outputstream.write('[')
        json.dump({"numberVerification": [{"longNumber": 281474976710655}]}, self._outputstream)
        self._outputstream.write(',')
        json.dump({"metaData": metadata}, self._outputstream)
        self._outputstream.write(',\n')
        self._outputstream.flush()
        self._state = 1  # premetadata has been written.

    def write_aspect_fragment(self, fragment):
        """
        Writes aspect fragment.
        If the fragment have values of type list_of_double,
        list_of_boolean, list_of_long or list_of_integer
        the values in the list need to be quoted
        :param fragment: Fragment as list or dict to convert to JSON via json.dump
        :raises NdexUtilError: if write_pre_metadata has not been called first
        :return: None
        """
        if self._state != 1:
            raise NDExUtilError("Data aspects can only be written between PreMetadata and PostMetadata.")

        json.dump(fragment, self._outputstream)
        self._outputstream.write(',')

    def write_post_metadata(self, metadata):
        """
        Writes the post meta data aspect. Once this is called this object
        can no longer be used cause all methods will raise an error.
        :param metadata:
        :return:
        """
        if self._state != 1:
            raise NDExUtilError("Post metadata aspect can only be written after PreMetadata and data aspects.")
        json.dump({"metaData": metadata}, self._outputstream)
        self._outputstream.write(',')
        json.dump({"status": [{"error": "", "success": True}]}, self._outputstream)
        self._outputstream.write(']')
        self._outputstream.flush()
        self._state = 2


class StreamTSVLoader (object):
    """
    Stream based TSV Loader
    """

    def __init__(self, loading_plan_file, style_cx):
        """
        Constructor that loads and validates the loading_plan_file as well as extracts
        the style from the style_cx object
        :param loading_plan_file: Path to loading plan file
        :param style_cx: NiceCXNetwork object containing a style 'cyVisualProperties' as
                         an opaque aspect
        """

        # fullpath of the loading plan json file
        # style CX object (niceCX object)
        # _plan is the full loading plan
        # _sytle_cx is a niceCx object which has the style we are going to use in this loader.
        # read and validate the plan
        # open the schema first
        if style_cx:
            cy_visual_properties = style_cx.get_opaque_aspect("cyVisualProperties")
            if not cy_visual_properties:
                raise NDExUtilError("cyVisualProperties aspect is missing in style template CX.")
            if len(cy_visual_properties) != 3:
                raise NDExUtilError("cyVisualProperties in style template has " +
                                    str(len(cy_visual_properties)) + " elements. It should be 3.")
            self._visual_properties_aspect = cy_visual_properties
        else:
            self._visual_properties_aspect = None

        here = path.abspath(path.dirname(__file__))
        with open(path.join(here, 'loading_plan_schema.json')) as json_file:
            self._plan_schema = json.load(json_file)

        with open(loading_plan_file, 'r') as lp:
            self._plan = json.load(lp)

        try:
            jsonschema.validate(self._plan, self._plan_schema)

        except jsonschema.ValidationError as e1:
            print("Failed to parse the loading plan: " + e1.message)
            print('at path: ' + str(e1.absolute_path))
            print("in block: ")
            print(e1.instance)
            logger.exception(e1)
            raise NDExUtilError("Malformed TSV loading plan: " + str(e1.absolute_path) + ' : ' + str(e1))

    def write_cx_network(self, tsv_file_discriptor, output_file_descriptor,
                         network_attributes = None, batchsize=20000):
        """
        Both input and output descriptor as objects NOT file names.
        this function is not thread safe
        caller need to close the input and output stream after this function is executed.
        the attributes in the networkAttributes parameter need to be in the format
        of cx. eg: quoted values in list.

        :param tsv_file_discriptor:
        :param output_file_descriptor:
        :param network_attributes:
        :param batchsize:
        :return:
        """
        # initialize the environment
        self.batchsize = batchsize

        # table to track the node constructed in this network
        # key: the external id of the node. Can come from represent or node name depend on the loading plan
        # value: node and its attributes.
        self.nodeTable = {}
        self.nodeCounter = 0
        self.edgeCounter = 0
        self.nodeAttrCounter = 0
        self.edgeAttrCounter = 0
        self.newNodes = []  # new nodes in the batch, each element has nodes and nodesAttribute info
        self.newEdges = []  # new edges in the batch, each element has edges and edgesAttribute info

        # start the process
        header = [h.strip() for h in tsv_file_discriptor.readline().split('\t')]
        self._check_header_vs_plan(header)

        # initialize the writer
        self.cxWriter = CXStreamWriter(output_file_descriptor)

        # write the conext as network attribute
        net_attrs = []
        context = self._plan.get("context")
        if context:
            net_attrs.append({"n": "@context", "v": json.dumps(context)})
        if network_attributes:
            if type(network_attributes) is list:
                net_attrs.extend(network_attributes)
            else:
                net_attrs.append(network_attributes)

        # prepare metadata
        premetadata = [{
                "name": "nodes",
                "version": "1.0",
                "consistencyGroup": 1
            }, {
                "name": "edges",
                "version": "1.0",
                "consistencyGroup": 1
            }
            ]

        if self._plan.get("source_plan").get("property_columns") or self._plan.get("target_plan").get("property_columns"):
            premetadata.append({"name": "nodeAttributes",
                                "version": "1.0",
                                "consistencyGroup": 1})

        if self._plan.get("edge_plan").get("property_columns"):
            premetadata.append({
                                "name": "edgeAttributes",
                                "version": "1.0",
                                "consistencyGroup": 1
            })

        if net_attrs:
            premetadata.append({"name": "networkAttributes", "version": "1.0", "consistencyGroup": 1,
                                "elementCount": len(net_attrs)})

        if self._visual_properties_aspect:
            premetadata.append({"consistencyGroup": 1, "elementCount": 3, "name": "cyVisualProperties", "version": "1.0"})

        self.cxWriter.write_pre_metadata(premetadata)

        # write the network attr and styles
        if net_attrs:
            self.cxWriter.write_aspect_fragment({"networkAttributes": net_attrs})

        if self._visual_properties_aspect:
            self.cxWriter.write_aspect_fragment({"cyVisualProperties": self._visual_properties_aspect})

        # start processing the file
        reader = csv.DictReader(tsv_file_discriptor, dialect='excel-tab', fieldnames=header)
        row_count = 2
        # for debugging purposes, max_rows can be set so that only a subset of a large file is processed
        for row in reader:
            try:
                self._process_row(row)
                row_count = row_count + 1
            except RuntimeError as err1:
                print("Error occurred in line " + str(row_count) + ". Message: " + str(err1))
                raise err1
            except Exception as err2:
                print("Error occurred in line " + str(row_count) + ". Message: " + str(err2))
                raise err2

        # flush out whats left in the buffer
        self._print_batch()

        # write the post metadata and finish the writing

        postmetadata = [{"name": "nodes", "idCounter": self.nodeCounter, "elementCount": self.nodeCounter},
                        {"name": "edges", "idCounter": self.edgeCounter, "elementCount": self.edgeCounter},
                        {"name": "edgeAttributes", "elementCount": self.edgeAttrCounter},
                        {"name": "nodeAttributes", "elementCount": self.nodeAttrCounter}]

        self.cxWriter.write_post_metadata(postmetadata)

    def _check_header_vs_plan(self, header):
        # each column name referenced in the plan must be in the header, otherwise raise an exception
        StreamTSVLoader._check_column(self._plan.get('source_plan').get('rep_column'), header)
        StreamTSVLoader._check_column(self._plan.get('source_plan').get('node_name_column'), header)
        StreamTSVLoader._check_plan_property_columns(self._plan.get('source_plan'), header)

        StreamTSVLoader._check_column(self._plan.get('target_plan').get('rep_column'), header)
        StreamTSVLoader._check_column(self._plan.get('target_plan').get('node_name_column'), header)
        StreamTSVLoader._check_plan_property_columns(self._plan.get('target_plan'), header)

        StreamTSVLoader._check_column(self._plan.get('edge_plan').get('predicate_id_column'), header)
        StreamTSVLoader._check_column(self._plan.get('edge_plan').get('citation_id_column'), header)
        StreamTSVLoader._check_plan_property_columns(self._plan.get('edge_plan'), header)

    @staticmethod
    def _check_column(column_name, header):
        if column_name:
            if column_name not in header:
                raise Exception("Error in import plan: column name " + column_name +
                                " in import plan is not in header " + str(header))

    @staticmethod
    def _check_plan_property_columns(column_name_raw, header):
        if column_name_raw:
            if type(column_name_raw) is str:
                col_list = column_name_raw.split("::")
                if len(col_list) > 2:
                    raise Exception("Column name '" + column_name_raw + "' has too many :: in it")
                else:
                    column_name = col_list[0]
                    if column_name not in header:
                        raise Exception(
                            "Error in import plan: column name " + column_name + " in import plan is not in header " +
                            str(header))
            else:
                column_name = column_name_raw.get("column_name")
                if column_name and (column_name not in header):
                    raise Exception(
                        "Error in import plan: column name " + column_name + " in import plan is not in header " +
                        str(header))

    def _process_row(self, row):
        """
        For each row, we create an edge + edge properties
        For that edge, we may create elements if they are new
        - source node + properties
        - target node + properties
        - predicate term
        :param row:
        :return:
        """

        source_node_id = self._create_node(row, self._plan.get('source_plan'))
        target_node_id = self._create_node(row, self._plan.get('target_plan'))

        self._create_edge(source_node_id, target_node_id, row)

    def _create_node(self, row, node_plan):

        nodename = None

        use_name_as_id = False

        if not node_plan.get('rep_column'):
            use_name_as_id = True

        if use_name_as_id and node_plan.get('rep_prefix'):
            raise RuntimeError("rep_column needs to be defined if re_prefix is defined in your loading plan.")

        if 'node_name_column' in node_plan:
            nodename = row.get(node_plan['node_name_column'])

        if use_name_as_id:
            ext_id = nodename
        else:
            ext_id = row.get(node_plan['rep_column'])

        if not ext_id:
            raise RuntimeError("Id value is missing.")

        node_attr = self._create_attr_obj(node_plan, row)

        if use_name_as_id:
            represent = None
        else:
            represent = (node_plan['rep_prefix'] + ":" + ext_id) if node_plan.get('rep_prefix') else ext_id

        return self._add_node(ext_id, nodename, represent, node_attr)

    def _add_node(self, external_id, node_name, represent, attributes):
        existing_node = self.nodeTable.get(external_id)
        if existing_node:
            # check if everything matches
            if node_name != existing_node.get('n'):
                raise RuntimeError("Node name mismatch on node id " + external_id + ": " +
                                   (node_name if node_name else "''") + " vs " +
                                   existing_node.n if existing_node else "''")
            if existing_node.get('r') != represent:
                raise RuntimeError("Node represent mismatch on node id " + external_id + ": " + (represent if represent else "''")
                                   + " vs " + (existing_node.r if existing_node.r else "''"))

            # check attributes consistency
            tmp_node = {"n": node_name,
                        "r": represent,
                        "attr": attributes}
            tmp_node2 = {"n": existing_node.get("n"), "r": existing_node.get("r"), "attr": existing_node.get("attr")}

            if tmp_node != tmp_node2:
                raise RuntimeError("Node value mismatch between " + json.dumps(tmp_node) + " and " + json.dumps(tmp_node2))
            return existing_node.get('id')
        else:
            new_node = {"id": self.nodeCounter,
                        "n": node_name,
                        "r": represent,
                        "attr": attributes}

            self.nodeCounter += 1
            self.nodeAttrCounter += len(attributes.keys())
            self.nodeTable[external_id] = new_node
            self.newNodes.append(new_node)
            return new_node["id"]

    def _create_attr_obj(self, node_or_edge_plan, row):
        """
        Create attribute object
        :param node_or_edge_plan: node or edge plan in the loading plan
        :param row: current row to be parsed
        :return:
        """
        attr = {}
        if node_or_edge_plan.get('property_columns'):
            for column_raw_temp in node_or_edge_plan['property_columns']:
                if isinstance(column_raw_temp, dict):
                    column_raw = column_raw_temp
                else:
                    if '::' in column_raw_temp:
                        column_split = column_raw_temp.split('::')
                        if len(column_split) > 1:
                            column_raw = {
                                'column_name': column_split[0],
                                'attribute_name': column_split[0],
                                'data_type': column_split[1]
                            }
                        else:
                            column_raw = {
                                'column_name': column_raw_temp,
                                'attribute_name': column_raw_temp
                            }
                    else:
                        column_raw = {
                            'column_name': column_raw_temp,
                            'attribute_name': column_raw_temp
                        }

                if not column_raw.get('data_type'):   # set the default datatype to string
                    column_raw['data_type'] = 'string'

                if not column_raw.get('attribute_name'):  # set the attribute name if it is not defined.
                    column_raw['attribute_name'] = column_raw.get('column_name')

                # type_temp = column_raw.get('data_type')
                value = None

                # this allows us to add arbitary attributes to all source or target nodes
                if column_raw.get('column_name'):
                    value = row.get(column_raw['column_name'])

                if (value is None) and column_raw.get('default_value'):
                    value = column_raw['default_value']

                if value:
                    if column_raw.get('delimiter'):
                        value = value.split(column_raw.get('delimiter'))
                        value = [entry.strip() for entry in value]
                        value = self._data_to_type(value, column_raw['data_type'])
                        # if not type_temp.startswith('list'):
                        #    type_temp = 'list_of_' + type_temp

                        if column_raw.get('value_prefix'):
                            value_list_temp = []
                            for value_item in value:
                                value_temp = column_raw.get('value_prefix') + ":" + str(value_item)
                                value_list_temp.append(value_temp)
                            value = value_list_temp
                    else:
                        value = self._data_to_type(value, column_raw['data_type'])
                        if value is None:
                            return ''

                        if column_raw.get('value_prefix'):
                            value = column_raw.get('value_prefix') + ":" + str(value)

                    attrname = column_raw['attribute_name'] if column_raw.get('attribute_name') \
                        else column_raw['column_name']
                    tmp_attr = {"n": attrname, "v": value}
                    if column_raw['data_type'] != 'string':
                        tmp_attr['d'] = column_raw['data_type']
                    attr[attrname] = tmp_attr

        return attr

    def _data_to_type(self, data, data_type):
        return_data = None

        if type(data) is str:
            data = data.replace('[', '').replace(']', '')
            if 'list_of' in data_type:
                data = data.split(',')

        if data_type == "boolean":
            if type(data) is str:
                return_data = data.lower() == 'true'
            else:
                return_data = bool(data)
        elif data_type == "double" or data_type == "float":
            return_data = float(data)
        elif data_type == "long" or data_type == "integer":
            return_data = int(data)
        elif data_type == "string":
            return_data = str(data)
        elif data_type == "list_of_boolean":
            # Assumption: if the first element is a string then so are the rest...
            if type(data[0]) is str:
                return_data = [s.lower() == 'true' for s in data]
            else:
                return_data = [bool(s) for s in data]
        elif data_type == "list_of_double" or data_type == "list_of_float":
            return_data = [float(s) for s in data]
        elif data_type == "list_of_long" or data_type == "list_of_integer":
            return_data = [int(s) for s in data]
        elif data_type == "list_of_string":
            return_data = [str(s) for s in data]
        else:
            return None

        return return_data

    def _create_edge(self, src_node_id, tgt_node_id, row):
        predicate_str = None
        edge_plan = self._plan.get('edge_plan')
        if edge_plan.get('predicate_id_column'):
            predicate_str = row[edge_plan['predicate_id_column']]

        if not predicate_str and edge_plan.get('default_predicate'):
            predicate_str = edge_plan['default_predicate']

        if not predicate_str:
            raise RuntimeError("Value for predicate string is not found in this row.")
        if edge_plan.get("predicate_prefix"):
            predicate_str = edge_plan['predicate_prefix'] + ":" + predicate_str

        attr = self._create_attr_obj(edge_plan, row)
        new_edge = {"id": self.edgeCounter, "s": src_node_id, "t": tgt_node_id, "i": predicate_str, "attr": attr}
        self.edgeCounter += 1

        self.newEdges.append(new_edge)
        self.edgeAttrCounter += len(attr.keys())

        if len(self.newEdges) >= self.batchsize:
            self._print_batch()

    def _print_batch(self):

        # print new nodes:
        new_nodes = []
        newnode_attrs = []
        for n in self.newNodes:
            new_n = {"@id": n["id"]}
            if n.get("n"):
                new_n['n'] = n.get("n")
            if n.get("r"):
                new_n["r"] = n.get("r")
            new_nodes.append(new_n)
            if n.get("attr"):
                for key, value in n.get("attr").items():
                    tmp_value = value.copy()
                    tmp_value['po'] = n["id"]
                    newnode_attrs.append(tmp_value)

        if new_nodes:
            self.cxWriter.write_aspect_fragment({"nodes": new_nodes})
        if newnode_attrs:
            self.cxWriter.write_aspect_fragment({"nodeAttributes": newnode_attrs})

        # clear the buffer
        self.newNodes.clear()

        # print edges and their attributes
        new_edges = []
        new_edge_attrs = []
        for e in self.newEdges:
            new_e = {'@id': e.get('id'), "s": e.get('s'), "t": e.get('t')}
            if e.get("i"):
                new_e['i'] = e.get("i")
                new_edges.append(new_e)
            if e.get("attr"):
                for key, value in e.get("attr").items():
                    value["po"] = e.get("id")
                    new_edge_attrs.append(value)

        if new_edges:
            self.cxWriter.write_aspect_fragment({"edges": new_edges})

        if new_edge_attrs:
            self.cxWriter.write_aspect_fragment({"edgeAttributes": new_edge_attrs})

        self.newEdges.clear()
