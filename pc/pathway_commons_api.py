__author__ = 'dexter'

import requests, math


# This class provides an interface to the Pathway Commons Web Service V7 API
# It is far from a complete interface, simply providing convenience methods
# used by ndex-python-utilities
#
class PathwayCommonsV2:
    def __init__(self):
        self.pc_service_base_uri = "http://www.pathwaycommons.org/pc2/"

        self.formats = ["BINARY_SIF", "BIOPAX", "EXTENDED_BINARY_SIF", "GSEA", "SBGN"]

        # convenience map of datasource abbreviations to the Pathway Commons Web Service V7 uri
        self.datasources = {
            "reactome": {
                "uri": "http://purl.org/pc2/7/reactome_human",
                "pathways": 1597
            },
            "pid": {
                "uri": "http://purl.org/pc2/7/pid",
                "pathways": 745
            },
            "phosphositeplus": {
                "uri": "http://purl.org/pc2/7/psp"
            },
            "humancyc": {
                "uri": "http://purl.org/pc2/7/hprd",
                "pathways": 289
            },
            "hprd": {
                "uri": "http://purl.org/pc2/7/pid"
            },
            "panther": {
                "uri": "http://purl.org/pc2/7/panther_human",
                "pathways": 284
            },
            "dip": {
                "uri": "http://purl.org/pc2/7/dip_human"
            },
            "biogrid": {
                "uri": "http://purl.org/pc2/7/biogrid_human"
            },
            "intact": {
                "uri": "http://purl.org/pc2/7/intact_human"
            },
            "intactcomplex": {
                "uri": "http://purl.org/pc2/7/intact_complex_human"
            },
            "bind": {
                "uri": "http://purl.org/pc2/7/bind_human",
            },
            "corum": {
                "uri": "http://purl.org/pc2/7/corum_human"
            },
            "transfac": {
                "uri": "http://purl.org/pc2/7/transfac",
                "pathways": 427
            },
            "mirtarbase": {
                "uri": "http://purl.org/pc2/7/mirtarbase_human",
                "pathways": 5
            },
            "drugbank": {
                "uri": "http://purl.org/pc2/7/drugbank"
            },
            "reconx": {
                "uri": "http://purl.org/pc2/7/reconx",
                "pathways": 1
            },
            "ctd": {
                "uri": "http://purl.org/pc2/7/ctdbase",
                "pathways": 28155
            },
            "kegg": {
                "uri": "http://purl.org/pc2/7/kegg_hsa",
                "pathways": 195
            }
        }

    def check_datasource(self, datasource_abbreviation):
        checked = datasource_abbreviation.lower()
        if self.datasources.get(checked):
            return checked
        else:
            return False

    def check_format(self, format):
        checked = format.upper()
        if checked == "EBS":
            checked = "EXTENDED_BINARY_SIF"
            return checked
        if checked == "SIF":
            checked = "BINARY_SIF"
            return checked
        if checked in self.formats:
            return checked
        else:
            return False

    def get_pathway_info_for_datasource(self, datasource_abbreviation):

        # look up the datasource uri by the abbreviation
        datasource = self.datasources.get(datasource_abbreviation)

        # compose the uri to get the "top pathways" for the datasource
        uri = self.pc_service_base_uri + "top_pathways.json?datasource=" + datasource.get("uri")
        print "GET " + uri

        # perform the request and check the status
        r = requests.get(uri)
        r.raise_for_status()

        # return the parsed JSON
        return r.json()


    # Get a pathway as text in Extended Binary SIF format based on its pathway commons uri
    def get_pathway_ebs_by_uri(self, pathway_uri):
        uri = self.pc_service_base_uri + "get?uri=" + pathway_uri + "&format=EXTENDED_BINARY_SIF"
        print "GET " + uri
        r = requests.get(uri)
        r.raise_for_status()
        return r.text

#http://www.pathwaycommons.org/pc2/top_pathways.json?datasource=http://purl.org/pc2/7/pid
#http://www.pathwaycommons.org/pc2/top_pathways.json?datasource=http://purl.org/pc2/7/pid






