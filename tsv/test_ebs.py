# /Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937/a4b7 Integrin signaling.sif

import ebs2cx
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox



ebs = ebs2cx.load_ebs_file("/Users/dexter/Projects/ndex-python-utilities/downloads/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937/a4b7 Integrin signaling.sif")

network = ebs2cx.ebs_to_network(ebs)

layouts.apply_directed_flow_layout(network, ['controls-phosphorylation-of', 'controls-transport-of'])

toolbox.apply_template(network, "72f9837f-7d27-11e6-b0a6-06603eb7f303", username="drh", password="drh")

network.write_to("/Users/dexter/" + network.get_name() + ".cx")

network.upload_to("http://dev2.ndexbio.org", "drh", "drh")