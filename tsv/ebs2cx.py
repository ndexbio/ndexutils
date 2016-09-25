import csv
import ndex.networkn as networkn

def load_ebs_file(filename):
    edge_table = []
    node_table = []
    ebs = {"edge_table":edge_table, "node_table": node_table}

    with open(filename, 'rU') as f:
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

def ebs_to_network(ebs):
    G = networkn.NdexGraph()
    G.set_name("test")
    node_id_map = {}
    # Create Nodes
    # PARTICIPANT	PARTICIPANT_TYPE	PARTICIPANT_NAME	UNIFICATION_XREF	RELATIONSHIP_XREF
    for node in ebs.get("node_table"):
        attributes = {}
        participant = node.get("PARTICIPANT")
        aliases = node.get("UNIFICATION_XREF")
        if aliases is not None and aliases is not "":
            attributes["aliases"] = aliases.split(",")

        node_id = G.add_new_node(participant, attributes)
        node_id_map[participant] = node_id

    # Create Edges
    # PARTICIPANT_A	INTERACTION_TYPE	PARTICIPANT_B	INTERACTION_DATA_SOURCE	INTERACTION_PUBMED_ID	PATHWAY_NAMES	MEDIATOR_IDS
    for edge in ebs.get("edge_table"):
        attributes = {}
        pmid = edge.get("INTERACTION_PUBMED_ID")
        if pmid is not None and pmid is not "":
            attributes["pubmed"] = pmid
        source_node_id = node_id_map.get(edge.get("PARTICIPANT_A"))
        target_node_id = node_id_map.get(edge.get("PARTICIPANT_B"))
        G.add_edge_between(source_node_id, target_node_id, interaction=edge.get("INTERACTION_TYPE"), attr_dict=attributes)

    return G

