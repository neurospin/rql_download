"""
Get Pathways related Genes
==========================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference in order to get the Pathways related Genes.
"""

# Imports
from __future__ import print_function
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

#############################################################################
# For one pathway
# ---------------

# Define the RQL request
rql = ("Any I Where X is Pathway, X name 'REACTOME_DNA_REPAIR', "
       "X pathway_genes G, G hgnc_name I")

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")
print("Number of Genes associated to 'REACTOME_DNA_REPAIR': ", len(rset))

#############################################################################
# For a list of pathways
# ----------------------

# Define the RQL request
rql = ("Any N, I Where X is Pathway, X name IN ('REACTOME_DNA_REPAIR', "
       "'KEGG_RIBOSOME'), X name N, X pathway_genes G, G hgnc_name I")

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")
info = {}
for name, rsid in rset:
    info.setdefault(name, []).append(rsid)
print("Number of SNPs associated to 'REACTOME_DNA_REPAIR': ", len(
    info["REACTOME_DNA_REPAIR"]))
print("Number of SNPs associated to 'KEGG_RIBOSOME': ", len(
    info["KEGG_RIBOSOME"]))
