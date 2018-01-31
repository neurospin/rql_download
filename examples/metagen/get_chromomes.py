"""
Get chromosomes
===============

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance that contains
a genomic reference.
"""

# Imports
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

# Define the RQL request
rql = "Any N Where X is Chromosome, X name N"

# Ask for login & password
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Execute the request
rset = connection.execute(rql)
pprint(rset)
