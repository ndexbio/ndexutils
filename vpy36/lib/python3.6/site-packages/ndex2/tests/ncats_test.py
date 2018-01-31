import unittest

from numpy.core.multiarray import dtype

from ndex2.niceCXNetwork import NiceCXNetwork
from ndex2.cx.aspects.NodeElement import NodeElement
from ndex2.cx.aspects.EdgeElement import EdgeElement
from ndex2.cx.aspects.NodeAttributesElement import NodeAttributesElement
from ndex2.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE
import ndex2.client as nc
import networkx as nx
import pandas as pd
import os
import ndex2
import cPickle
import requests

path_this = os.path.dirname(os.path.abspath(__file__))

my_username = 'scratch'
my_password = 'scratch'
my_server = 'http://dev.ndexbio.org'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestNcats(unittest.TestCase):
    @unittest.skip("Temporary skipping")
    def test_ncats(self):
        output = None
        G = nx.Graph()
        G.add_node('ABC', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('DEF', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('GHI', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('JKL', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('MNO', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('PQR', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})
        G.add_node('XYZ', attr_dict={'Alpha': '1.234', 'Beta': '9.876'})

        G.add_edge('ABC', 'DEF', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('DEF', 'GHI', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('GHI', 'JKL', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('DEF', 'JKL', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('JKL', 'MNO', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('DEF', 'MNO', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('MNO', 'XYZ', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})
        G.add_edge('DEF', 'PQR', attr_dict={'weight': '0.4321', 'interaction': 'interacts-with'})

        niceCx = ndex2.create_nice_cx_from_networkx(G)

        niceCx.set_name('NCATS TEMP2')

        upload_message = niceCx.upload_to(my_server, my_username, my_password, visibility='PUBLIC')
        separator = os.sep
        uuid = upload_message.split(separator)[-1]
        print(uuid)

        url = 'http://general.bigmech.ndexbio.org:5603/directedpath/query?' \
              'source=%s' \
              '&target=%s' \
              '&pathnum=15' \
              '&uuid=%s' \
              '&server=%s' % ('ABC','MNO',uuid, 'dev.ndexbio.org')

        s = requests.session()
        s.auth = (my_username, my_password)

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json,text/plain',
                   'Cache-Control': 'no-cache',
                   'User-Agent':  'ndex2',
                   }
        response = s.post(url, data={}, headers=headers)
        #self.debug_response(response)
        response.raise_for_status()
        if response.status_code == 204:
            output = ""
        if response.headers['content-type'] == 'application/json':
            output = response.json()
        else:
            output = response.text

        print(output)

        #http://general.bigmech.ndexbio.org:5603/directedpath/query?source=AKT1,MDM2,MTOR&target=INSR,IRS1,EGFR&pathnum=15&uuid=84f321c6-dade-11e6-86b1-0ac135e8bacf&server=public.ndexbio.org

    @unittest.skip("Temporary skipping")
    def test_ncats3(self):
        path_to_network = os.path.join(path_this, 'tmp.pkl')
        with open(path_to_network, 'rb') as f:
            tmp2 = cPickle.load(f)
            tmp2.subnetwork_id = 1
            tmp2.upload_to('http://dev.ndexbio.org', 'scratch', 'scratch')
            print 'test'



    @unittest.skip("Temporary skipping")
    def test_ncats2(self):
        niceCx_from_server = ndex2.create_nice_cx_from_server(server='public.ndexbio.org',
        uuid= 'c0e70804-d848-11e6-86b1-0ac135e8bacf') # '8948691b-f4c8-11e7-adc1-0ac135e8bacf')#
        print(niceCx_from_server.get_summary())

        for k, v in niceCx_from_server.nodeAttributes.items():
            for na in v:
                val_type = na.get_data_type()
                if na.get_data_type() == ATTRIBUTE_DATA_TYPE.FLOAT:
                    value = na.get_values()
                    na.set_values(str(value))
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.INTEGER:
                    value = na.get_values()
                    na.set_values(str(value))
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.DOUBLE:
                    value = na.get_values()
                    na.set_values(str(value))
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.LIST_OF_FLOAT:
                    values = na.get_values()
                    na.set_data_type(ATTRIBUTE_DATA_TYPE.STRING)
                    na.set_values("")
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.LIST_OF_INTEGER:
                    values = na.get_values()
                    na.set_data_type(ATTRIBUTE_DATA_TYPE.STRING)
                    na.set_values("")
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.LIST_OF_DOUBLE:
                    values = na.get_values()
                    na.set_data_type(ATTRIBUTE_DATA_TYPE.STRING)
                    na.set_values("")
                elif na.get_data_type() == ATTRIBUTE_DATA_TYPE.LIST_OF_STRING:
                    values = na.get_values()
                    na.set_data_type(ATTRIBUTE_DATA_TYPE.STRING)
                    na.set_values("")
                elif na.get_data_type() == None:
                    value = na.get_values()
                    na.set_values(str(value))
                else:
                    value = na.get_values()
                    na.set_values(str(value))

                print(k)

        niceCx_from_server.upload_to(my_server, my_username, my_password)

    @unittest.skip("Temporary skipping")
    def test_ncats4(self):
        net_client = nc.Ndex2(host='public.ndexbio.org', username='scratch', password='scratch')
        net_set = net_client.get_network_set('0f06f419-68c1-11e7-961c-0ac135e8bacf')
        if net_set.get('networks'):
            for ns in net_set.get('networks'):
                niceCx_from_server = ndex2.create_nice_cx_from_server(server='public.ndexbio.org',
                    uuid=ns)
                #found_network = net_client.get_network_summary(ns)
                print(niceCx_from_server)

    #@unittest.skip("Temporary skipping")
    def test_ncats5(self):

        my_username = 'scratch'
        my_password = 'scratch'
        my_server = 'http://dev.ndexbio.org'
        big_gim_set_id = '4b28e99e-f584-11e7-a019-06832d634f41'
        path_this = os.path.dirname(os.path.abspath(__file__))
        path_to_network = os.path.join(path_this, 't8d1.csv')

        tissue = {}
        tissue['1'] = 'Adrenal Gland'
        tissue['2'] = 'Blood'
        tissue['3'] = 'Brain'
        tissue['4'] = 'Breast'
        tissue['5'] = 'Colon'
        tissue['6'] = 'Esophagus'
        tissue['7'] = 'Liver'
        tissue['8'] = 'Lung'
        tissue['9'] = 'Pancreas'
        tissue['10'] = 'Prostate'
        tissue['11'] = 'Skin'
        tissue['12'] = 'Stomach'
        tissue['13'] = 'Testis'
        tissue['14'] = 'Thyroid'

        disease = {}
        disease['1'] = 'adrenal carcinoma'
        disease['2'] = 'Fanconi anemia'
        disease['3'] = 'Parkinson disease, late-onset'
        disease['4'] = 'breast ductal carcinoma'
        disease['5'] = 'colitis (disease)'
        disease['6'] = 'Barrett esophagus'
        disease['7'] = 'chronic hepatitis C infection'
        disease['8'] = 'asthma, susceptibility to'
        disease['9'] = 'pancreatitis'
        disease['10'] = 'prostate cancer'
        disease['11'] = 'acne (disease)'
        disease['12'] = 'gastric cancer'
        disease['13'] = 'testicular cancer'
        disease['14'] = 'Thyrthyroid gland diseaseoid'

        ndex2_client = nc.Ndex2(host=my_server, username=my_username, password=my_password)

        for ki, vi in tissue.items():
            print(ki)
            for kj, vj in disease.items():
                path_to_network = os.path.join(path_this, 'BigGIM', 't%sd%s.csv' % (ki, kj))
                if os.path.isfile(path_to_network):
                    #print('BigGIM - %s %s' % (vi, vj))
                    with open(path_to_network, 'rU') as tsvfile:
                        header = [h.strip() for h in tsvfile.readline().split(',')]

                        df = pd.read_csv(tsvfile, delimiter=',', engine='python', names=header,
                                         dtype={'Gene1': str, 'Gene2': str})

                        niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Gene1', target_field='Gene2',
                                                                  source_node_attr=['score'], target_node_attr=['score'])

                        context = [{'entrez': 'http://www.ncbi.nlm.nih.gov/gene/'}]
                        niceCx.set_context(context)
                        niceCx.set_name('BigGIM - %s %s' % (vi, vj))

                        upload_message = niceCx.upload_to(my_server, my_username, my_password, visibility='PUBLIC')
                        net_uuid = upload_message.split('/')[-1]

                        print(str(net_uuid))
                        #ndex2_client.add_networks_to_networkset(big_gim_set_id, net_uuid)

        #with open(path_to_network, 'rU') as tsvfile:
            #header = [h.strip() for h in tsvfile.readline().split(',')]

            #df = pd.read_csv(tsvfile, delimiter=',', engine='python', names=header)

            #niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Gene1', target_field='Gene2',
            #                                          source_node_attr=['score'], target_node_attr=['score'])

            #upload_message = niceCx.upload_to(my_server, my_username, my_password)

            #print(niceCx)

    @unittest.skip("Temporary skipping")
    def test_ncats6(self):
        load_these = []

