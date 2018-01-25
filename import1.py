__author__ = 'aarongary'
import tsv.delim2cx as d2c
import jsonschema
import os
import json
import pandas as pd

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'
path_this = os.path.dirname(os.path.abspath(__file__))
try:
    path_to_load_plan = os.path.join(path_this, 'tsv', 'test', 'signor_load_plan.json')
    load_plan = None
    with open(path_to_load_plan, 'rU') as lp:
        load_plan = json.load(lp)

    path_to_network = os.path.join(path_this, 'tsv', 'signor2.txt')
    with open(path_to_network, 'rU') as tsvfile:
        header = [h.strip() for h in tsvfile.readline().split('\t')]

        df = pd.read_csv(tsvfile, dtype=str, na_filter=False, delimiter='\t', engine='python', names=header)

        rename = {}
        for column_name in df.columns:
            rename[column_name] = column_name.upper()
        df_upper = df.rename(columns=rename)

        loaded_signor = d2c.convert_pandas_to_nice_cx_with_load_plan(df_upper, load_plan, max_rows=15,
                                            name='SIGNOR - TEST LOAD', description='SIGNOR - TEST LOAD')

        merge_plan = [
            {
                "attribute1": "TYPEA",
                "attribute2": "TYPEB",
                "new_attribute": "TYPE"
            }
        ]

        for merge_spec in merge_plan:
            loaded_signor.merge_node_attributes(
                merge_spec.get("attribute1"),
                merge_spec.get("attribute2"),
                merge_spec.get("new_attribute"))

        loaded_signor.upload_to(upload_server, upload_username, upload_password)

        print(loaded_signor.get_summary())

    #import_plan = d2c.TSVLoadingPlan('importme.json')

    #tsv_converter = d2c.TSV2CXConverter(import_plan)

    #G = tsv_converter.convert_tsv_to_cx('importme.txt', name='importme', description='importme desc')

    #print G.to_cx()

except jsonschema.ValidationError as e1:
    print "Failed to parse the loading plan: " + e1.message
    print 'at path: ' + str(e1.absolute_path)
    print "in block: "
    print e1.instance

