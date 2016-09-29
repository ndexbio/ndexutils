import csv
import ndex.networkn as networkn
from os import listdir, makedirs
from os.path import isfile, isdir, join, abspath, dirname, exists, basename, splitext
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox

def upload_ebs_files(dirpath, ndex, groupname=None, template_network=None, layout=None):
    network_id_map={}
    for filename in listdir(dirpath):
        path = join(dirpath, filename)
        network_name = basename(path)
        ebs_network = load_ebs_file_to_network(path)
        if layout:
            if layout.get("name") is "causal_flow":
                layouts.apply_directed_flow_layout(ebs_network, directed_edge_types=layout.get("directed_edge_types"))
        if template_network:
            toolbox.apply_network_as_template(template_network)

        network_id =ndex.save_cx_stream_as_new_network(self.to_cx_stream())
        network_id_map[network_name]=network_id
    if groupname:
        ndex.grant_networks_to_group(groupname, network_id_map.values())
    return network_id_map


def load_ebs_file_to_network(path):
    edge_table = []
    node_table = []
    ebs = {"edge_table":edge_table, "node_table": node_table}
    network_name = path

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


# Name	                            Description
# controls-state-change-of	        First protein controls a reaction that changes the state of the second protein.
# controls-transport-of	            First protein controls a reaction that changes the cellular location of the second protein.
# controls-phosphorylation-of	    First protein controls a reaction that changes the phosphorylation status of the second protein.
# controls-expression-of	        First protein controls a conversion or a template reaction that changes expression of the second protein.
# catalysis-precedes	            First protein controls a reaction whose output molecule is input to another reaction controled by the second protein.
# in-complex-with	                Proteins are members of the same complex.
# interacts-with	                Proteins are participants of the same MolecularInteraction.
# neighbor-of	                    Proteins are participants or controlers of the same interaction.
# consumption-controled-by	        The small molecule is consumed by a reaction that is controled by a protein
# controls-production-of	        The protein controls a reaction of which the small molecule is an output.
# controls-transport-of-chemical	The protein controls a reaction that changes cellular location of the small molecule.
# chemical-affects	                A small molecule has an effect on the protein state.
# reacts-with	                    Small molecules are input to a biochemical reaction.
# used-to-produce	                A reaction consumes a small molecule to produce another small molecule.
def _is_causal(rel):
    if rel in ["controls-state-change-of",
                "controls-transport-of",
                "controls-phosphorylation-of",
                "controls-expression-of",
                "catalysis-precedes",
                "in-complex-with",
                "controls-production-of",
                "controls-transport-of-chemical",
                "chemical-affects",
                "used-to-produce",
               ]:
        return True
    return False


def _is_filtered(rel, filter_list=["neighbor-of", "interacts-with", "controls-state-change-of"]):
    if rel in filter_list:
        return True
    return False

def _get_node_type(ebs_type):
    if ebs_type is None:
        return "Other"
    if ebs_type in ["SmallMolecule", "SmallMoleculeReference"]:
        return "SmallMolecule"
    if ebs_type in ["Complex","ComplexAssembly"]:
        return "Complex"
    if ebs_type in ["Protein","ProteinReference"]:
        return "Protein"
    if ebs_type in ["Rna","RnaReference"]:
        return "Rna"
    return "Other"

def ebs_to_network(ebs, remove_orphan_nodes=True):
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

        attributes["type"] = _get_node_type(node.get("PARTICIPANT_TYPE"))

        node_id = G.add_new_node(participant, attributes)
        node_id_map[participant] = node_id

    # Create Edges
    # PARTICIPANT_A	INTERACTION_TYPE	PARTICIPANT_B	INTERACTION_DATA_SOURCE	INTERACTION_PUBMED_ID	PATHWAY_NAMES	MEDIATOR_IDS
    for edge in ebs.get("edge_table"):
        interaction = edge.get("INTERACTION_TYPE")
        if _is_filtered(interaction):
            continue
        attributes = {}
        attributes["causal"] = _is_causal(interaction)

        pmid = edge.get("INTERACTION_PUBMED_ID")
        if pmid is not None and pmid is not "":
            attributes["pubmed"] = pmid
        source_node_id = node_id_map.get(edge.get("PARTICIPANT_A"))
        target_node_id = node_id_map.get(edge.get("PARTICIPANT_B"))
        G.add_edge_between(source_node_id, target_node_id, interaction=interaction, attr_dict=attributes)

    if remove_orphan_nodes:
        G.remove_orphans()
    return G

