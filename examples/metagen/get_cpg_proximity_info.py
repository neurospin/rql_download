"""
Get CPG proximity information
=============================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference in order to get a CPG proximity information.
"""

# Imports
from __future__ import print_function
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

#############################################################################
# CPG information
# ---------------

# Define the RQL request
rql = ("Any CP, CN, GN Where C is Cpg, C cg_id 'cg11448807', C position CP, "
       "C cpg_chromosome CR, CR name CN, C cpg_genes G, G hgnc_name GN")

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset)
info = {"cg11448807": {}}
for position, chr_name, gene_name in rset:
    info["cg11448807"]["position"] = position
    info["cg11448807"]["chr_name"] = chr_name
    info["cg11448807"].setdefault("gene_names", {})[gene_name] = {}
print("Information about SNP 'cg11448807': ")
pprint(info)

#############################################################################
# Add Gene information
# --------------------
# 
# It is possible to perform this step with the previous one, but it is
# dangerous since the gene related information we want to extract are not
# always specified.
# That the reson why we retrieve the gene information programmatically.

# Go through each gene
for gene_name, gene_info in info["cg11448807"]["gene_names"].items():

    # CpgIslands
    rql = ("Any I Where X is Gene, X hgnc_name '{0}', X gene_cpg_islands C, "
           "C cpg_island_id I".format(gene_name))
    rset = connection.execute(rql)
    gene_info["cpg_islands"] = [row[0] for row in rset]

    # Cpgs
    rql = ("Any I Where X is Gene, X hgnc_name '{0}', X gene_cpgs C, "
           "C cg_id I".format(gene_name))
    rset = connection.execute(rql)
    gene_info["cpgs"] = [row[0] for row in rset]

    # Pathways
    rql = ("Any N Where X is Gene, X hgnc_name '{0}', X gene_pathways P, "
           "P name N".format(gene_name))
    rset = connection.execute(rql)
    gene_info["pathways"] = [row[0] for row in rset]

print("Information about SNP 'cg11448807' with gene maps: ")
pprint(info)

