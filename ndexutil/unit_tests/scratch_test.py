__author__ = 'aarongary'
import subprocess
import os
from os import getcwd
import ndexebs.ebs2cx as ebs2cx
import ndex.client as nc
import ndex.networkn as networkn
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox
import sys
import json
import ujson
from elasticsearch import Elasticsearch
from os import listdir
from os.path import isfile, join
import csv
import time
import io
import networkx as nx
import colorlover as cl
#===========================================
# This pipeline requires ndex-enrich. Clone
# repo in the same folder as this proj root
#===========================================
sys.path.append('../../ndex-enrich')
import ndex_access
import term2gene_mapper
import data_model as dm
import fake_persistence as storage
import similarity_map_utils as smu
import sys
from os import path
from ndex.networkn import NdexGraph

EPSILON = sys.float_info.epsilon  # smallest possible difference

def convert_to_rgb(minval, maxval, val, colors):
    fi = float(val-minval) / float(maxval-minval) * (len(colors)-1)
    i = int(fi)
    f = fi - i
    if f < EPSILON:
        return colors[i]
    else:
        (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i+1]
        return int(r1 + f*(r2-r1)), int(g1 + f*(g2-g1)), int(b1 + f*(b2-b1))

def convert_to_rgb_string(minval, maxval, val, colors):
    r, g, b = convert_to_rgb(minval, maxval, val, colors)
    return 'rbg(' + str(r) + ',' + str(g) + ', ' + str(b) + ')'


#with open(path.join(path.abspath(path.dirname(__file__)),'nci_pid_preview.cx'), 'r') as file_handler:
#    network_in_cx_from_file = file_handler.read().replace('\n', '')
#    G = NdexGraph(cx=json.loads(network_in_cx_from_file))
#    print G.to_cx()

source_network = networkn.NdexGraph(server="http://dev.ndexbio.org", username="scratch", password="scratch", uuid="49eb81d9-665a-11e7-8e93-06832d634f41")
toolbox.apply_template(source_network, "4a78a6ab-665a-11e7-8e93-06832d634f41", server="http://dev.ndexbio.org", username="scratch", password="scratch")
source_network.upload_to(server="http://dev.ndexbio.org", username="scratch", password="scratch")

if False:
    elastic_search_uri = 'http://ec2-107-21-1-214.compute-1.amazonaws.com/'
    es = Elasticsearch([elastic_search_uri],send_get_body_as='POST',timeout=300) # Prod Clustered Server

    search_body = {
        'sort' : [
            '_score'
        ],
       'query': {
            'bool': {
                'must': [
                   {'match': {
                      '_id': '2020037526'
                   }}
                ]
             }
        },
        'size': 1
    }

    results = es.search(
        index = 'clusters',
        body = search_body
    )

    if(len(results['hits']['hits']) > 0):
        result = results['hits']['hits'][0]['_source']
        x_node_list = result.get('x_node_list')
        y_node_list = result.get('y_node_list')
        correlation_matrix = result.get('correlation_matrix')

        edge_tuples = [(x_node_list[e.get('x_loc')].get('name') + '_' + result.get('x_node_list_type'), y_node_list[e.get('y_loc')].get('name') + '_' + result.get('y_node_list_type'), {'weight': e.get('correlation_value')}) for e in correlation_matrix]

        x_node_values = [n.get('value') for n in x_node_list]
        y_node_values = [n.get('value') for n in y_node_list]
        all_node_values = x_node_values + y_node_values
        max_nv = max(all_node_values)
        min_nv = min(all_node_values)
        denom = max_nv - min_nv

        nodes_x_y_dict = {n.get('name') + '_' + result.get('x_node_list_type'): (n.get('value') - min_nv)/denom for n in x_node_list}
        for ny in y_node_list:
            if nodes_x_y_dict.get(ny.get('name') + '_' + result.get('y_node_list_type')) is not None:
                nodes_x_y_dict[ny.get('name') + '_' + result.get('y_node_list_type')] = (ny.get('value') - min_nv)/denom

        G=nx.Graph()
        G.add_edges_from(edge_tuples)
        nx.set_node_attributes(G, 'expression', nodes_x_y_dict)
        final_positions = nx.spring_layout(G, iterations=5)
        print final_positions
        print len(edge_tuples)

        gene_list = {
            'ENAH_g': 1, 'CDH11_g': 1, 'TRAPPC8_g': 1,'GLTP_g': 1,
            'ENAH_v': 1, 'CDH11_v': 1, 'TRAPPC8_v': 1,'GLTP_v': 1,
            'ENAH_m': 1, 'CDH11_m': 1, 'TRAPPC8_m': 1,'GLTP_m': 1,
            }

        node_array = []
        colors = [(122, 255, 255), (255, 0, 255)]
        i = 0

        degree_dict = G.degree()
        for n,d in G.nodes_iter(data=True):
            id_clean = n.replace("_g","").replace("_v","").replace("_m","")

            expressionRGBString = convert_to_rgb_string(0.0, 1.0, d.get('expression'), colors)
            node_suffix = n[-2:]
            node_shape = 'dot'
            if node_suffix == '_v':
                node_shape = "diamond"
            elif node_suffix == '_m':
                node_shape = "triangle"
            elif node_suffix == '_p':
                node_shape = "square"

            node_degree = degree_dict.get(n)
            if node_degree is not None and node_degree > 30:
                node_degree = 30 + ((node_degree - 30)/10)
                node_degree = 50 if node_degree > 50 else node_degree
                node_degree = 15 if node_degree < 15 else node_degree
            else:
                node_degree = 15

            font_size = node_degree

            if gene_list.get(n) is not None:
                node_array.append({
                    'id': i, 'label': id_clean, 'node_value': d.get('weight'),
                    'permaFont': {'size': 40}, 'font': {'size': 40}, 'permaLabel': id_clean, 'borderWidth': 4,
                    'color': {'background': expressionRGBString, 'border': '#FF0000'}, 'permaColor': {'background':expressionRGBString, 'border': '#FF0000'},
                    'expressionRGB': expressionRGBString, 'clusterRGB': '#C0C0C0',
                    #'local_cc': result.nodes[i].local_cc,
                    'shape': node_shape, 'size': 20, 'permaSize': 20, 'nodeDegree': 20
                })
            else:
                print 'not query node'
                id_clean_label = id_clean;
                if id_clean[-2:] == "_p" and len(id_clean.length) >= 12:
                    id_clean_label = id_clean[0:9] + '...';

                node_array.append({'id': i, 'label': id_clean_label, 'permaLabel': id_clean, 'node_value': d.get('weight'),
                'permaFont': {'size': font_size}, 'font': {'size': font_size},
                'color': {'background': expressionRGBString, 'border': '#c0c0c0'},
                'expressionRGB': expressionRGBString, 'clusterRGB': '#C0C0C0', #clusterRGBString,
                #'local_cc': result.nodes[i].local_cc,
                'permaColor': {'background':expressionRGBString, 'border': '#c0c0c0'},
                'shape': node_shape, 'size': 20, 'permaSize': 20, 'nodeDegree': node_degree});

            i += 1
        print ujson.dumps(node_array)


        edge_array = []
        colors = [(0, 0, 255), (255, 255, 255), (255, 0, 0)]
        max_edge_value = 0;
        min_edge_value = 1000;

        edge_weights_by_id = {}
        edge_weights_unsorted = []
        for s,t,d in G.edges_iter(data=True):
            if d.get('weight') > max_edge_value:
                max_edge_value = d.get('weight')
            if d.get('weight') < min_edge_value:
                min_edge_value = d.get('weight')
            e_weight = d.get('weight')

            edge_weights_unsorted.append(e_weight)

            e_weight_small = float("{0:.2f}".format(e_weight))
            if edge_weights_by_id.get(e_weight_small) is None:
                edge_weights_by_id[e_weight_small] = [i]
            else:
                edge_weights_by_id[e_weight_small].append(i)

        edge_weights_sorted = sorted(edge_weights_unsorted, reverse=True)

        top_400 = edge_weights_sorted[400]
        #==============================
        #
        #==============================
        if min_edge_value > 0:
            min_edge_value = 0

        for s,t,d in G.edges_iter(data=True):
            r_g_b = convert_to_rgb_string(min_edge_value, max_edge_value, d.get('weight'), colors)
            e_weight = d.get('weight')
            if e_weight >= top_400:
                edge_array.append({
                    'id': i,
                    'from': s, 'to': t, 'label': '',
                    'font': {'align': 'horizontal', 'size': 20, 'background': 'rgba(255,255,255,255)'},
                    'title': e_weight, 'zindex': 1050,
                    'edgeWeight': e_weight,
                    'color': {
                        'color': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'hover': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'highlight': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'opacity': (0.6)
                    },
                    'permaColor': {
                        'color': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'hover': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'highlight': convert_to_rgb_string(min_edge_value, max_edge_value, e_weight, colors),
                        'opacity': (0.6)
                    },
                    'hidden': False

                })
            if i % 1000 == 0:
                print str(i)
            i += 1

        print ujson.dumps(edge_array)

def getNetworkProperty(summary, prop_name):
    for prop in summary['properties']:
        if ( prop['predicateString'] == prop_name) :
            return prop['value']
    return None

if False:
    netpath_base_uri = 'http://www.netpath.org/pathways?path_id='
    ndex_server = 'http://dev.ndexbio.org'
    current_directory = os.path.dirname(os.path.abspath(__file__))
    run_normal = False
    current_netpath_metadata = {}


    ndex = nc.Ndex(ndex_server,'netpathtest','netpathtest')
    summaries = ndex.search_networks('*', 'netpathtest',0,50)

    for summary in summaries.get('networks'):
        print summary.get('name')
        #print summary.get('externalId')
        #print summary.get('description')
        #print getNetworkProperty(summary, 'Reference')
        print '===================='

        current_netpath_metadata[summary.get('name')] = {
            'uuid': summary.get('externalId'),
            'description': summary.get('description'),
            'reference': getNetworkProperty(summary, 'Reference')
        }

    print json.dumps(current_netpath_metadata)

    #print json.dumps(summaries)
