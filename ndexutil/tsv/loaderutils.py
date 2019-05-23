# -*- coding: utf-8 -*-


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
                res += '\t\t' + entry + '\n'
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