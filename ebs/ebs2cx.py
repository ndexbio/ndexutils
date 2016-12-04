import csv
from os import listdir, makedirs
from os.path import isfile, isdir, join, abspath, dirname, exists, basename, splitext
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox
from ndex.networkn import NdexGraph
import networkx as nx

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


def upload_ebs_files(dirpath, ndex, group_id=None, template_network=None, layout=None,
                     update=False, filter=None, max=None, nci_table=None):
    my_layout = _check_layout_(layout)
    my_filter = _check_filter_(filter)
    my_template_network = _check_template_network_(template_network)
    network_id_map = {}
    network_count = 0
    if max is not None:
        print "max files: " + str(max)

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

    for filename in listdir(dirpath):
        network_count = network_count + 1
        if max is not None and network_count > max:
            break

        print ""
        print "loading ebs file #" + str(network_count) + ": " + filename
        path = join(dirpath, filename)
        network_name = network_name_from_path(path)
        in_dir.append(network_name)

        search_result = search_for_matching_networks(ndex, network_name)
        matching_networks = search_result["networks"]
        matching_network_count = search_result["numFound"]

        if update and matching_network_count > 1:
            print "skipping this file because " + str(
                matching_network_count) + "existing networks match '" + network_name + "'"
            continue

        ebs = load_ebs_file_to_dict(path)
        ebs_network = ebs_to_network(ebs, name=network_name)

        # Do this one first to establish subnetwork and view ids from template
        # this is not ideal, but ok for special case of this loader
        if my_template_network:
            toolbox.apply_network_as_template(ebs_network, template_network)
            print "applied graphic style from " + str(template_network.get_name())

        if my_filter:
            if filter == "cravat_1":
                cravat_edge_filter(ebs_network)
            if filter == "ndex_1":
                ndex_edge_filter(ebs_network)

        if my_layout:
            if layout == "directed_flow":
                layouts.apply_directed_flow_layout(ebs_network, node_width=35, use_degree_edge_weights=True)
                print "applied directed_flow layout"

        provenance_props = [{"name": "dc:title", "value": network_name}]

        if nci_table:
            add_nci_table_properties(ebs_network, network_name, nci_table, not_in_nci_table)

        ebs_network.set_network_attribute("dc:description", NCI_DESCRIPTION_TEMPLATE % network_name)

        ebs_network.set_network_attribute("dc:title", network_name)

        if nci_table:
            ebs_network.set_network_attribute("dc:version", "NCI Curated Human Pathways from PID (final); 27-Jul-2015")

        if update:
            if matching_network_count == 0:
                print "saving new network " + network_name
                network_url = ndex.save_cx_stream_as_new_network(ebs_network.to_cx_stream())
                network_id = network_url.split("/")[-1]
                provenance = toolbox.make_provenance("Upload by NDEx EBS network converter",
                                                     network_id,
                                                     ndex,
                                                     entity_props=provenance_props)
                ndex.set_provenance(network_id, provenance)
            elif matching_network_count == 1:
                network_to_update = matching_networks[0]
                print "updating network " + network_to_update.get("name") + " with " + network_name
                network_id = network_to_update.get("externalId")
                old_provenance = ndex.get_provenance(network_id)
                provenance = toolbox.make_provenance("Update by NDEx EBS network converter",
                                                     network_id,
                                                     ndex,
                                                     provenance=old_provenance,
                                                     entity_props=provenance_props)
                ndex.update_cx_network(ebs_network.to_cx_stream(), network_id)
                ndex.set_provenance(network_id, provenance)
            else:
                raise ValueError("unexpected case: should not try to update when more than one matching network")
        else:
            print "saving new network " + network_name
            network_url = ndex.save_cx_stream_as_new_network(ebs_network.to_cx_stream())
            network_id = network_url.split("/")[-1]

            provenance = toolbox.make_provenance("Upload by NDEx EBS network converter",
                                                 network_id,
                                                 ndex,
                                                 entity_props=provenance_props)
            ndex.set_provenance(network_id, provenance)

        network_id_map[network_name] = network_id

    if group_id:
        print "granting networks to group id " + group_id
        ndex.grant_networks_to_group(group_id, network_id_map.values())

    if len(not_in_nci_table) > 0:
        print "Networks in directory not found in NCI table:"
        for name in not_in_nci_table:
            print "   " + name

    if len(in_nci_table) > 0:
        in_table_not_in_dir = list(set(in_nci_table) - set(in_dir))
        if len(in_table_not_in_dir) > 0:
            print "Networks in NCI table not found in directory:"
            for name in not_in_nci_table:
                print "   " + name

    return network_id_map


def search_for_matching_networks(ndex, network_name):
    search_string = 'name:"' + network_name + '"'
    return ndex.search_networks(search_string=search_string, account_name=ndex.username)


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
        print "removed " + str(delta) + " orphans"


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
        print "style template network: " + str(template.get_name())
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
                    "neighbor-of",  # Proteins are participants or controlers of the same interaction.
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
    remove_my_orphans(network)
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
    #                 print "removing edge " + str(edge_id) + " " + "neighbor-of"
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
    #         print "removing edge " + str(csc_a_b) + " " + "controls-state-change-of"
    #     if csc_b_a and cp_b_a:
    #         network.remove_edge_by_id(csc_b_a)
    #         print "removing edge " + str(csc_b_a) + " " + "controls-state-change-of"


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
                    print "removing edge " + str(edge["edge_id"]) + " : " + edge_type
                    some_edge_removed = True
        else:
            # there is no pmid in the subsumed edge,
            # it can therefore be removed without loss of information
            network.remove_edge_by_id(edge["edge_id"])
            print "removing edge " + str(edge["edge_id"]) + " : " + edge_type
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
        #G.set_network_attribute("label", [pid])
        G.set_network_attribute("pid", pid)

    # if "Reviewed By" in network_dict:
    #     reviewed_by = network_dict["Reviewed By"]
    #     names = reviewed_by.split(",")
    #     reviewers = []
    #     for name in names:
    #         reviewers.append(name.strip())
    #     G.set_network_attribute("reviewer", reviewers)
    #
    # if "Curated By" in network_dict:
    #     curated_by = network_dict["Curated By"]
    #     names = curated_by.split(",")
    #     authors = []
    #     for name in names:
    #         authors.append(name.strip())
    #     G.set_network_attribute("author", authors)

    if "Revision Date" in network_dict:
        revision_date = network_dict["Revision Date"]
        G.set_network_attribute("revised", revision_date)


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


def ebs_to_network(ebs, name="not named"):
    G = NdexGraph()
    G.set_name(name)
    node_id_map = {}
    identifier_citation_id_map = {}

    # Create Nodes
    # PARTICIPANT	PARTICIPANT_TYPE	PARTICIPANT_NAME	UNIFICATION_XREF	RELATIONSHIP_XREF
    for node in ebs.get("node_table"):
        attributes = {}
        if "PARTICIPANT" in node:

            if "PARTICIPANT_NAME" in node:
                name = node["PARTICIPANT_NAME"]
                if name is not None and len(name) > 0:
                    attributes["name"] = name

            attributes["type"] = _get_node_type(node.get("PARTICIPANT_TYPE"))
            if "UNIFICATION_XREF" in node:
                alias_string = node["UNIFICATION_XREF"]
                if alias_string is not None and alias_string is not "":
                    attributes["aliases"] = alias_string.split(";")
                    # attributes["represents"] = aliases[0] - can't take first alias for ebs.
                    # Need to resolve uniprot primary id for the gene

            participant = node["PARTICIPANT"]
            node_id = G.add_new_node(participant, attributes)
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

        if interaction in DIRECTED_INTERACTIONS:
            attributes["directed"] = True

        # handle pmids as edge attribute
        if "INTERACTION_PUBMED_ID" in edge:
            pmid_string = edge["INTERACTION_PUBMED_ID"]
            if pmid_string is not None and pmid_string is not "":
                pmids = pmid_string.split(";")
                attributes["pmid"] = pmids

        source_node_id = node_id_map.get(edge["PARTICIPANT_A"])
        target_node_id = node_id_map.get(edge["PARTICIPANT_B"])
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
                    G.add_edge_citation_ref(edge_id, citation_id)
                else:
                    citation_id = identifier_citation_id_map[prefixed_pmid]
                    G.add_edge_citation_ref(edge_id, citation_id)

    return G

NCI_DESCRIPTION_TEMPLATE = ("<i>%s</i> was derived from the latest BioPAX3 version of the Pathway Interaction Database (PID)"
                                " curated by NCI/Nature. The BioPAX was first converted to Extended Binary SIF (EBS) by"
                                " the PAXTools utility from Pathway Commons. It was then processed to remove redundant"
                                " edges, add a 'directed flow' layout, and styled with Cytoscape Visual Properties.")