"""
Get SNP proximity information
=============================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference in order to get a SNP proximity information.
"""

# Imports
from __future__ import print_function
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

#############################################################################
# SNP information
# ---------------

# Define the RQL request
rql = ("Any SP, SM, CN, GN Where S is Snp, S rs_id 'rs75684916', "
       "S position SP, S maf SM, S snp_chromosome C, C name CN, "
       "S snp_genes G, G hgnc_name GN")

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset)
info = {"rs75684916": {}}
for position, maf, chr_name, gene_name in rset:
    info["rs75684916"]["position"] = position
    info["rs75684916"]["maf"] = maf
    info["rs75684916"]["chr_name"] = chr_name
    info["rs75684916"].setdefault("gene_names", {})[gene_name] = {}
print("Information about SNP 'rs75684916': ")
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
for gene_name, gene_info in info["rs75684916"]["gene_names"].items():

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

print("Information about SNP 'rs75684916' with gene maps: ")
pprint(info)

