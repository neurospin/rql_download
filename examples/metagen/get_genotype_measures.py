"""
Get Genotype Measures
=====================

Credit: A Grigis

In this tutorial we will show you how to filter a PLINK dataset containing
genotype data. This example is an excerpt of 'piws.metagen.genotype'.
Note that all the described steps have been implemented within the
web services that host your geniomic data. If the service has been
properly configured you can use the CWInstanceConnection.get_genotype_measure
method. 
"""

# Imports
from __future__ import print_function
import os
import numpy
import zipfile
from pprint import pprint
from cwbrowser import CWInstanceConnection
from cwbrowser.utils import ask_credential
from pysnptools.snpreader import Bed

#############################################################################
# Read&Filter PLINK
# -----------------
#
# We first define a simple function to load and filter a PLINK dataset.
# This function is from 'piws.metagen.genotype'.

def load_plink_bed_bim_fam_dataset(path_dataset, snp_ids=None,
                                   subject_ids=None, count_A1=True):
    """
    Load a Plink bed/bim/fam dataset as a SnpData instance. Optionnally a
    specific list of snps or subjects can be extracted to avoid loading
    everything in memory.

    Parameters
    ----------
    path_dataset: str
        Path to the Plink bed/bim/fam dataset, with or without .bed extension.
    snp_ids: list/set of str, default None
        Snps that should be extracted if available in the dataset.
        By default None, all snps are loaded.
    subject_ids: list of str, default None
        Subjects that should be extracted if available in the dataset.
        By default None, all subjects are loaded.
    count_A1: bool, default True
        Genotypes are provided as allele counts, A1 if True else A2.

    Return
    ------
    snp_data: pysnptools object
        PLINK data loaded by the 'pysnptools' library.
    """

    # Load the metadata, without loading the genotypes
    snp_data = Bed(path_dataset, count_A1=count_A1)

    # If requested, filter on snp ids
    if snp_ids is not None:
        snp_ids = set(snp_ids)
        snp_bool_indexes = [(s in snp_ids) for s in snp_data.sid]
        snp_data = snp_data[:, snp_bool_indexes]

    # If requested, filter on subject ids
    if subject_ids is not None:
        subject_ids = set(subject_ids)
        subject_bool_indexes = [(s in subject_ids) for s in snp_data.iid[:, 1]]
        snp_data = snp_data[subject_bool_indexes, :]

    # Load the genotypes from the Plink dataset
    snp_data = snp_data.read()

    return snp_data

#############################################################################
# Get some PLINK data
# -------------------
#
# We want to download the QC Gentic PLINK data available in IMAGEN.
# Define CubicWeb service url
url = "https://imagen2.cea.fr/database"

# Ask for login & password
print(url)
login, password = ask_credential()

# Define a connection
connection = CWInstanceConnection(url, login, password, verify=True,
                                  server_root="/home/{0}".format(login))

# Define the RQL request
rql = "Any G Where G is GenomicMeasure, G label 'QC_Genetics'"

# Create a persistent temporary directory
tmp_dir = os.path.join(os.sep, "tmp", "cwbrowser_data")
if not os.path.isdir(tmp_dir):
    os.mkdir(tmp_dir)

# Execute the request
rset = connection.execute_with_sync(rql, sync_dir=tmp_dir, nb_tries=5)
pprint(rset)

# Unzip the downloaded file
zip_file = rset[0][0]
basename = os.path.basename(zip_file)
dirname = os.path.dirname(zip_file)
fantasy_zip = zipfile.ZipFile(zip_file)
fantasy_zip.extractall(dirname)
fantasy_zip.close()
plink_data = os.path.join(dirname, basename.split(".")[0])

#############################################################################
# Get SNPs of interest
# --------------------
#
# We now retrieve some SNPs of interest from a list of genes

# Define the genes of interest
gene_names = ["BRCA2", "SRY"]

# Define CubicWeb service url
url = "https://metagen.partenaires.cea.fr/metagen"

# Ask for login & password
print(url)
login, password = ask_credential()

# Define a connection: disable the security certificate check
connection = CWInstanceConnection(url, login, password, verify=False)

# Define the RQL request
rql = ("Any I Where X is Gene, X hgnc_name IN ({0}), X hgnc_name N, "
       "X gene_snps S, S rs_id I".format(repr(gene_names)[1: -1]))

# Execute the request
rset = connection.execute(rql)
pprint(rset[:10])
print("...")
snp_ids = [row[0] for row in rset]
print("Number of SNPs associated to 'BRCA2' and 'TOMM22P2': ", len(snp_ids))


#############################################################################
# Get the genotype measures of interest
# -------------------------------------
#
# We now retrieve the genotype measures of interest from a list of SNPs.
snp_data = load_plink_bed_bim_fam_dataset(plink_data, snp_ids=snp_ids,
                                          subject_ids=None, count_A1=True)
rs_ids = snp_data.sid.tolist()
records = numpy.concatenate((snp_data.iid, snp_data.val),
                            axis=1).tolist()
info = {}
for row in records:
    info[row[0]] = {}
    for key, val in zip(rs_ids, row[2:]):
        info[row[0]][key] = val
sid = info.keys()[0]
print("The genotype measures of '{0}' associated to 'BRCA2' and "
      "'TOMM22P2':".format(sid))
pprint(info[sid])
