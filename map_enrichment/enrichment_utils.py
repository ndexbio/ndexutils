from scipy.stats import hypergeom


def load_gene_list(path):
    with open(path, 'R') as file:
        gene_list = file.read().split()
        return gene_list


def enrich_map(map_network, query_genes, genes_attribute="genes"):
    # the Query gene list is Q
    # determine all_genes, the set of all genes annotated on network nodes
    # the size of all_genes is all_gene_count
    all_genes = get_all_genes(map_network)
    all_genes_count = len(all_genes)


    # determine "covered_genes", the overlap between query_genes and all_genes
    # the query genes not overlapping are recorded as "not_covered"
    covered_genes = query_genes & all_genes
    covered_gene_count = len(covered_genes)

    # for each node in the map_network,
    for node in map_network.nodes():

        # the genes associated with the node, node_genes are specified by gene_attribute (defaulting to "genes")
        if genes_attribute in map_network.get_node_attributes(node):
            node_genes = map_network.get_node_attribute(node, genes_attribute)
            node_gene_count = len(node_genes)

            # calculate the overlap and enrichment for
            # covered_genes in node_genes for all_genes

            overlap = list(covered_genes & node_genes)
            map_network.set_node_attribute("overlap", overlap)
            k = len(overlap)
            map_network.set_node_attribute("k", k)
            pvalue = hypergeom(all_genes_count, node_gene_count, covered_gene_count).sf(k)
            map_network.set_node_attribute("pvalue", pvalue)


def get_all_genes(map_network):
    return map_network.get_network_attribute("all_genes")



