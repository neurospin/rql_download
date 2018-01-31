"""
Get Genes related SNPs
======================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference in order to get the Genes related SNPs.
"""

# Imports
from __future__ import print_function
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

#############################################################################
# For one gene
# ------------

# Define the RQL request
rql = "Any I Where X is Gene, X hgnc_name 'BRCA2', X gene_snps S, S rs_id I"

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")
print("Number of SNPs associated to 'BRCA2': ", len(rset))

#############################################################################
# For a list of genes
# -------------------

# Define the RQL request
rql = ("Any N, I Where X is Gene, X hgnc_name IN ('BRCA2', 'TOMM22P2'), "
       "X hgnc_name N, X gene_snps S, S rs_id I")

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")
info = {}
for name, rsid in rset:
    info.setdefault(name, []).append(rsid)
print("Number of SNPs associated to 'BRCA2': ", len(info["BRCA2"]))
print("Number of SNPs associated to 'TOMM22P2': ", len(info["TOMM22P2"]))
