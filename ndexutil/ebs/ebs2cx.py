

import logging
import csv
from os import listdir
from os.path import isfile, join, abspath, dirname, basename, splitext
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox
from ndex.networkn import NdexGraph
import networkx as nx
import mygene
import json

logger = logging.getLogger(__name__)


NDEX_SIF_INTERACTIONS = ["controls-state-change-of",
                         # First protein controls a reaction that changes the state of the second protein.

                         "controls-transport-of",
                         # First protein controls a reaction that changes the cellular location of the second protein.

                         "controls-phosphorylation-of"  # First protein controls a reaction that changes the phosphorylation status of the second protein.

                         "controls-expression-of",
                         # First protein controls a conversion or a template reaction that changes expression of the second protein.

                         "catalysis-precedes",
                         # First protein controls a reaction whose output molecule is input to another reaction controled by the second protein.

                         "in-complex-with",  # Proteins are members of the same complex.

                         "interacts-with",  # Proteins are participants of the same MolecularInteraction.

                         "neighbor-of",  # Proteins are participants or controlers of the same interaction.

                         "consumption-controled-by",
                         # The small molecule is consumed by a reaction that is controled by a protein

                         "controls-production-of",
                         # The protein controls a reaction of which the small molecule is an output.

                         "controls-transport-of-chemical"  # The protein controls a reaction that changes cellular location of the small molecule.

                         "chemical-affects",  # A small molecule has an effect on the protein state.

                         "reacts-with",  # Small molecules are input to a biochemical reaction.

                         "used-to-produce"  # A reaction consumes a small molecule to produce another small molecule.
                         ]

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

current_directory = dirname(abspath(__file__))
def get_json_from_file(file_path):
    if(isfile(file_path)):
        c_file = open(file_path, "r")
        c_data = json.load(c_file)
        c_file.close()
        return c_data
    else:
        return None

gene_symbol_mapping = get_json_from_file(join(current_directory, 'gene_symbol_mapping.json'))


def upload_ebs_files(dirpath, ndex, group_id=None, template_network=None, layout=None,
                     update=False, filter=None, max=None, nci_table=None):
    my_layout = _check_layout_(layout)
    my_filter = _check_filter_(filter)
    my_template_network = _check_template_network_(template_network)
    network_id_map = {}
    network_count = 0
    if max is not None:
        logger.info("max files: " + str(max))

    in_dir = []
    in_nci_table = []
    not_in_nci_table = []
    if nci_table:
        for row in nci_table:
            if "Pathway Name" in row:
                in_nci_table.append(row["Pathway Name"])
                #
                # if "Corrected Pathway Name" in row:
                #     in_nci_table.append(row["Corrected Pathway Name"])

    skipped = []
    account_network_map = search_for_non_biopax_networks(ndex)
    files = []
    file_network_names = []
    for file in listdir(dirpath):
        if file.endswith(".sif"):
            files.append(file)
            network_name = network_name_from_path(file)
            file_network_names.append(network_name)

    logger.info(str(len(files)) + 'SIF files to load')
    logger.info(str(len(account_network_map)) + 'Non-Biopax Networks in the account')

    account_networks = account_network_map.keys()
    account_not_file = list(set(account_networks).difference(set(file_network_names)))

    logger.info("%s Networks in the account not in upload files" % (len(account_not_file)))
    for network_name in account_not_file:
        logger.info(" - %s" % (network_name))

    for filename in files:
        network_count = network_count + 1
        if max is not None and network_count > max:
            break

        logger.info("loading ndexebs file #" + str(network_count) + ": " + filename)
        path = join(dirpath, filename)
        network_name = network_name_from_path(path)
        in_dir.append(network_name)

        matching_networks = account_network_map.get(network_name)
        matching_network_count = 0
        if matching_networks and update:
            matching_network_count = len(matching_networks)
            if matching_network_count > 1:
                logger.info("skipping this file because %s existing networks match '%s'" % (len(matching_networks), network_name))
                skipped.append(network_name  + " :duplicate names")
                continue

        ebs = load_ebs_file_to_dict(path)

        if len(ebs) == 0:
            logger.info("skipping this file because no rows were found when processing it as EBS")
            skipped.append(network_name + " :no rows in file")
            continue

        ebs_network = ebs_to_network(ebs, name=network_name)

        if len(ebs_network.nodes()) == 0:
            logger.info("skipping this network because no nodes were found when processing it as EBS")
            skipped.append(network_name + " :no nodes in file")
            continue

        # Do this one first to establish subnetwork and view ids from template
        # this is not ideal, but ok for special case of this loader
        if my_template_network:
            toolbox.apply_network_as_template(ebs_network, template_network)
            logger.info("applied graphic style from " + str(template_network.get_name()))

        if my_filter:
            if filter == "cravat_1":
                cravat_edge_filter(ebs_network)
            if filter == "ndex_1":
                ndex_edge_filter(ebs_network)

        if my_layout:
            if layout == "directed_flow":
                layouts.apply_directed_flow_layout(ebs_network,
                                                   node_width=25,
                                                   use_degree_edge_weights=True,
                                                   iterations=200)
                logger.info("applied directed_flow layout")

        provenance_props = [{"name": "dc:title", "value": network_name}]

        if nci_table:
            add_nci_table_properties(ebs_network, network_name, nci_table, not_in_nci_table)

        ebs_network.set_network_attribute("description", NCI_DESCRIPTION_TEMPLATE % network_name)

        ebs_network.set_network_attribute("organism", "human")

        if nci_table:
            ebs_network.set_network_attribute("version", "27-Jul-2015")

        ebs_network.update_provenance("Created by NDEx EBS network converter", entity_props=provenance_props)

        if update:
            if matching_network_count == 0:
                logger.info("saving new network " + network_name)
                network_url = ndex.save_cx_stream_as_new_network(ebs_network.to_cx_stream())
                network_id = network_url.split("/")[-1]

            elif matching_network_count == 1:
                network_to_update = matching_networks[0]
                logger.info("updating network " + network_to_update.get("name") + " with " + network_name)
                network_id = network_to_update.get("externalId")
                ndex.update_cx_network(ebs_network.to_cx_stream(), network_id)

            else:
                raise ValueError("unexpected case: should not try to update when more than one matching network")
        else:
            logger.info("saving new network " + network_name)
            network_url = ndex.save_cx_stream_as_new_network(ebs_network.to_cx_stream())
            network_id = network_url.split("/")[-1]


        network_id_map[network_name] = network_id

    if group_id:
        logger.info("granting networks to group id " + group_id)
        ndex.grant_networks_to_group(group_id, network_id_map.values())

    for network_name in account_network_map:
        networks = account_network_map[network_name]
        if len(networks) > 1:
            logger.info("Skipped %s because of multiple non-BioPAX matches in the account" % (network_name))

    logger.info("-----------------")
    for network_name in skipped:
        logger.info("Skipped %s" % (network_name))

    return network_id_map

def search_for_non_biopax_networks(ndex):
    search_result = ndex.search_networks(search_string="", account_name=ndex.username, size=10000)
    if "networks" in search_result:
        networks_in_account = search_result["networks"]
    else:
        networks_in_account = search_result

    logger.info("%s networks in account %s" % (len(networks_in_account), ndex.username))

    account_non_biopax_network_map = {}
    biopax_network_count = 0
    for network in networks_in_account:
        name = network["name"]
        skip = False
        if "properties" in network:
            for property in network["properties"]:
                property_name = property["predicateString"]
                if property_name == "sourceFormat" or property_name == "ndex:sourceFormat":
                    if property["value"] == "BIOPAX":
                        skip = True
                        biopax_network_count += 1
                        break
        if not skip:
            if name in account_non_biopax_network_map:
                networks = account_non_biopax_network_map[name]
            else:
                networks = []
                account_non_biopax_network_map[name] = networks
            networks.append(network)

    logger.info("%s BioPAX networks in account %s" % (biopax_network_count, ndex.username))
    for name in account_non_biopax_network_map:
        networks = account_non_biopax_network_map[name]
        if len(networks) > 1:
            logger.info("%s duplicate non-biopax networks for %s" % (len(networks), name))
    logger.info("%s non-BioPAX networks in account %s" % (len(account_non_biopax_network_map), ndex.username))

    return account_non_biopax_network_map

def check_upload_account(username, ndex, dirpath, nci_table):
    search_result = ndex.search_networks(search_string="*",  account_name=username, size=10000)

    if "networks" in search_result:
        networks_in_account = search_result["networks"]
    else:
        networks_in_account = search_result

    account_sif_networks = []
    account_sif_names = []
    for network in networks_in_account:
        if "properties" in network:
            for property in network["properties"]:
                property_name = property["predicateString"]
                if property_name == "sourceFormat" or property_name == "ndex:sourceFormat":
                    if property["value"] != "BIOPAX":
                        account_sif_networks.append(network)
                        account_sif_names.append(network.get("name"))
                        break

    logger.info("%s non-BioPAX networks in account %s" % (len(account_sif_names), username))

    upload_names = []
    for path in listdir(dirpath):
        upload_names.append(network_name_from_path(path))
    logger.info("%s networks to upload / update" % (len(upload_names)))

    # Raise an exception if any of the upload_names are in the account_sif_names multiple times

    nci_names = []
    nci_corrected_names = []

    original_to_corrected_map = {}
    for row in nci_table:
        original_name = None
        if "Pathway Name" in row:
            original_name = row["Pathway Name"]
            nci_names.append(original_name)
        if "Corrected Pathway Name" in row:
            c_name = row["Corrected Pathway Name"]
            if c_name != "":
                nci_corrected_names.append(c_name)
                original_to_corrected_map[original_name] = c_name

    logger.info("there are %s NCI networks specified in the NCI table:" % (len(nci_names)))

    all_nci_names = list(set(nci_corrected_names).union(set(nci_names)))

    # case 1: NCI network names NOT in account_sif names:
    nci_not_account_sifs = list(set(nci_names).difference(set(account_sif_names)))
    logger.info("%s NCI networks out of %s are not in the account:" % (len(nci_not_account_sifs), len(nci_names)))
    for name in nci_not_account_sifs:
        logger.info(name)

    # case 1a: Corrected NCI names NOT in account_sif names:
    nci_corrected_not_account_sifs = list(set(nci_corrected_names).difference(set(account_sif_names)))
    logger.info("%s NCI (corrected name) networks out of %s are not in the account:" % (len(nci_corrected_not_account_sifs), len(nci_corrected_names)))
    for name in nci_corrected_not_account_sifs:
        logger.info(name)

    # case 2: NCI network names NOT in upload names:
    nci_original_not_upload = list(set(nci_names).difference(set(upload_names)))
    logger.info("%s NCI original names out of %s are not in the %s upload names:" % (len(nci_original_not_upload), len(nci_names), len(upload_names)))
    for name in nci_original_not_upload:
        logger.info(name)

    # case 2a: Corrected NCI names NOT in upload names:
    nci_corrected_not_upload = list(set(nci_corrected_names).difference(set(upload_names)))
    logger.info("%s NCI (corrected name) networks out of %s are not in the %s upload names:" % (len(nci_corrected_not_upload), len(nci_corrected_names), len(upload_names)))
    for name in nci_corrected_not_upload:
        logger.info(name)

    # case 4: NCI Networks for which neither the original or corrected name is in the upload list
    # case 2: NCI network names NOT in upload names:
    nci_not_upload = []
    for original_name in nci_names:
        if original_name in upload_names:
            continue
        corrected_name = original_to_corrected_map.get(original_name)
        if not corrected_name:
            nci_not_upload.append([original_name])
            continue
        if corrected_name in upload_names:
            continue
        else:
            nci_not_upload.append([original_name, corrected_name])

    logger.info("%s NCI networks from table not in the %s upload names:" % (len(nci_not_upload), len(upload_names)))
    for item in nci_not_upload:
        if len(item) == 1:
            logger.info(item[0])
        else:
            logger.info("%s -> %s" % (item[0], item[1]))


    # case 5: duplicates of upload names in account_sif names:

    # case 6: upload names not matching any NCI names: CREATE
    upload_not_nci = list(set(upload_names).difference(set(all_nci_names)))
    logger.info("%s upload networks out of %s do not match any of the names from the nci table (corrected or original) and therefore will be created :" % (len(upload_not_nci), len(upload_names)))
    for name in upload_not_nci:
        logger.info(name)

    # case 7: upload names matching some NCI name: UPDATE
    upload_and_nci = list(set(upload_names).intersection(set(all_nci_names)))
    logger.info("%s upload networks out of %s that match an nci name (corrected or original) and therefore will be updated):" % (len(upload_and_nci), len(upload_names)))

    # case 8: account non-BioPAX names not matching any upload name
    account_sif_not_upload = list(set(account_sif_names).difference(set(upload_names)))
    logger.info("%s account (non-BioPAX) networks out of %s do not match any of the upload networks :" % (len(account_sif_not_upload), len(account_sif_names)))
    for name in account_sif_not_upload:
        logger.info(name)

    # case 8: upload names not in account (non-BioPAX)  names=
    upload_not_account_sif = list(set(upload_names).difference(set(account_sif_names)))
    logger.info("%s upload networks out of %s do not match any of the account (non-BioPAX)  networks :" % (len(upload_not_account_sif), len(upload_names)))
    for name in upload_not_account_sif:
        logger.info(name)




def network_name_from_path(path):
    base = basename(path)
    split = splitext(base)
    return split[0]


def remove_my_orphans(network):
    before_node_count = nx.number_of_nodes(network)
    network.remove_orphan_nodes()
    after_node_count = nx.number_of_nodes(network)
    delta = before_node_count - after_node_count
    if delta > 0:
        logger.info("removed " + str(delta) + " orphans")


def _check_filter_(the_filter):
    if the_filter is None:
        return False
    elif the_filter in ["cravat_1", "ndex_1"]:
        return the_filter
    else:
        raise "unknown the_filter: " + str(the_filter)


def _check_layout_(layout):
    if layout is None:
        return False
    elif layout in ["directed_flow"]:
        return layout
    else:
        raise "unknown layout" + str(layout)


def _check_template_network_(template):
    if template is None:
        return False
    elif not isinstance(template, NdexGraph):
        raise "template_network is not an NdexGraph: " + str(template)
    else:
        logger.info("style template network: " + str(template.get_name()))
        return template


CRAVAT_FILTER_LIST = ["neighbor-of", "interacts-with", "controls-state-change-of"]


def cravat_edge_filter(network):
    for edge_id in network.edgemap.keys():
        interaction = str(network.get_edge_attribute_value_by_id(edge_id, 'interaction'))
        if interaction in CRAVAT_FILTER_LIST:
            network.remove_edge_by_id(edge_id)

    remove_my_orphans(network)


# Next:
# get pmids for edges in tuple to edge map
# make removal conditional on NOT removing any unique pmids.
# - a neighbor of edge is preserved if it has a pmid that is not associated with any other edge
# - csc edge is preserved if it has a pmid that is not associated any more specific edge
# hmmm... we can abstract this to finding "more specific edges" for each edge that we
# consider pruning.
NDEX_FILTER_SUBSUMPTION = {
    "neighbor-of": ["controls-state-change-of",
                    # First protein controls a reaction that changes the state of the second protein.
                    "controls-transport-of",
                    # First protein controls a reaction that changes the cellular location of the second protein.
                    "controls-phosphorylation-of"  # First protein controls a reaction that changes the phosphorylation status of the second protein.
                    "controls-expression-of",
                    # First protein controls a conversion or a template reaction that changes expression of the second protein.
                    "catalysis-precedes",
                    # First protein controls a reaction whose output molecule is input to another reaction controled by the second protein.
                    "in-complex-with",  # Proteins are members of the same complex.
                    "interacts-with",  # Proteins are participants of the same MolecularInteraction.
                    "consumption-controled-by",
                    # The small molecule is consumed by a reaction that is controled by a protein
                    "controls-production-of",
                    # The protein controls a reaction of which the small molecule is an output.
                    "controls-transport-of-chemical"  # The protein controls a reaction that changes cellular location of the small molecule.
                    "chemical-affects",  # A small molecule has an effect on the protein state.
                    "reacts-with",  # Small molecules are input to a biochemical reaction
                    "used-to-produce"  # A reaction consumes a small molecule to produce another small molecule.
                    ],
    "controls-state-change-of": [
        "controls-transport-of",
        "controls-phosphorylation-of",
        "controls-expression-of"
    ]
}


def ndex_edge_filter(network):
    map = create_tuple_to_edge_map(network)
    remove_subsumed_edges_of_type_in_network("neighbor-of", map, network)
    remove_subsumed_edges_of_type_in_network("controls-state-change-of", map, network)
    # remove_my_orphans(network)
    return True

    # for tuple_key, edges in map.items():
    #     # get the neighbor-of edges
    #     neighbor_of_edge_ids = []
    #     for edge in edges:
    #         if edge["interaction"] == "neighbor-of":
    #             neighbor_of_edge_ids.append = edge["edge_id"]
    #
    #     n_neighbors = len(neighbor_of_edge_ids)
    #
    #     # remove unwanted neighbor-of edges, if any
    #     if n_neighbors < len(edges) and n_neighbors > 0:
    #         if n_neighbors == 1:
    #             # one neighbor-of is the only edge, keep it
    #             continue
    #         else:
    #             # remove all but one
    #             for edge_id in range(1, n_neighbors - 1):
    #                 network.remove_edge_by_id(edge_id)
    #                 logger.info("removing edge " + str(edge_id) + " " + "neighbor-of")
    #             continue
    #
    #     # controls-state-change-of
    #     # if there is both a controls-state-change-of edge and
    #     # controls-phosphorylation-of edge from A to B, then
    #     # remove the controls-phosphorylation-of edge
    #     node_ids = tuple_key.split("_")
    #     node_a = node_ids[0]
    #     node_b = node_ids[1]
    #     csc_a_b = None
    #     csc_b_a = None
    #     cp_a_b = None
    #     cp_b_a = None
    #     for edge in edges:
    #         if edge["interaction"] == "controls-state-change-of":
    #             if edge["source_id"] == node_a:
    #                 csc_a_b = edge["edge_id"]
    #             else:
    #                 csc_b_a = edge["edge_id"]
    #
    #         if edge["interaction"] == "controls-phosphorylation-of":
    #             if edge["source_id"] == node_a:
    #                 cp_a_b = edge["edge_id"]
    #             else:
    #                 cp_b_a = edge["edge_id"]
    #     if csc_a_b and cp_a_b:
    #         network.remove_edge_by_id(csc_a_b)
    #         logger.info("removing edge " + str(csc_a_b) + " " + "controls-state-change-of")
    #     if csc_b_a and cp_b_a:
    #         network.remove_edge_by_id(csc_b_a)
    #         logger.info("removing edge " + str(csc_b_a) + " " + "controls-state-change-of")


def remove_subsumed_edges_of_type_in_network(edge_type, tuple_to_edge_map, network):
    for tuple_key, edges in tuple_to_edge_map.items():
        node_ids = tuple_key.split("_")
        node_a_id = node_ids[0]
        forward_edges = []
        backward_edges = []
        for edge in edges:
            if edge["source_id"] == node_a_id:
                forward_edges.append(edge)
            else:
                backward_edges.append(edge)

        remove_subsumed_edges_of_type(edge_type, forward_edges, network)
        remove_subsumed_edges_of_type(edge_type, backward_edges, network)


def remove_subsumed_edges_of_type(edge_type, edges, network):
    if len(edges) == 0:
        return False

    subsuming_interactions = NDEX_FILTER_SUBSUMPTION.get(edge_type)
    if not subsuming_interactions:
        # this edge type is never subsumed
        return False

    subsuming_edges = []
    subsuming_pmids = []
    edges_to_be_subsumed = []
    for edge in edges:
        if edge["interaction"] == edge_type:
            edges_to_be_subsumed.append(edge)
        if edge["interaction"] in subsuming_interactions:
            subsuming_edges.append(edge)
            if "pmid" in edge:
                for pmid in edge["pmid"]:
                    subsuming_pmids.append(pmid)

    if len(subsuming_edges) == 0 or len(edges_to_be_subsumed) == 0:
        # nobody to be subsumed or nobody to do the subsuming :-)
        return False

    some_edge_removed = False
    for edge in edges_to_be_subsumed:
        if "pmid" in edge:
            # check to be sure that all pmids cited
            # by the "to be subsumed" edges are cited
            # in some subsuming edge to ensure that
            # removal of the edge does not lose information
            for pmid in edge["pmid"]:
                if pmid in subsuming_pmids:
                    network.remove_edge_by_id(edge["edge_id"])
                    logger.info("removing edge " + str(edge["edge_id"]) + " : " + edge_type)
                    some_edge_removed = True
        else:
            # there is no pmid in the subsumed edge,
            # it can therefore be removed without loss of information
            network.remove_edge_by_id(edge["edge_id"])
            logger.info("removing edge " + str(edge["edge_id"]) + " : " + edge_type)
            some_edge_removed = True

    return some_edge_removed


def create_tuple_to_edge_map(network):
    map = {}
    for edge_id in network.edgemap:
        s, t = network.edgemap[edge_id]
        interaction = network.get_edge_attribute_value_by_id(edge_id, "interaction")
        if s > t:
            tuple_key = str(s) + "_" + str(t)
        else:
            tuple_key = str(t) + "_" + str(s)
        if not tuple_key in map:
            map[tuple_key] = [{"edge_id": edge_id, "interaction": interaction, "source_id": s, "target_id": t}]
        else:
            map[tuple_key].append({"edge_id": edge_id, "interaction": interaction, "source_id": s, "target_id": t})
    return map


def load_nci_table_to_dicts(path):
    table = []
    with open(path, 'rU') as f:
        reader = csv.DictReader(f, dialect='excel-tab')
        for row in reader:
            table.append(row)
    return table


def add_nci_table_properties(G, network_name, nci_table, not_in_nci_table):
    # find the entry for network_name in nci_table
    network_dict = None
    for row in nci_table:
        if "Pathway Name" in row:
            if network_name == row["Pathway Name"]:
                # simple match!
                network_dict = row
                break
        if "Corrected Pathway Name" in row:
            if network_name == row["Corrected Pathway Name"]:
                network_dict = row
                break
    if not network_dict:
        not_in_nci_table.append(network_name)
        return

    if "PID" in network_dict:
        pid = network_dict["PID"]
        G.set_network_attribute("labels", pid)

    if "Reviewed By" in network_dict:
        reviewed_by = network_dict["Reviewed By"]
        # names = reviewed_by.split(",")
        # reviewers = []
        # for name in names:
        #     reviewers.append(name.strip())
        # G.set_network_attribute("reviewer", reviewers)
        G.set_network_attribute("reviewers", reviewed_by)

    if "Curated By" in network_dict:
        curated_by = network_dict["Curated By"]
        # names = curated_by.split(",")
        # authors = []
        # for name in names:
        #     authors.append(name.strip())
        # G.set_network_attribute("author", authors)
        G.set_network_attribute("author", curated_by)

    # if "Revision Date" in network_dict:
    #     revision_date = network_dict["Revision Date"]
    #     G.set_network_attribute("revised", revision_date)


def load_ebs_file_to_dict(path):
    edge_table = []
    node_table = []
    ebs = {"edge_table": edge_table, "node_table": node_table}

    with open(path, 'rU') as f:
        lines = f.readlines()
        mode = "edge"
        edge_lines = []
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
                node_lines.append(line)
            elif mode is "edge":
                edge_lines.append(line)

        edge_reader = csv.DictReader(edge_lines, fieldnames=edge_fields, dialect='excel-tab')
        for dict in edge_reader:
            edge_table.append(dict)

        node_reader = csv.DictReader(node_lines, fieldnames=node_fields, dialect='excel-tab')
        for dict in node_reader:
            node_table.append(dict)

    return ebs

def _get_node_type(ebs_type):
    if ebs_type is None:
        return "Other"
    if ebs_type in ["SmallMolecule", "SmallMoleculeReference"]:
        return "SmallMolecule"
    if ebs_type in ["Complex", "ComplexAssembly"]:
        return "Complex"
    if ebs_type in ["Protein", "ProteinReference"]:
        return "Protein"
    if ebs_type in ["Rna", "RnaReference"]:
        return "Rna"
    return "Other"

import requests

def ebs_to_network(ebs, name="not named"):
    G = NdexGraph()
    G.set_name(name)
    node_id_map = {}
    identifier_citation_id_map = {}
    node_mapping = {}
    mg = mygene.MyGeneInfo()

    # Create Nodes
    # PARTICIPANT	PARTICIPANT_TYPE	PARTICIPANT_NAME	UNIFICATION_XREF	RELATIONSHIP_XREF

    id_list = []
    for node in ebs.get("node_table"):
        if "PARTICIPANT" in node:
            participant = node["PARTICIPANT"]
            participant = clean_brackets(participant)
            if participant is not None and '_HUMAN' in participant and node_mapping.get(participant) is None:
                id_list.append(participant)

    url = 'https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json?method=db2db&input=uniprot entry name&inputValues=' + ','.join(id_list) + '&outputs=genesymbol&taxonId=9606&format=row'
    look_up_req = requests.get(url)
    look_up_json = look_up_req.json()
    if look_up_json is not None:
        for bio_db_item in look_up_json:
            gene_symbol_mapping[bio_db_item.get('InputValue')] = bio_db_item.get('Gene Symbol')
            node_mapping[bio_db_item.get('InputValue')] = bio_db_item.get('Gene Symbol')

    for node in ebs.get("node_table"):
        attributes = {}
        if "PARTICIPANT" in node:
            participant = node["PARTICIPANT"]
            participant = clean_brackets(participant)
            participant_symbol = ''
            if participant is not None:
                #participant = participant.replace('_HUMAN', '')

                participant_symbol = gene_symbol_mapping.get(participant)
                #=====================================
                # if the node is not a protien type
                # then skip mygene.info look up
                #=====================================
                if node.get('PARTICIPANT_TYPE') is not None and node.get('PARTICIPANT_TYPE') != 'ProteinReference':
                    participant_symbol = participant

                if participant_symbol is None:
                    participant_symbol = mg.query(participant, species='human')
                    if participant_symbol is not None and participant_symbol.get('hits') is not None and len(participant_symbol.get('hits')) > 0:
                        ph = participant_symbol.get('hits')[0]
                        if 'symbol' in ph:
                            participant_symbol = str(ph.get('symbol'))
                            gene_symbol_mapping[participant] = participant_symbol
                    else:
                        participant_symbol = None

            participant_name = None
            if participant_symbol is not None:
                node_name = participant_symbol
            else:
                node_name = participant

            node_name_tmp = participant

            if "PARTICIPANT_NAME" in node:
                name = node["PARTICIPANT_NAME"]
                if name is not None and len(name) > 0:
                    attributes["name"] = name
                    participant_name = name

            node_type = _get_node_type(node.get("PARTICIPANT_TYPE"))

            if "UNIFICATION_XREF" in node:
                alias_string = node["UNIFICATION_XREF"]
                if alias_string is not None and alias_string is not "":
                    aliases = alias_string.split(";")
                    attributes["alias"] = aliases
                    # attributes["represents"] = alias[0] - can't take first alias for ndexebs.
                    # Need to resolve uniprot primary id for the gene
                    if node_type == "Other":
                        node_type = layouts.aliases_to_node_type(aliases)

            attributes["type"] = node_type

            if node_name_tmp.startswith("CHEBI") and participant_name:
                node_name = participant_name

            # check mygene.info

            #if there is a result use the gene symbol and add the uniprot id as an alias

            node_id = G.add_new_node(node_name, attributes)
            node_id_map[participant] = node_id

    # Create Edges
    # PARTICIPANT_A	INTERACTION_TYPE	PARTICIPANT_B	INTERACTION_DATA_SOURCE
    # INTERACTION_PUBMED_ID	PATHWAY_NAMES	MEDIATOR_IDS
    for edge in ebs.get("edge_table"):
        if "INTERACTION_TYPE" not in edge:
            raise "No interaction type for edge " + str(edge)
        if "PARTICIPANT_A" not in edge:
            raise "No participant A in edge " + str(edge)
        if "PARTICIPANT_B" not in edge:
            raise "No participant B in edge " + str(edge)

        attributes = {}
        interaction = edge["INTERACTION_TYPE"]
        attributes["interaction"] = interaction

        if interaction in DIRECTED_INTERACTIONS:
            attributes["directed"] = True

        # handle pmids as edge attribute
        if "INTERACTION_PUBMED_ID" in edge:
            pmid_string = edge["INTERACTION_PUBMED_ID"]
            if pmid_string is not None and pmid_string is not "":
                pmids = pmid_string.split(";")
                attributes["pmid"] = pmids

        participant_a = clean_brackets(edge["PARTICIPANT_A"])
        participant_b = clean_brackets(edge["PARTICIPANT_B"])
        #if participant_a is not None:
        #    participant_a = participant_a.replace('_HUMAN', '')
        #if participant_b is not None:
        #    participant_b = participant_b.replace('_HUMAN', '')
        source_node_id = node_id_map.get(participant_a)
        target_node_id = node_id_map.get(participant_b)
        edge_id = G.add_edge_between(source_node_id, target_node_id, interaction=interaction, attr_dict=attributes)

        # handle pmids in CX citation and edgeCitation aspect representations in networkn network object
        if "pmid" in attributes:
            prefixed_pmids = []
            for pmid in attributes["pmid"]:
                prefixed_pmids.append("pmid:" + str(pmid))

            for prefixed_pmid in prefixed_pmids:
                if prefixed_pmid not in identifier_citation_id_map:
                    citation_id = G.add_citation(identifier=prefixed_pmid)
                    identifier_citation_id_map[prefixed_pmid] = citation_id

                    G.add_citation_to_edge(edge_id, prefixed_pmid) #add_edge_citation_ref(edge_id, citation_id)
                else:
                    citation_id = identifier_citation_id_map[prefixed_pmid]
                    G.add_citation_to_edge(edge_id, prefixed_pmid) #add_edge_citation_ref(edge_id, citation_id)

    # save gene_symbol_mapping to file (caching)
    with open(join(current_directory, 'gene_symbol_mapping.json'), 'w') as outfile:
        json.dump(gene_symbol_mapping, outfile, indent=4)

    return G

#def get_mygene_info_label():

NCI_DESCRIPTION_TEMPLATE = ("<i>%s</i> was derived from the latest BioPAX3 version of the Pathway Interaction Database (PID)"
                                " curated by NCI/Nature. The BioPAX was first converted to Extended Binary SIF (EBS) by"
                                " the PAXTools v5 utility. It was then processed to remove redundant"
                                " edges, to add a 'directed flow' layout, and to add a graphic style using Cytoscape Visual Properties."
                                " This network can be found in searches using its original PID accession id, present in"
                                " the 'labels' property.")

def clean_brackets(clean_this_string):
    return_this = ''
    if clean_this_string is not None:
        return_this = clean_this_string.replace('[','').replace(']','')
        #if ',' in return_this:
        #    return_this = return_this.split(',')[0].upper()
        return return_this
    else:
        return clean_this_string


def get_my_gene_info(gene_id):
    alt_term_id = []
    if(len(gene_id) > 0):
        r_json = {}
        try:
            url = 'http://mygene.info/v3/query?q=' + gene_id

            r = requests.get(url)
            r_json = r.json()
            if 'hits' in r_json and len(r_json['hits']) > 0:
                for alt_term in r_json['hits']:
                    if(isinstance(alt_term['symbol'], list)):
                        alt_term_id.append(alt_term['symbol'][0].upper())
                    else:
                        alt_term_id.append(alt_term['symbol'].upper())

                #gene_symbol = r_json['hits'][0]['symbol'].upper()
                return alt_term_id
        except Exception as e:
            logger.exception('Caught exception')
            return {'hits': [{'symbol': gene_id, 'entrezgene': '', 'name': 'Entrez results: 0'}]}

        return ["UNKNOWN"]
    else :
        return ["UNKNOWN"]


