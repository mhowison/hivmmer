"""
hivmmer - An alignment and variant-calling pipeline for Illumina deep sequencing of
          HIV-1, based on the probabilistic aligner HMMER.

https://github.com/kantorlab/hivmmer

Please cite:

Howison M, Coetzer M, Kantor R. 2019. Measurement error and variant-calling in
deep Illumina sequencing of HIV. Bioinformatics 35(12): 2029-2035.
doi:10.1093/bioinformatics/bty919
"""

import os
import pandas as pd
from importlib import resources

import hivmmer.filter
import hivmmer.report
from .codons import codons
from .consensus import consensus
from .drms import drms
from .table import aa_table
from .translate import translate, translate_unambiguous

__version__ = resources.read_text("hivmmer", "VERSION").strip()

genes = ("gag", "pol", "vif", "vpr", "tat", "vpu", "env", "nef")

def copy_hmms(dst):
    """
    Copy the prepackaged HMM files for whole genome HIV alignment to the `dst` directory.
    """
    for gene in genes:
        for ext in ("h3f", "h3i", "h3m", "h3p"):
            fname = "{}.hmm.{}".format(gene, ext)
            with open(os.path.join(dst, fname), "wb") as f1:
                with resources.open_binary("hivmmer", fname) as f2:
                    f1.write(f2.read())

def list_hxb2():
    """
    Returns the ordered list of HXB2 coordinates in the prepackaged HMM files.
    """
    hxb2 = []
    for gene in genes:
        with resources.open_binary("hivmmer", "{}.hxb2.tsv".format(gene)) as f:
            hxb2 += pd.read_csv(f, sep="\t", usecols=["hxb2"]).hxb2.tolist()
    return hxb2

# vim: expandtab sw=4 ts=4
