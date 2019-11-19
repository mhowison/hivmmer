"""
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns
import time
from matplotlib.ticker import FixedLocator
from subprocess import run


_genes = {
    "gag": 790,
    "pol": 2085,
    "vif": 5041,
    "vpr": 5559,
    "tat": 5831,
    "vpu": 6062,
    "env": 6225,
    "nef": 8797
}
_end = 9417


def plot_coverage(codonfile, outfile, min_coverage=10):
    """
    Write a PDF plot to `outfile` showing the coverage at each HXB2 position
    based on the codon counts in `codonfile`.
    """
    codons = pd.read_csv(codonfile, sep="\t", index_col="hxb2").fillna("")
    coverage = codons.groupby(level=0)["count"].sum()

    # Initialize plot
    sns.set_style("ticks")
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    ax.set_title("Coverage", loc="left", fontsize=16)

    # Draw coverage
    xlim = (min(_genes.values()), _end)
    ax.fill_between(xlim, (min_coverage, min_coverage), color="r")
    ax.bar(coverage.index, coverage.values, width=1.0, color="k", edgecolor="none")

    # Setup x axis
    ax.set_xlabel("Gene and HXB2 Coordinates")
    ax.set_xlim(xlim)
    ax.set_xticks(list(_genes.values()))
    ax.set_xticklabels(["{} {}".format(gene[0], str(gene[1]).rjust(4)) for gene in _genes.items()], rotation=90, fontfamily="monospace")
    ax.grid(axis="x")

    # Setup y axis
    ax.set_ylabel("# of Reads")
    yticks = [0, min_coverage]
    if coverage.max() > 1.1*min_coverage:
        yticks.append(coverage.max())
    ax.set_ylim(yticks[0], yticks[-1])
    ax.set_yticks(yticks)

    # Finalize and write to file
    sns.despine(trim=True)
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()


def _plot_drms(aa, drm, outfile):
    """
    Common plotting routine for plot_drms() and plot_sdrms().
    """
    # Initialize plot
    sns.set_style("ticks")
    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(15, 6), gridspec_kw={"height_ratios": [1, 4]})

    # Serialize the X coordinates for PR, RT, IN
    aa["x"] = aa["position"]
    aa.loc[aa["region"] == "RT", "x"] = aa.loc[aa["region"] == "RT", "position"] + 100
    aa.loc[aa["region"] == "IN", "x"] = aa.loc[aa["region"] == "IN", "position"] + 541
    del aa["region"]
    del aa["position"]

    drm["x"] = drm["position"]
    drm.loc[drm["region"] == "RT", "x"] = drm.loc[drm["region"] == "RT", "position"] + 100
    drm.loc[drm["region"] == "IN", "x"] = drm.loc[drm["region"] == "IN", "position"] + 541

    # Calculate total coverage
    coverage = aa.groupby("x")["coverage"].sum()

    # Unpivot and remove zero- or low-coverage calls
    del aa["hxb2"]
    aa = aa.melt(id_vars=["x", "coverage"], var_name="variant", value_name="count")
    aa["frequency"] = aa["count"] / aa["coverage"]

    # Top coverage plot
    ymax = coverage.max()
    ylim = (0, ymax)
    ax1.set_ylim(ylim)
    ax1.set_yticks(ylim)
    ax1.set_yticklabels(list(map("{:,d}".format, ylim)))
    ax1.set_ylabel("Coverage", size=14)
    ax1.bar(coverage.index - 0.5, coverage.values, width=1.0, color="k", edgecolor="k")
    ax1.axvline(x=100, lw=1.0, color="w")
    ax1.axvline(x=541, lw=1.0, color="w")

    # Region labels
    ax1.get_xaxis().set_tick_params(direction="out", which="both", top="off")
    ax1.text(1, -0.3*ymax, "Protease", fontsize="14", weight="bold")
    ax1.text(101, -0.3*ymax, "Reverse Transcriptase", fontsize="14", weight="bold")
    ax1.text(543, -0.3*ymax, "Integrase", fontsize=14, weight="bold")

    # X axis
    margin = 1.5
    xticks = [1] + list(range(10, 100, 10)) + [101] + list(range(110, 540, 10)) + [542] + list(range(551, 811, 10))
    xlabels = [1] + list(range(10, 100, 10)) + [1] + list(range(10, 440, 10)) + [1] + list(range(10, 269, 10))
    ax2.set_xlim(1-margin, 811+margin)
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xlabels, fontsize=9, rotation=90)
    ax2.set_xlabel("AA Position", size=14)
    ax2.xaxis.set_minor_locator(FixedLocator(list(range(1, 811))))
    ax2.xaxis.set_tick_params(direction="out", which="both", top="off")

    # Y axis
    yticks = [0.1, 1, 5, 10, 20, 50, 100]
    ax2.set_ylabel("AA Frequency", size=14)
    ax2.set_yscale("log")
    ax2.set_ylim(0.09, 110)
    ax2.set_yticks(yticks)
    ax2.set_yticklabels(['%g%%' % i for i in yticks], size=14)
    ax2.get_yaxis().set_tick_params(direction="out", which="both", top="off")

    # Grid
    ax2.grid(True, which="major")
    ax2.axvline(x=100, lw=1.0, color="k")
    ax2.axvline(x=541, lw=1.0, color="k")

    # Scatterplot
    ax2.scatter(aa["x"], 100*aa["frequency"], ec="k", alpha=0.5, marker=".", fc="none")

    # Annotate DRMs
    ax2.scatter(drm["x"], 100*drm["frequency"], fc=drm["color"], marker=".", ec="none")
    ax2.scatter(drm["x"], 100*drm["frequency"], ec=drm["color"], marker="o", fc="none")

    # Finalize and write to file
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()


def plot_drms(aafile, drmfile, outfile):
    """
    Write a PDF plot to `outfile` showing DRMs, or return None if no DRMS
    were found.
    """
    aa = pd.read_excel(aafile)
    drm = pd.read_csv(drmfile)
    drm = drm[(drm.IAS == 1) | (drm.Stanford == 1)]

    if len(drm) > 0:
        drm["color"] = "r"
        drm.loc[(drm.IAS == 1) & (drm.Stanford == 0), "color"] = "b"
        drm.loc[(drm.IAS == 1) & (drm.Stanford == 1), "color"] = "m"
        _plot_drms(aa, drm, outfile)
        return outfile
    else:
        return None


def plot_sdrms(aafile, drmfile, outfile):
    """
    Write a PDF plot to `outfile` showing SDRMs, or return None if no SDRMS
    were found.
    """
    aa = pd.read_excel(aafile)
    sdrm = pd.read_csv(drmfile)
    sdrm = sdrm[sdrm.SDRM == 1]
    if len(sdrm) > 0:
        sdrm["color"] = "r"
        _plot_drms(aa, sdrm, outfile)
        return outfile
    else:
        return None


def compile(fastq1, fastq2, coveragefile, drmfile, sdrmfile, workdir, outfile):
    """
    Write a PDF report to `outfile` containing coverage, DRM, and SDRM plots.
    """

    st_fastq1 = os.stat(fastq1)
    st_fastq2 = os.stat(fastq2)

    if drmfile is not None:
        drm = r"\includegraphics[width=6.5in]{%s}" % drmfile
    else:
        drm = "None found."

    if sdrmfile is not None:
        sdrm = r"\includegraphics[width=6.5in]{%s}" % sdrmfile
    else:
        sdrm = "None found."

    tex = r"""
           \documentclass{article}[11pt]
           \usepackage[letterpaper, margin=1in]{geometry}
           \usepackage{helvet}
           \usepackage{graphicx}
           \renewcommand*\familydefault{\sfdefault}
           \begin{document}
           \subsection*{Input files}
           \begin{tabular}{ll}
           \hline
           \bf FASTQ1 & %s \\
           Size & %.1f MB \\
           Last modified & %s \\
           \hline
           \bf FASTQ2 & %s \\
           Size & %.1f MB \\
           Last modified & %s \\
           \hline
           \end{tabular}
           \subsection*{Coverage}
           \includegraphics[width=6.5in]{%s}
           \subsection*{DRMs}
           %s
           \subsection*{SDRMs}
           %s
           \end{document}
           """ % (fastq1, st_fastq1.st_size / 1048576, time.ctime(st_fastq1.st_mtime),
                  fastq2, st_fastq2.st_size / 1048576, time.ctime(st_fastq2.st_mtime),
                  coveragefile, drm, sdrm)

    # Write tex to flie
    with open(os.path.join(workdir, "report.tex"), "w") as f:
        f.write(tex)

    # Run pdflatex
    with open(os.path.join(workdir, "pdflatex.log"), "w") as f:
        run(["pdflatex", "-jobname=" + outfile, "report.tex"],
            stdout=f, stderr=f, check=True, cwd=workdir)


# vim: expandtab sw=4 ts=4
