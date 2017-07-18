#!/usr/local/bin/python

import sys
import argparse
import bottle
import traceback
from bottle import route, default_app, request, parse_auth, HTTPResponse, response
import time
import os
import tempfile
import tsv.delim2cx as d2c
import jsonschema
import ndex.beta.toolbox as toolbox
import ndex.beta.layouts as layouts
import ndex.networkn as networkn
import ndex.client as nc


bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024 *1024

api = default_app()

#log = app.get_logger('api')

@bottle.get('/status')
def api_message(message):
    return 'tsv loader REST server v0.1'

@route('/upload', method='POST')
def do_upload():
#    plan   = request.forms.get('plan')
    upload     = request.files.get('upload')
    plan   = request.files.get('plan')

    name, ext = os.path.splitext(upload.filename)
    print name + ',' + ext

    tf = tempfile.NamedTemporaryFile()
    upload.save(tf.name, True) # appends upload.filename automatically


    pfile = tempfile.NamedTemporaryFile()
    plan.save(pfile.name,True)

    name = request.forms.get('name')
    desc = request.forms.get('description')

    try:
        import_plan = d2c.TSVLoadingPlan(pfile)

    except jsonschema.ValidationError as e1:
        print "Failed to parse the loading plan: " + e1.message
        print 'at path: ' + str(e1.absolute_path)
        print "in block: "
        print e1.instance
        return

    tsv_converter = d2c.TSV2CXConverter(import_plan)

    my_ndex = nc.Ndex("http://dev2.ndexbio.org", 'scratch','scratch')

    ng = tsv_converter.convert_tsv_to_cx(tf.name, name=name, description=desc)
    my_ndex.save_cx_stream_as_new_network(ng.to_cx_stream())

    return 'OK'




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
        api.install(EnableCors())
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