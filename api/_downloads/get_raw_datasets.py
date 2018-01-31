"""
Get RAW datasets
================

Credit: A Grigis

In this tutorial we will send a request to a PIWS instance to retrieve RAW
datasets
"""

# Imports
from __future__ import print_function
import os
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential

# Define CubicWeb service url
url = "https://imagen2.cea.fr/database"

#############################################################################
# List RAW types
# --------------
#
# We first list all the available RAW data types.

# Define the RQL request
rql = "DISTINCT Any L ORDERBY L Where S is Scan, S label L"

# Ask for login & password
login, password = ask_credential()

# Define a connection
connection = CWInstanceConnection(url, login, password, verify=True,
                                  server_root="/home/{0}".format(login))

# Execute the request
rset = connection.execute(rql)
pprint(rset)


#############################################################################
# Get T1 data
# -----------
#
# We want to list all the available T1 data and associated subjects.

# Define the RQL request
rql = ("Any S, C Where S is Scan, S subject SU, SU code_in_study C, S label "
       "'ADNI_MPRAGE'")

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")


#############################################################################
# Download T1 data
# ----------------
#
# We want now to download the available T1 data. For illustration puposes, we
# will select only the data from one subject.

# Select the subject
subject = rset[0][1]

# Define the RQL request
rql = ("Any S Where S is Scan, S subject SU, SU code_in_study '{0}', "
       "S label 'ADNI_MPRAGE'".format(subject))

# Create a persistent temporary directory
tmp_dir = os.path.join(os.sep, "tmp", "cwbrowser_data")
if not os.path.isdir(tmp_dir):
    os.mkdir(tmp_dir)

# Execute the request
rset = connection.execute_with_sync(rql, sync_dir=tmp_dir)
pprint(rset)

