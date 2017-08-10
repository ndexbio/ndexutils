#!/usr/local/bin/python

import sys
import argparse
import bottle
import traceback
from bottle import route, default_app, request, redirect, static_file, parse_auth, HTTPResponse, response
import time
import os
import tempfile
import tsv.delim2cx as d2c
import jsonschema
import ndex.beta.toolbox as toolbox
import ndex.beta.layouts as layouts
import ndex.networkn as networkn
import ndex.client as nc
import pymongo
import json
from bson import json_util
import datetime
from time import gmtime, strftime
import requests

mongodb_uri = 'mongodb://localhost'


bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024 *1024

api = default_app()

#log = app.get_logger('api')
current_directory = os.path.dirname(os.path.abspath(__file__))

# default to the network analysis app index page
@bottle.get('/')
def index():
    redirect('/index.html')


# generic API to serve any resource in the static directory
@bottle.get('/<filepath:path>')
def static(filepath):
    print filepath
    print current_directory
    return static_file(filepath, root=os.path.join(current_directory, 'ui'))


@bottle.get('/plans')
def api_plans():
    client = pymongo.MongoClient(mongodb_uri)
    db = client.files

    import_plans = db.import_plans

    found_import_plans = import_plans.find()

    return_this = []
    for found in found_import_plans:
        return_this.append({'import_plan': found.get('import_plan'), 'plan_name': found.get('plan_name')})

    return json.dumps({'results': return_this})

@bottle.get('/templates')
def api_styles():
    #ndex_meta_client = nc.Ndex('http://dev2.ndexbio.org', 'scratch', 'scratch')
    #summaries = ndex_meta_client.search_networks('style', 'scratch',0,500)
    edge_types = {}

    #return_this = []
    #for summary in summaries.get('networks'):
    #    return_this.append({'name': summary.get('name'), 'uuid': summary.get('externalId')})

    #return json.dumps({'results': return_this})
    return json.dumps({"results": [{"name": "style template 1", "uuid": "32b91bb8-6e3a-11e7-a55f-0660b7976219"}, {"name": "NCI Map Style", "uuid": "3aeca6e7-c3c5-11e6-a7bc-0660b7976219"}
                                   , {"name": "MDA231_All_AP-MS_20170804 style 2", "uuid": "c62cbbce-7d2d-11e7-9743-0660b7976219"}]})

@bottle.get('/status')
def api_message(message):
    return 'tsv loader REST server v0.1'

@route('/upload', method='POST')
def do_upload():
#    plan   = request.forms.get('plan')
    my_req = request

    json_data = request.forms.get('plan')
    upload     = request.files.get('upload')
    plan   = request.files.get('plan')
    save_plan = request.query['save_plan'] in ['true', 'True']

    name, ext = os.path.splitext(upload.filename)
    print name + ',' + ext

    tf = tempfile.NamedTemporaryFile()
    upload.save(tf.name, True) # appends upload.filename automatically

    pfile = tempfile.NamedTemporaryFile()
    plan.save(pfile.name,True)

    name = request.forms.get('name')
    desc = request.forms.get('description')
    style_template = request.forms.get('template')

    #==================
    # SAVE TO MONGO
    #==================
    client = pymongo.MongoClient(mongodb_uri)
    db = client.files

    import_plans = db.import_plans

    plan_string = plan.file.read()

    print type(plan_string)

    data = json.loads(plan_string)
    if save_plan:
        import_plans.save({'plan_name': name + ' ' + strftime("%a, %d %b %Y %H:%M:%S", gmtime()), 'import_plan': data})

    try:
        import_plan = d2c.TSVLoadingPlan(pfile.name)

    except jsonschema.ValidationError as e1:
        print "Failed to parse the loading plan: " + e1.message
        print 'at path: ' + str(e1.absolute_path)
        print "in block: "
        print e1.instance
        return

    tsv_converter = d2c.TSV2CXConverter(import_plan)

    my_ndex = nc.Ndex("http://dev2.ndexbio.org", 'scratch','scratch')

    ng = tsv_converter.convert_tsv_to_cx(tf.name, name=name, description=desc)

    if len(style_template) > 0:
        toolbox.apply_template(ng, style_template, server='http://dev2.ndexbio.org', username='scratch', password='scratch') # NCI PID

    #ng.set_network_attribute('hasLayout', True)
    #toolbox.apply_source_target_layout(ng)


    client = pymongo.MongoClient(mongodb_uri)
    db = client.cache

    uniprot_lookup = db.uniprot_lookup
    uniprot_full_lookup = db.uniprot_full_lookup

    for node in ng.nodes(data=True):
        if len(node) > 1:
            node_name = node[1].get('name')
            prey = node[1].get('Prey')

            if prey is not None:
                uniprot_dict_lookup = uniprot_lookup.find_one({'id': prey})
                if uniprot_dict_lookup is not None:
                    uniprot_dict = uniprot_dict_lookup.get('uniprot_dict')
                else:
                    uniprot_dict, look_up_resp = lookup_uniprot(prey)
                    uniprot_lookup.save({'id': prey, 'uniprot_dict': uniprot_dict})
                    uniprot_full_lookup.save({'id': prey, 'look_up_resp': look_up_resp})

                if uniprot_dict is not None:
                    if uniprot_dict.get('comments') is not None and len(uniprot_dict.get('comments')) > 0:
                        ng.set_node_attribute(node[0],'comments', uniprot_dict.get('comments'))
                    if uniprot_dict.get('function') is not None and len(uniprot_dict.get('function')) > 0:
                        ng.set_node_attribute(node[0],'function', uniprot_dict.get('function'))
                    if uniprot_dict.get('subcellular_location') is not None and len(uniprot_dict.get('subcellular_location')) > 0:
                        ng.set_node_attribute(node[0],'subcellular_location', uniprot_dict.get('subcellular_location'))
                    if uniprot_dict.get('similarity') is not None and len(uniprot_dict.get('similarity')) > 0:
                        ng.set_node_attribute(node[0],'similarity', uniprot_dict.get('similarity'))
                    if uniprot_dict.get('synonyms') is not None and len(uniprot_dict.get('synonyms')) > 0:
                        ng.set_node_attribute(node[0],'synonyms', uniprot_dict.get('synonyms'))
                    if uniprot_dict.get('GO') is not None and len(uniprot_dict.get('GO')) > 0:
                        ng.set_node_attribute(node[0],'GO', uniprot_dict.get('GO'))
                    if uniprot_dict.get('GO_title') is not None and len(uniprot_dict.get('GO_title')) > 0:
                        ng.set_node_attribute(node[0],'GO_title', uniprot_dict.get('GO_title'))

                print node_name

    cx_stream = ng.to_cx_stream()
    my_ndex.save_cx_stream_as_new_network(cx_stream)

    return 'OK'

def lookup_uniprot(prey):
    return_dict = {'recommended_name': '', 'function': [], 'subcellular_location': [],'similarity': [], 'synonyms': [], 'GO': [], 'GO_title': []}
    look_up_json = {}

    client = pymongo.MongoClient(mongodb_uri)
    db = client.cache

    uniprot_full_lookup = db.uniprot_full_lookup

    uniprot_dict_lookup = uniprot_full_lookup.find_one({'id': prey})
    if uniprot_dict_lookup is not None:
        look_up_json = uniprot_dict_lookup.get('look_up_resp')
    else:
        url = 'http://www.ebi.ac.uk/proteins/api/proteins/' + prey
        look_up_resp = requests.get(url, headers={'Accept':'application/json'})

        if look_up_resp.ok:
            look_up_json = look_up_resp.json()

    if look_up_json is not None:
        #===================
        # COMMENTS SECTION
        #===================
        comments = look_up_json.get('comments')
        if comments is not None:
            function_array = []
            subcell_array = []
            simularity_array = []
            try:
                for comment in comments:
                    if comment.get('type') == 'FUNCTION':
                        for comment_text in comment.get('text'):
                            function_array.append(comment_text.get('value'))

                    elif comment.get('type') == 'SUBCELLULAR_LOCATION':
                        if comment.get('text') is not None:
                            for comment_text in comment.get('text'):
                                subcell_array.append(comment_text.get('value'))

                    elif comment.get('type') == 'SIMILARITY':
                        for comment_text in comment.get('text'):
                            simularity_array.append(comment_text.get('value'))

                return_dict['function'] = function_array
                return_dict['subcellular_location'] = subcell_array
                return_dict['similarity'] = simularity_array
            except Exception as e:
                print 'Issue with comments'
                print e.message


        #===================
        # PROTEIN SECTION
        #===================
        recommendedName = ''
        try:
            recommendedName = look_up_json.get('protein').get('recommendedName').get('fullName').get('value')
        except Exception as e:
            print 'No protein section'

        return_dict['recommended_name'] = recommendedName

        #===================
        # GENE SECTION
        #===================
        synonyms = []
        try:
            synonyms_array = look_up_json.get('gene')[0].get('synonyms')
            for syn in synonyms_array:
                synonyms.append(syn.get('value'))
        except Exception as e:
            print 'No synonyms section'

        return_dict['synonyms'] = synonyms

        #=======================
        # GO ANNOTATION SECTION
        #=======================
        go_annotations = []
        go_annotations_title = []
        try:
            dbReferences_array = look_up_json.get('dbReferences')
            for ref in dbReferences_array:
                if ref.get('type') == 'GO':
                    term = ref.get('properties').get('term')
                    if term is not None and term.startswith('P:'):
                        go_annotations.append('http://amigo.geneontology.org/amigo/term/' + ref.get('id'))
                        go_annotations_title.append(term[2:] + ' (' + ref.get('id') + ')')
        except Exception as e:
            print 'No synonyms section'

        return_dict['GO'] = go_annotations
        return_dict['GO_title'] = go_annotations_title

        print return_dict

        return return_dict, look_up_json
    else:
        return None, None



class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization'

            if request.method != 'OPTIONS':
                return fn(*args, **kwargs)

        return _enable_cors

def main():
    status = 0
    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, help='HTTP port', default=8072)
    args = parser.parse_args()

    print 'starting web server on port %s' % args.port
    print 'press control-c to quit'

    try:
 #       log.info('entering main loop')
        #api.install(EnableCors())
        api.run(host='0.0.0.0', port=args.port)
 #   except KeyboardInterrupt:
 #       log.info('exiting main loop')
    except Exception as e:
        str = 'could not start web server: %s' % e
  #      log.error(str)
        print str
        status = 1

   # log.info('exiting with status %d', status)
    return status

if __name__ == '__main__':
    sys.exit(main())