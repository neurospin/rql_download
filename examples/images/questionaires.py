"""
Get questionnaires
==================

Credit: V Frouin & A Grigis

In this tutorial we will send a request to a PIWS instance to retrieve some
questionnaire data.
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
# List questionnaires
# -------------------
#
# We first list all the available questionnaires.

# Define the RQL request
rql = "DISTINCT Any QN ORDERBY QN Where Q is Questionnaire, Q name QN"

# Ask for login & password
login, password = ask_credential()

# Define a connection
connection = CWInstanceConnection(url, login, password, verify=True,
                                  server_root="/home/{0}".format(login))

# Execute the request
rset = connection.execute(rql)
pprint(rset)


#############################################################################
# Get the 'PSYTOOLS-adsr-youth' questionnaire
# -------------------------------------------
#
# We want to get all the available 'PSYTOOLS-adsr-youth' questionnaire data.
# We ask the system for all the subjects and all the timepoints.

# Define the RQL request
rql = ("Any SC, T, FD Where Q is Questionnaire, Q name 'PSYTOOLS-adsr-youth', "
       "Q questionnaire_questionnaire_runs QR, QR in_assessment A, "
       "A timepoint T, QR subject S, S code_in_study SC, QR file F, F data FD")

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")

# Organize the result set so we can access the answer of a specific
# subject/timepoint/question.
dataset = {}
for subject, timepoint, questionnaire in rset:
    if subject not in dataset:
        dataset[subject] = {}
    if timepoint in dataset[subject]:
        raise ValueError("The timepoint '{0}' appears multiple time for "
                         "subject '{1}'.".format(timepoint, subject))
    dataset[subject][timepoint] = questionnaire
print("TS1 for subject '000085724167' at timepoint 'FU2': ",
      dataset["000085724167"]["FU2"]["ts_1"])
