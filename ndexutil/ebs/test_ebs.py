# /Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937/a4b7 Integrin signaling.sif

import ebs2cx
import sys
from . import temp_append_path
sys.path.insert(1, temp_append_path)

import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox

# - aliases in correct form
# - represents
# - gene
# - node type
# - nicer cytoscape style template
# - cravat group
# - (tested) filter orphans
# - load-ndexebs directory host group username password
# - generate description

#file = "/Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937/a4b7 Integrin signaling.sif"

#file = "/Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937/Wnt signaling network.sif"

file = "/Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-05-05T16:11:41.157145/p53 pathway.sif"


ebs = ebs2cx.load_ebs_file_to_dict(file)

network = ebs2cx.ebs_to_network(ebs)

layouts.apply_directed_flow_layout(network)

toolbox.apply_template(network, "72f9837f-7d27-11e6-b0a6-06603eb7f303", username="drh", password="drh")

network.write_to("/Users/dexter/" + network.get_name() + ".cx")

network.upload_to("http://dev.ndexbio.org", "drh", "drh")