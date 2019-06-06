# -*- coding: utf-8 -*-

import re
import logging
import requests
from requests.exceptions import HTTPError
from biothings_client import get_client

logger = logging.getLogger(__name__)


class NetworkIssueReport(object):
    """
    Holds summary information about issues found during network
    creation
    """
    def __init__(self, network_name):
        """
        Constructor

        :param network_name: name of network to display in report
        :type network_name: string
        """
        self._networkname = network_name
        self._issuemap = {}
        self._nodetype = set()

    def add_nodetype(self, nodetype):
        """
        Adds `nodetype` to set of node types

        :param nodetype: value of type node attribute
        :type nodetype: string
        :return: None
        """
        if nodetype is None:
            return
        self._nodetype.add(nodetype)

    def get_nodetypes(self):
        """
        Gets node types

        :return: set of node types
        :rtype: set
        """
        return self._nodetype

    def addissues(self, description, issue_list):
        """
        Adds issues to the report

        :param description: description of issue
        :type description: string
        :param issue_list: list of strings describing the issues
        :type issue_list: list
        :return: None
        """
        if issue_list is None:
            return
        if len(issue_list) is 0:
            return
        if description is None:
            return
        self._issuemap[description] = issue_list

    def get_fullreport_as_string(self):
        """
        Gets report as string

        :return: report in a human readable form with newlines
                 and tabs for indenting the issues
        :rtype: string
        """
        res = ''
        for key in self._issuemap.keys():
            num_issues = len(self._issuemap[key])
            if num_issues == 1:
                issue_word = 'issue'
            else:
                issue_word = 'issues'
            res += '\t' + str(num_issues) + ' ' + issue_word + ' -- ' +\
                   key + '\n'
            for entry in self._issuemap[key]:
                res += '\t\t' + str(entry) + '\n'
        if len(res) is 0:
            return ''

        return str(self._networkname) + '\n' + res


class NetworkUpdator(object):
    """
    Base class for classes that update
    a network
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def get_description(self):
        """
        Subclasses should implement
        :return:
        """
        raise NotImplementedError('subclasses should implement')

    def update(self, network):
        """
        subclasses should implement
        :param network:
        :return:
        """
        raise NotImplementedError('subclasses should implement')


class GeneSymbolSearcher(object):
    """
    Wrapper around :py:mod:`biothings_client` to query
    """

    def __init__(self,
                 bclient=get_client('gene')):
        """
        Constructor
        """
        self._cache = {}
        self._bclient = bclient

    def _query_mygene(self, val):
        """
        Queries biothings_client with 'val' to find
        hit

        :param val: id to send to :py:mod:`biothings_client`
        :type val: string
        :return: gene symbol or None
        :rtype: string
        """
        try:
            res = self._bclient.query(val)
            if res is None:
                logger.debug('Got None back from query for: ' + val)
                return ''
            logger.debug('Result from query for ' + val + ' ' + str(res))
            if res['total'] == 0:
                logger.debug('Got No hits back from query for: ' + val)
                return ''
            if len(res['hits']) > 0:
                logger.debug('Got a hit from query for: ' + val)
                sym_name = res['hits'][0].get('symbol')
                if sym_name is None:
                    logger.debug('Symbol name was None for ' + val)
                    return ''
                return sym_name.upper()
        except HTTPError as he:
            logger.error('Caught exception running query for: ' + val)

        return None

    def _query_uniprot(self, val):
        """

        :param val:
        :return:
        """
        res = requests.get('https://www.uniprot.org/uniprot/' +
                           val.upper() + '.txt')
        for entry in res.text.split('\n'):
            if entry.startswith('GN'):
                if 'Name' in entry:
                    return re.sub(';.*', '',
                                  re.sub(' .*', '',
                                         re.sub('^GN.*Name=',
                                                '', entry)))
        return None

    def get_symbol(self, val):
        """
        Queries biothings_client with 'val' to find
        hit

        :param val: id to send to :py:mod:`biothings_client`
        :type val: string
        :return: gene symbol or None
        :rtype: string
        """
        if val is None:
            logger.error('None passed in')
            return None

        cache_symbol = self._cache.get(val)
        if cache_symbol is not None:
            if cache_symbol == '':
                return None
            return cache_symbol

        sym_name = self._query_mygene(val)
        if sym_name is None or sym_name == '':
            res = self._query_uniprot(val)
            if res is not None:
                self._cache[val] = res
                return res
            sym_name = ''
        self._cache[val] = sym_name
        return sym_name
