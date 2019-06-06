#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `GeneSymbolSearcher` class."""

import os
import tempfile
import shutil

import unittest
import mock
from mock import MagicMock
import requests
import requests_mock
from requests.exceptions import HTTPError
from ndexutil.tsv.loaderutils import GeneSymbolSearcher
from requests.exceptions import HTTPError


class TestGeneSymbolSearcher(unittest.TestCase):
    """Tests for `GeneSymbolSearcher` class."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_get_symbol_none_passed_in(self):
        searcher = GeneSymbolSearcher()
        self.assertEqual(None, searcher.get_symbol(None))

    def test_get_symbol_cache_hit(self):
        searcher = GeneSymbolSearcher()
        searcher._cache['haha'] = 'gee'
        self.assertEqual('gee', searcher.get_symbol('haha'))

    def test_get_symbol_cache_hit_is_empty_str(self):
        searcher = GeneSymbolSearcher()
        searcher._cache['haha'] = ''
        self.assertEqual(None, searcher.get_symbol('haha'))

    def test_symbol_not_in_cache_no_hit(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value={'max_score': None,
                                             'took': 5, 'total': 0,
                                             'hits': []})
        searcher = GeneSymbolSearcher(bclient=mock)

        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='404', text=None)
            self.assertEqual('', searcher.get_symbol('haha'))

        mock.query.assert_called_with('haha')

    def test_symbol_not_in_cache_no_hit_and_httperror_raised(self):
        mock = MagicMock()
        mock.query = MagicMock(side_effect=HTTPError('some error'))
        searcher = GeneSymbolSearcher(bclient=mock)
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='404', text=None)
            self.assertEqual('', searcher.get_symbol('haha'))

        mock.query.assert_called_with('haha')

    def test_symbol_not_in_cache_no_hit_and_none_returned(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value=None)
        searcher = GeneSymbolSearcher(bclient=mock)
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='404', text=None)
            self.assertEqual('', searcher.get_symbol('haha'))

        mock.query.assert_called_with('haha')

    def test_symbol_not_in_cache_no_hit_and_hit_name_is_none(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value={'total': 1,
                                             'hits': [{'symbol': None}]})
        searcher = GeneSymbolSearcher(bclient=mock)
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='404', text=None)
            self.assertEqual('', searcher.get_symbol('haha'))

        mock.query.assert_called_with('haha')

    def test_symbol_not_in_cache_no_hit_total_incorrect(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value={'total': 1,
                                             'hits': []})
        searcher = GeneSymbolSearcher(bclient=mock)
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='404', text=None)
            self.assertEqual('', searcher.get_symbol('haha'))

        mock.query.assert_called_with('haha')

    def test_symbol_not_in_cache_no_but_got_hit_with_cache_check(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value={'max_score': 437.58682, 'took': 62,
                                             'total': 5031,
                                             'hits': [{'_id': '7157',
                                                       '_score': 437.58682,
                                                       'entrezgene': '7157',
                                                       'name': 'tumor protein p53',
                                                       'symbol': 'TP53',
                                                       'taxid': 9606},
                                                      {'_id': '24842',
                                                       '_score': 306.22318,
                                                       'entrezgene': '24842',
                                                       'name': 'tumor protein p53',
                                                       'symbol': 'Tp53',
                                                       'taxid': 10116},
                                                      {'_id': '109394672',
                                                       '_score': 296.02454,
                                                       'entrezgene': '109394672',
                                                       'name': 'tumor protein p53',
                                                       'symbol': 'TP53',
                                                       'taxid': 186990},
                                                      {'_id': '113633022',
                                                       '_score': 296.02454,
                                                       'entrezgene': '113633022',
                                                       'name': 'tumor protein p53',
                                                       'symbol': 'TP53',
                                                       'taxid': 90247},
                                                      {'_id': '102169621', '_score': 296.02454, 'entrezgene': '102169621', 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 9925}, {'_id': '113878373', '_score': 296.02454, 'entrezgene': '113878373', 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 30522}, {'_id': '101285670', '_score': 296.02454, 'entrezgene': '101285670', 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 9733}, {'_id': '105819395', '_score': 296.02454, 'entrezgene': '105819395', 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 379532}, {'_id': 'ENSMMMG00000019747', '_score': 296.02454, 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 9994}, {'_id': '100583326', '_score': 296.02454, 'entrezgene': '100583326', 'name': 'tumor protein p53', 'symbol': 'TP53', 'taxid': 61853}]})
        searcher = GeneSymbolSearcher(bclient=mock)
        self.assertEqual('TP53', searcher.get_symbol('tp53'))
        self.assertEqual('TP53', searcher.get_symbol('tp53'))
        mock.query.assert_called_once_with('tp53')

    def test_query_uniprot(self):
        mock = MagicMock()
        mock.query = MagicMock(return_value={'total': 0,
                                             'hits': []})
        searcher = GeneSymbolSearcher(bclient=mock)
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://www.uniprot.org/uniprot/HAHA.txt',
                           status_code='200', text="""ID   BXA1_CLOBO              Reviewed;        1296 AA.
AC   P0DPI0; A5HZZ9; A7G1U9; P01561; P10845; P18639;
DT   18-JUL-2018, integrated into UniProtKB/Swiss-Prot.
DT   18-JUL-2018, sequence version 1.
DT   08-MAY-2019, entry version 9.
DE   RecName: Full=Botulinum neurotoxin type A;
DE            Short=BoNT/A;
DE   AltName: Full=Bontoxilysin-A;
DE            Short=BOTOX;
DE   AltName: Full=Botulinum neurotoxin type A1;
DE   Contains:
DE     RecName: Full=Botulinum neurotoxin A light chain;
DE              Short=LC;
DE              EC=3.4.24.69 {ECO:0000269|PubMed:8243676};
DE   Contains:
DE     RecName: Full=Botulinum neurotoxin A heavy chain;
DE              Short=HC;
DE   Flags: Precursor;
GN   Name=botA {ECO:0000303|PubMed:2185020};
GN   Synonyms=atx {ECO:0000303|PubMed:8521962},
GN   bonT {ECO:0000303|PubMed:8863443};
OS   Clostridium botulinum.""")
            self.assertEqual('botA', searcher.get_symbol('haha'))
