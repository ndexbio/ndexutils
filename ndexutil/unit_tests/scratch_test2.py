__author__ = 'aarongary'
from mygene import MyGeneInfo

#mg = MyGeneInfo()

#participant_symbol = mg.query('BRF1')
#if participant_symbol is not None and participant_symbol.get('hits') is not None and len(participant_symbol.get('hits')) > 0:
#    ph = participant_symbol.get('hits')[0]
#    if 'symbol' in ph:
#        participant_symbol = ph.get('symbol')

#participant_symbol2 = mg.getgene('LOC103689948')

#print participant_symbol2
#print participant_symbol


search_trie = {
    'chromosome': {
        'segregation': {'found': {'classification': 'GO', 'label': 'chromosome segregation', 'id': 'GO:123'}}
    },
    'mitotic': {
        'chromosome': {
            'movement': {
                 'towards': {
                     'spindle': {
                         'pole': {'found': {'classification': 'GO', 'label': 'mitotic chromosome movement towards spindle pole', 'id': 'GO:124'}}
                     }
                 }
            }
        }
    },
    'NFKB1': {'found': 'GENE:'},
    'BRAF': {'found': 'GENE:'},
    'BRACA1': {'found': 'GENE:'},
    'BRACA2': {'found': 'GENE:'},
    'ESPN': {'found': 'GENE:'},
    'FOX1': {'found': 'GENE:'}
}


search_sentence = 'NFKB1 BRAF ESPN chromosome segregation mitotic chromosome movement towards spindle pole'

ss_array = search_sentence.split(' ')
ss_keep_going = None
for ss_a in ss_array:
    if ss_keep_going is not None:
        ss_found = ss_keep_going.get(ss_a)
    else:
        ss_found = search_trie.get(ss_a)

    if ss_found is not None and 'found' in ss_found:
        print ss_a + ' is a ' + str(ss_found.get('found'))
        ss_keep_going = None
        ss_found = None
    elif ss_keep_going is None:
        ss_keep_going = search_trie.get(ss_a)
    else:
        ss_keep_going = ss_keep_going.get(ss_a)



#import ndex.networkn as networkn
#import ndex.beta.toolbox as toolbox

#source_network = networkn.NdexGraph(server="http://www.ndexbio.org", username="pvtodorov", password="** your password **", uuid="0c42488b-657c-11e7-a03e-0ac135e8bacf")
#toolbox.apply_template(source_network, "feecdc30-5dbc-11e7-8f50-0ac135e8bacf", server="http://www.ndexbio.org", username="pvtodorov", password="** your password **")
#source_network.upload_to(server="http://www.ndexbio.org", username="pvtodorov", password="** your password **")


