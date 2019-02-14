# -*- coding: utf-8 -*-

import os
import re
import requests
import argparse
import logging
import json
import time
import pandas as pd
import csv

import ndexutil.tsv.tsv2nicecx2 as t2n

from ndex2.client import Ndex2
from ndexutil.config import NDExUtilConfig
from ndexutil.exceptions import NDExUtilError

# create logger
logger = logging.getLogger(__name__)


def get_argument_parser(subparsers):
    """
    Adds parameters for argparse to process for ncipid
    :param subparsers:
    :return:
    """
    desc = """
         This tool loads ncipid content into NDEx using sif
         files passed to this tool. The sif files can be
         are found in NCI_PID_EXTENDED_BINARY_SIF_2016-06-09-PC2v8 API
         on the NDEx ftp server
         
         To connect to NDEx server a configuration file must be passed
         into --conf parameter. If --conf is unset the configuration 
         the path ~/{confname} is examined. 
         
         The configuration file should be formatted as follows:
         
         [<value in --profile (default ncipid)>]
         
         {user} = <NDEx username>
         {password} = <NDEx password>
         {server} = <NDEx server(omit http) ie public.ndexbio.org>
         {style} = <NDEx UUID of network to use for styling networks created>
         
         Example:
         
         [ncipid_dev]
         
         {user} = joe123
         {password} = somepassword123
         {server} = dev.ndexbio.org
         {style} = 86f63bf8-1b48-11e9-a05d-525400c25d22
         
    """.format(confname=NDExUtilConfig.CONFIG_FILE,
               user=NDExUtilConfig.USER,
               password=NDExUtilConfig.PASSWORD,
               server=NDExUtilConfig.SERVER,
               style=NciPidContentLoader.STYLE)
    help_fm = argparse.RawDescriptionHelpFormatter

    parser = subparsers.add_parser('loadncipid',
                                   help='Uploads NCI PID networks to NDEx',
                                   description=desc,
                                   formatter_class=help_fm)

    parser.add_argument('--profile', help='Profile in configuration '
                                          'file to use to load '
                                          'NDEx credentials (default ncipid)',
                        default='ncipid')
    ncon = NDExUtilConfig()
    parser.add_argument('--conf', help='Path to configuration file to load '
                                       '(default ' +
                                       ncon.get_config_file()+ ')',
                        default=ncon.get_config_file())
    parser.add_argument('--genesymbol', help='Path to gene symbol mapping json file')
    parser.add_argument('--loadplan', help='Load plan json file', required=True)
    parser.add_argument('--networkattribcsv', help='tab delimited file containing'
                                                   'PID Pathway Name, reviewed by, '
                                                   'curated by and revision data'
                                                   'for ncipid networks', required=True)
    parser.add_argument('--releaseversion', help='Sets version network attribute',
                        default='APR-2018')
    parser.add_argument('--singlefile', help='Only process file matching name in'
                                             '<sifdir>',
                        default=None)
    parser.add_argument('sifdir', help='Directory containing .sif files to parse')
    return parser


participant_type_map = {
    'ProteinReference': 'Protein',
    'SmallMoleculeReference': 'SmallMolecule'
}

DIRECTED_INTERACTIONS = ["controls-state-change-of",
                         "controls-transport-of",
                         "controls-phosphorylation-of",
                         "controls-expression-of",
                         "catalysis-precedes",
                         "controls-production-of",
                         "controls-transport-of-chemical",
                         "chemical-affects",
                         "used-to-produce"
                         ]

CONTROL_INTERACTIONS = ["controls-state-change-of",
                        "controls-transport-of",
                        "controls-phosphorylation-of",
                        "controls-expression-of"
                        ]


class NciPidContentLoader(object):
    """
    Loads content from NCI-PID sif files to NDEx
    """
    STYLE = 'style'

    def __init__(self, args):
        """
        Constructor
        """
        self._args = args
        self._user = None
        self._pass = None
        self._server = None
        self._template = None
        self._gene_symbol_map = {}
        self._net_summaries = None
        self._ndex = None
        self._node_mapping = {}
        self._loadplan = None

    def _parse_config(self):
        """
        Parses config
        :return:
        """
        ncon = NDExUtilConfig()
        con = ncon.get_config()
        self._user = con.get(self._args.profile, NDExUtilConfig.USER)
        self._pass = con.get(self._args.profile, NDExUtilConfig.PASSWORD)
        self._server = con.get(self._args.profile, NDExUtilConfig.SERVER)
        self._template = con.get(self._args.profile, NciPidContentLoader.STYLE)

    def _parse_load_plan(self):
        """

        :return:
        """
        with open(self._args.loadplan, 'r') as f:
            self._loadplan = json.load(f)

    def _load_gene_symbol_map(self):
        """
        Loads gene symbol map
        :return:
        """
        if not os.path.isfile(self._args.genesymbol):
            raise NDExUtilError('Gene symbol mapping file ' +
                                str(self._args.genesymbol) +
                                ' does not exist')

        with open(self._args.genesymbol, 'r') as f:
            self._gene_symbol_map = json.load(f)

    def _load_network_summaries_for_user(self):
        """
        Gets a dictionary of all networks for user account
        <network name upper cased> => <NDEx UUID>
        :return: dict
        """
        net_summaries = self._ndex.get_network_summaries_for_user(self._user)
        self._net_summaries = {}
        for nk in net_summaries:
            if nk.get('name') is not None:
                self._net_summaries[nk.get('name').upper()] = nk.get('externalId')

    def _get_network_properties(self, network_id):
        """
        Uh
        :param network_id:
        :return:
        """
        nps = self._ndex.get_network_aspect_as_cx_stream(network_id, 'networkAttributes')

        network_properties = nps.json()
        return_properties = {}
        for net_prop in network_properties:
            return_properties[net_prop.get('n')] = net_prop.get('v')

        return return_properties

    def query_mygene_for_genesymbol(self, gene_client, node, alias_values):
        """
        Given a NiceCXNetwork() node and node_attribute for node
        this function gets a list of uniprot ids from the 'r' aka
        represents field of node and from the 'alias' attribute in
        the node attribute. mygene.querymany(scope='uniprot' is used
        to get gene symbols. If multiple then there is a check for
        identical values, if a descrepancy is found a message is
        logged to error and the first entry is used.
        :param node:
        :param node_attributes:
        :return:
        """
        idlist = []
        if node is not None:
            if 'r' in node:
                if 'uniprot' in node['r']:
                    idlist.append(re.sub('^.*:', '', node['r']))
        for entry in alias_values:
            if 'uniprot' in entry:
                idlist.append(re.sub('^.*:', '', entry))
        res = gene_client.querymany(idlist, scopes='uniprot', fields='symbol', returnall=True)

        symbolset = set()
        logger.debug('res: ' + str(res))
        for entry in res:
            if not 'symbol' in entry:
                continue
            symbolset.add(entry['symbol'])
        if len(symbolset) > 1:
            logger.error('Query ' + str(idlist) + ' returned multiple symbols: ' + str(symbolset) + ' using 1st')
        if len(symbolset) == 0:
            # need to query uniprot then
            for id in idlist:
                resp = requests.get('https://www.uniprot.org/uniprot/' + id + '.txt')
                if resp.status_code is 200:
                    logger.debug('In response')
                    for entry in resp.text.split('\n'):

                        if not entry.startswith('GN'):
                            continue
                        logger.debug('Found matching line: ' + entry)
                        if 'Name=' in entry:
                            subent = re.sub('^.*Name=', '', entry)
                            logger.debug('name in entry' + subent)
                            genesym = re.sub(' +.*', '', subent)
                            logger.debug('genesym: ' + genesym)
                            symbolset.add(genesym)

        logger.debug('All symbols found: ' + str(symbolset))
        return symbolset.pop()

    def _get_uniprot_gene_symbol_mapping(self, network):
        id_list = []

        for k, v in network.get_nodes():
            participant_name = v['n']
            logger.debug('node names: ' + participant_name)
            if participant_name is not None and '_HUMAN' in participant_name and self._gene_symbol_map.get(
                    participant_name) is None:
                id_list.append(participant_name)
        logger.info('Lookup: ' + str(id_list))
        # =================================
        # LOOKUP UNIPROT ID -> GENE SYMBOL
        # =================================
        url = 'https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json?method=db2db&input=uniprot ' \
              'entry name&inputValues=' + ','.join(id_list) + '&outputs=genesymbol&taxonId=9606&format=row'
        logger.debug('look up query: ' + url)
        look_up_req = requests.get(url)
        look_up_json = look_up_req.json()
        if look_up_json is not None:
            for bio_db_item in look_up_json:
                self._gene_symbol_map[bio_db_item.get('InputValue')] = bio_db_item.get('Gene Symbol')
                self._node_mapping[bio_db_item.get('InputValue')] = bio_db_item.get('Gene Symbol')

    def _merge_node_attributes(self, network, source_attribute1,
                               source_attribute2, target_attribute):
        """
        Iterate through every node in 'network' and put the attributes in
        'source_attribute1' or 'source_attribute2' into a new 'target_attribute'
        'source_attribute1' and 'source_attribute2' are removed. This implementation
        is a bit weird cause if both 'source_attribute1' and 'source_attribute2' have
        data then 'source_attribute1' is taken
        :param network:
        :param source_attribute1:
        :param source_attribute2:
        :param target_attribute:
        :return: None
        """
        for node_id, node in network.get_nodes():
            value1 = network.get_node_attribute(node, source_attribute1)
            value2 = network.get_node_attribute(node, source_attribute2)
            merged_value = value1 or value2
            if merged_value:
                network.set_node_attribute(node['@id'], target_attribute, merged_value['v'],
                                           type=merged_value['d'],
                                           overwrite=True)
                network.remove_node_attribute(node, source_attribute1)
                network.remove_node_attribute(node, source_attribute2)
        return None

    def _get_pandas_dataframe(self, file_name):
        """
        Gets pandas data frame from file
        :param file_name:
        :return: tuple (dataframe, node lines list, node fields list)
        """
        path_to_sif = os.path.join(os.path.abspath(self._args.sifdir),
                                   file_name)
        if os.path.getsize(path_to_sif) is 0:
            logger.error('File is empty: ' + path_to_sif)
            return None, None, None

        with open(path_to_sif, 'rU') as f:
            lines = f.readlines()

        mode = "edge"
        edge_lines = []
        edge_rows_tuples = []
        node_rows_tuples = []
        node_lines = []
        edge_fields = []
        node_fields = []
        for index in range(len(lines)):
            line = lines[index]
            if index is 0:
                edge_fields = [h.strip() for h in line.split('\t')]
            elif line == '\n':
                mode = "node_header"
            elif mode is "node_header":
                node_fields = [h.strip() for h in line.split('\t')]
                mode = "node"
            elif mode is "node":
                node_tuple = tuple(line.split('\t'))
                node_rows_tuples.append(node_tuple)
                node_lines.append(line)
            elif mode is "edge":
                edge_tuple = tuple(line.split('\t'))
                edge_rows_tuples.append(edge_tuple)
                edge_lines.append(line)

        df = pd.DataFrame.from_records(edge_rows_tuples, columns=edge_fields)

        df_nodes = pd.DataFrame.from_records(node_rows_tuples, columns=node_fields)

        df_with_a = df.join(df_nodes.set_index('PARTICIPANT'), on='PARTICIPANT_A')

        df_with_a_b = df_with_a.join(df_nodes.set_index('PARTICIPANT'), on='PARTICIPANT_B', lsuffix='_A',
                                     rsuffix='_B')
        df_with_a_b = df_with_a_b.replace('\n', '', regex=True)
        df_with_a_b['PARTICIPANT_A'] = df_with_a_b['PARTICIPANT_A'].map(lambda x: x.lstrip('[').rstrip(']'))
        df_with_a_b['PARTICIPANT_B'] = df_with_a_b['PARTICIPANT_B'].map(lambda x: x.lstrip('[').rstrip(']'))
        return df_with_a_b, node_lines, node_fields

    def _replace_uniprot_with_gene_name_and_set_represents(self, network):
        """

        :param network:
        :return:
        """
        for k, v in network.get_nodes():
            # ==============================================
            # CONVERT NODE NAME FROM UNIPROT TO GENE SYMBOL
            # ==============================================
            logger.debug('Node: ' + str(v))
            participant_name = v['n']
            if '_HUMAN' in participant_name and self._node_mapping.get(participant_name) is not None:
                v['r'] = self._node_mapping.get(participant_name)
            elif len(participant_name) > 25:
                v['r'] = (participant_name.split('/')[0])

            # =============================
            # SET REPRESENTS
            # =============================
            aliases = network.get_node_attribute(v, 'alias')
            if aliases is not None and aliases['v'] != 'null' and len(aliases) > 0:
                logger.debug('Aliases is: ' + str(aliases))
                v['r'] = (aliases['v'][0])
            else:
                v['r'] = v['n']
                if aliases == 'null':
                    network.remove_node_attribute(k, 'alias')

            if aliases is not None and len(aliases) > 1:
                replace_alias = network.get_node_attribute(k, 'alias')
                logger.debug('replace_alias is: ' + str(replace_alias))
                network.set_node_attribute(k, 'alias', aliases['v'][1:], type=replace_alias['d'],
                                           overwrite=True)
            else:
                network.remove_node_attribute(k, 'alias')

            node_type = network.get_node_attribute(k, 'type')
            logger.debug('node_type: ' + str(node_type))
            network.set_node_attribute(k, 'type', participant_type_map.get(node_type['v']),
                                       overwrite=True)

    def _get_edge_type_maps(self, network):
        """
        Iterates through all edges and examines interaction 'i'
        field setting the dictionaries returned as follows.

        If interaction is 'neighbor-of' then neighbor_of map dict is
        set as follows:

        neighbor_of[source node id][target node id] = edge id
        neighbor_of[target node id][source node id] = edge id

        If interaction is 'controls-state-change-of' then controls_state map dict is
        set as follows:

        controls_state[source node id][target node id] = edge id
        controls_state[target node id][source node id] = edge id

        For any other interaction then other_edge is set as follows:

        other_edge[source node id][target node id] = edge id
        other_edge[target node id][source node id] = edge id

        In addition, if interaction is in DIRECTED_INTERACTIONS list
        constant defined in this module then the edge attribute 'directed'
        is set to True otherwise it is set to False

        :param network:
        :return: tuple of dicts (neighbor_of, controls_state, other_edge)
        """
        neighbor_of_map = {}
        controls_state_change_map = {}
        other_edge_exists = {}
        for k, v in network.get_edges():
            s = v['s']
            t = v['t']
            i = v['i']
            if i == 'neighbor-of':
                if not s in neighbor_of_map:
                    neighbor_of_map[s] = {}
                if not t in neighbor_of_map:
                    neighbor_of_map[t] = {}
                neighbor_of_map[s][t] = k
                neighbor_of_map[t][s] = k
            elif i == 'controls-state-change-of':
                if controls_state_change_map.get(s) is None:
                    controls_state_change_map[s] = {}
                if controls_state_change_map.get(t) is None:
                    controls_state_change_map[t] = {}
                controls_state_change_map[s][t] = k
                controls_state_change_map[t][s] = k
            else:
                if not s in other_edge_exists:
                    other_edge_exists[s] = {}
                if not t in other_edge_exists:
                    other_edge_exists[t] = {}
                other_edge_exists[s][t] = True
                other_edge_exists[t][s] = True

            if i in DIRECTED_INTERACTIONS:
                network.set_edge_attribute(k, 'directed', True)
            else:
                network.set_edge_attribute(k, 'directed', False)

        return neighbor_of_map, controls_state_change_map, other_edge_exists

    def _remove_other_edges_in_neighbor_of_edges(self, network,
                                                 neighbor_of_map,
                                                 other_edge_exists):
        """
        Iterate through 'neighbor_of_map' which is a dict of this
        structure which had interactions named 'neighbor-of'

        [source node id][target node id]
                                          => edge id
        [target node id][source node id]

        Then iterate through 'other_edge_exists' which is a dict of
        this structure and had interactions OTHER then 'neighbor-of'
        and 'controls-state-change-of'

        [source node id][target node id]
                                          => edge id
        [target node id][source node id]

        and remove any edges and edge attributes
        that are in 'other_edge_exists'
        :param network:
        :param neighbor_of_map:
        :return:
        """
        n_edges = neighbor_of_map.items()
        for s, ti in n_edges:
            inner_neighbor = ti.items()
            for t, i in inner_neighbor:
                if other_edge_exists.get(s) is not None:
                    if other_edge_exists[s].get(t) is not None:
                        network.remove_edge(i)
                        # remove edge attributes for deleted edge
                        net_attrs = network.get_edge_attributes(i)
                        for net_attr in net_attrs:
                            network.remove_edge_attribute(i, net_attr['n'])

    def _remove_other_edges_in_controls_state_of_edges(self,
                                                       network,
                                                       controls_state_change_map,
                                                       other_edge_exists):
        """
        Iterate through 'controls_state_change_map' which is a dict of this
        structure which had interactions named 'controls-state-change-of'

        [source node id][target node id]
                                          => edge id
        [target node id][source node id]

        Then iterate through 'other_edge_exists' which is a dict of
        this structure and had interactions OTHER then 'neighbor-of'
        and 'controls-state-change-of'

        [source node id][target node id]
                                          => edge id
        [target node id][source node id]

        and remove any edges and edge attributes
        that are in 'other_edge_exists'
        :param network:
        :param controls_state_change_map:
        :param other_edge_exists:
        :return:
        """
        n_edges = controls_state_change_map.items()
        for s, ti in n_edges:
            inner_neighbor = ti.items()
            for t, i in inner_neighbor:
                if other_edge_exists.get(s) is not None:
                    if other_edge_exists[s].get(t) is not None:
                        network.remove_edge(i)
                        # remove edge attributes for deleted edge
                        net_attrs = network.get_edge_attributes(i)
                        for net_attr in net_attrs:
                            network.remove_edge_attribute(i, net_attr['n'])

    def _set_alias_and_represents(self, network, node_to_update,
                                  node_info):
        """

        :return:
        """
        unification_xref = node_info.get('UNIFICATION_XREF')
        if unification_xref is not None and len(unification_xref) > 0:
            unification_xref_array_tmp = unification_xref.split(';')
            unification = unification_xref_array_tmp[0]
            unification_xref_array = []
            for uxr in unification_xref_array_tmp:
                if uxr.upper().count('CHEBI') > 1:
                    unification_xref_array.append(uxr.replace('chebi:', '', 1))

            if len(unification_xref_array) < 1:
                if len(unification_xref_array_tmp) > 1:
                    unification_xref_array_tmp = unification_xref_array_tmp[1:]
                    network.set_node_attribute(node_to_update['@id'], 'alias', unification_xref_array_tmp,
                                               type='list_of_string',
                                               overwrite=True)
                elif len(unification_xref_array_tmp) == 1:
                    network.remove_node_attribute(node_to_update['@id'], 'alias')
                else:
                    network.set_node_attribute(node_to_update['@id'], 'alias', unification_xref_array_tmp,
                                               type='list_of_string',
                                               overwrite=True)
            else:
                if len(unification_xref_array) > 1:
                    unification_xref_array = unification_xref_array[1:]
                    network.set_node_attribute(node_to_update['@id'], 'alias', unification_xref_array,
                                               type='list_of_string',
                                               overwrite=True)
                else:
                    network.remove_node_attribute(node_to_update['@id'], 'alias')

        else:
            unification = node_info.get('PARTICIPANT').lstrip('[').rstrip(']')
        node_to_update['r'] = unification.replace('chebi:', '', 1)

    def _update_node_name_with_gene_symbol(self, node_to_update, participant_name):
        """

        :param node_to_update:
        :param participant_name:
        :return:
        """
        if participant_name is not None and '_HUMAN' in participant_name and self._gene_symbol_map.get(
                participant_name) is not None:
            gene_symbol_mapped_name = self._gene_symbol_map.get(participant_name)
            if len(gene_symbol_mapped_name) > 25:
                clean_symbol = gene_symbol_mapped_name.split('/')[0]
            else:
                clean_symbol = self._gene_symbol_map.get(participant_name)
            if len(clean_symbol) == 0 or clean_symbol == '-':
                logger.debug('Mapping came back with -. Going with old name: ' + node_to_update['n'])
            else:
                logger.debug('Updating node from name: ' + node_to_update['n'] + ' to ' + clean_symbol)
                node_to_update['n'] = clean_symbol

    def _update_node_name_if_chebi_and_get_participant_name(self, node_to_update, node_info):
        """

        :param node_to_update:
        :param node_info:
        :return:
        """
        participant_name = node_info.get('PARTICIPANT_NAME')
        if participant_name is not None:
            participant_name = participant_name.lstrip('[').rstrip(']')
        if node_to_update['n'].startswith("CHEBI") and participant_name:
            if participant_name is not None:
                node_to_update['n'] = participant_name
        return participant_name

    def _process_sif(self, file_name):
        """
        Processes sif file
        :param file_name:
        :return:
        """
        node_table = []

        df, node_lines, node_fields = self._get_pandas_dataframe(file_name)
        if df is None:
            return
        network = t2n.convert_pandas_to_nice_cx_with_load_plan(df, self._loadplan)

        network.set_name(file_name.replace('.sif', ''))

        # merge node attributes, logic was removed ndex2 python client so call a local implementation
        self._merge_node_attributes(network, 'alias_a', 'alias_b', 'alias')
        self._merge_node_attributes(network, 'PARTICIPANT_TYPE_A', 'PARTICIPANT_TYPE_B', 'type')

        self._get_uniprot_gene_symbol_mapping(network)

        self._replace_uniprot_with_gene_name_and_set_represents(network)

        (neighbor_of_map, controls_state_change_map,
         other_edge_exists) = self._get_edge_type_maps(network)

        self._remove_other_edges_in_neighbor_of_edges(network, neighbor_of_map,
                                                      other_edge_exists)

        self._remove_other_edges_in_controls_state_of_edges(network,
                                                            controls_state_change_map,
                                                            other_edge_exists)

        node_reader = csv.DictReader(node_lines, fieldnames=node_fields, dialect='excel-tab')
        for dict in node_reader:
            node_table.append(dict)

        # =======================
        # PROCESS NODES
        # =======================
        for node_info in node_table:
            node_to_update = network.get_node_by_name(node_info.get('PARTICIPANT').lstrip('[').rstrip(']'))

            participant_name = self._update_node_name_if_chebi_and_get_participant_name(node_to_update,
                                                                                        node_info)

            self._set_alias_and_represents(network, node_to_update, node_info)

            self._update_node_name_with_gene_symbol(node_to_update, participant_name)

            network.set_node_attribute(node_to_update['@id'], 'type',
                                       participant_type_map.get(node_info.get('PARTICIPANT_TYPE')),
                                       type='string',
                                       overwrite=True)

        # ebs_network = NdexGraph(cx=network.to_cx())

        # layouts.apply_directed_flow_layout(ebs_network, node_width=25, use_degree_edge_weights=True, iterations=200)

        # ebs_network.subnetwork_id = 1
        # ebs_network.view_id = 1

        network_update_key = self._net_summaries.get(network.get_name().upper())

        network.apply_template(self._server, self._template,
                               username=self._user, password=self._pass)

        self._set_version_in_network_attributes(network_update_key, network)
        if network_update_key is not None:
            # this is a bit weird, if its a new network then the version wont be
            # set
            self._set_version_in_network_attributes(network_update_key, network)

            return network.update_to(network_update_key, self._server, self._user, self._pass,
                                     user_agent=self._get_user_agent())
        else:
            upload_message = network.upload_to(self._server, self._user,
                                               self._pass,
                                               user_agent=self._get_user_agent())
            time.sleep(1)
            return upload_message

    def _set_version_in_network_attributes(self, network_update_key, network):
        """
        :param network_update_key:
        :param network:
        :return:
        """
        network_properties = self._get_network_properties(network_update_key)
        for k, v in network_properties.items():
            if k.upper() == 'VERSION':
                network.set_network_attribute('version', self._args.releaseversion)
            else:
                network.set_network_attribute(k, v)

    def _get_user_agent(self):
        """

        :return:
        """
        return 'ncipid/' + self._args.version
    def _create_ndex_connection(self):
        """
        creates connection to ndex
        :return:
        """
        if self._ndex is None:
            self._ndex = Ndex2(host=self._server, username=self._user,
                               password=self._pass, user_agent=self._get_user_agent())

    def run(self):
        """
        Runs content loader
        :return:
        """
        self._parse_config()
        self._create_ndex_connection()
        logger.debug('Parsed config: ' + self._user)
        self._load_gene_symbol_map()
        self._load_network_summaries_for_user()
        self._parse_load_plan()

        file_reverse = sorted(os.listdir(self._args.sifdir),
                              key=lambda s: s.lower(), reverse=True)

        for file in file_reverse:  # listdir(path_to_sif_files):
            # if 'PathwayCommons.8.NCI_PID.BIOPAX.sif' in file:
            # if not file.startswith('Visual signal transduction Rods.sif'):
            #    continue
            if self._args.singlefile is not None:
                if self._args.singlefile != os.path.basename(file):
                    continue

            if file.endswith(".sif"):
                logger.debug('Processing ' + file)
                self._process_sif(file)

        return 0