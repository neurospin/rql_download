"""
Get Genes related CpgIslands
============================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference in order to get the Genes related CpgIslands.
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
rql = ("Any I Where X is Gene, X hgnc_name 'BRCA2', X gene_cpg_islands C, "
       "C cpg_island_id I")

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset)
print("Number of CpgIslands associated to 'BRCA2': ", len(rset))

#############################################################################
# For a list of genes
# -------------------

# Define the RQL request
rql = ("Any N, I Where X is Gene, X hgnc_name IN ('BRCA2', 'SRY'), "
       "X hgnc_name N, X gene_cpg_islands C, C cpg_island_id I")

# Execute the request
rset = connection.execute(rql)
pprint(rset)
info = {}
for name, rsid in rset:
    info.setdefault(name, []).append(rsid)
print("Number of CpgIslands associated to 'BRCA2': ", len(info["BRCA2"]))
print("Number of CpgIslands associated to 'SRY': ", len(info["SRY"]))
