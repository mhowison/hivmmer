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
from importlib import resources

import hivmmer.filter as filter
from .translate import translate
from .codons import codons

__version__ = resources.read_text("hivmmer", "VERSION").strip()

# Genes are ordered by descending size.
genes = ("pol", "env", "gag", "nef", "vif", "vpr", "vpu", "tat")

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

