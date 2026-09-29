"""Rebuild the paper's Table 2, Table 3 and Figure 2 from the released per-response data.

    python -m detect.evaluate [--basic-column sim_basic|sim_basic_all20]

Writes results/table2.{csv,md}, results/table3.{csv,md}, results/fig2_similarity.png and
results/paper_check.md, which compares every recomputed cell with the published value.

Averaging follows the paper: Table 2 averages are the plain mean of the per-survey rates;
Table 3 averages pool all responses of the group.
"""
import argparse
import csv

from .common import DATA, MODEL_NAMES, MODELS, POST_2022, PRE_2022, RESULTS

THRESHOLDS = [0.7, 0.75, 0.8, 0.85, 0.9]
SIG_SURVEYS_PRE = [2, 3, 4]          # survey #1 is excluded from signature-based detection

# Published values (percent), for the comparison in results/paper_check.md.
PAPER_T2 = {
    "gpt-3.5-turbo-0125": [13.91, 1.18, 7.03, 2.50, 48.71, 18.18, 24.76],
    "gpt-4-0613": [56.02, 35.88, 37.70, 39.38, 32.08, 62.12, 66.77],
    "gpt-4o-2024-08-06": [58.52, 32.94, 37.70, 35.62, 51.74, 49.49, 66.59],
    "gpt-4o-mini-2024-07-18": [22.81, 5.88, 4.79, 6.25, 58.58, 28.79, 28.46],
}
PAPER_T3 = {  # threshold -> strategy -> surveys #2..#7
    0.7: {"basic": [15.88, 7.35, 13.12, 6.09, 14.65, 15.74],
          "sentiment": [23.53, 13.10, 21.25, 7.55, 21.72, 18.04]},
    0.75: {"basic": [8.82, 4.47, 6.25, 3.00, 7.58, 14.59],
           "sentiment": [11.76, 6.39, 11.88, 3.43, 15.15, 15.74]},
    0.8: {"basic": [1.18, 1.92, 1.25, 2.23, 2.53, 13.82],
          "sentiment": [3.53, 4.47, 4.38, 2.23, 7.58, 14.78]},
    0.85: {"basic": [0.00, 0.64, 0.00, 1.89, 0.00, 11.32],
           "sentiment": [0.00, 2.24, 1.25, 1.97, 3.54, 13.05]},
    0.9: {"basic": [0.00, 0.32, 0.00, 1.29, 0.00, 4.80],
          "sentiment": [0.00, 0.96, 0.00, 1.37, 0.51, 8.64]},
}


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(k, n):
    return 100.0 * k / n if n else float("nan")


def table2(rows):
    """Share of responses each model labels AI-generated, per survey (valid replies only)."""
    out = {}
    for m in MODELS:
        per = {}
        for s in PRE_2022 + POST_2022:
            vals = [r[m] for r in rows if int(r["survey"]) == s and r[m] in ("0", "1")]
            per[s] = pct(sum(v == "1" for v in vals), len(vals))
        per["pre"] = sum(per[s] for s in PRE_2022) / len(PRE_2022)
        per["post"] = sum(per[s] for s in POST_2022) / len(POST_2022)
        out[m] = per
    return out


def table3(rows, basic_col):
    """Share of responses whose similarity reaches each threshold, per survey."""
    col = {"basic": basic_col, "sentiment": "sim_sentiment"}
    out = {}
    for th in THRESHOLDS:
        for strat, c in col.items():
            per = {}
            for s in SIG_SURVEYS_PRE + POST_2022:
                v = [float(r[c]) for r in rows if int(r["survey"]) == s]
                per[s] = pct(sum(x >= th for x in v), len(v))
            for name, group in [("pre", SIG_SURVEYS_PRE), ("post", POST_2022)]:
                v = [float(r[c]) for r in rows if int(r["survey"]) in group]
                per[name] = pct(sum(x >= th for x in v), len(v))
            out[(th, strat)] = per
    return out


def write_tables(t2, t3, counts2, counts3):
    RESULTS.mkdir(exist_ok=True)
    s2 = PRE_2022 + ["pre"] + POST_2022 + ["post"]
    head2 = [f"#{s} ({counts2[s]})" if s in counts2 else ("Avg. pre-2022" if s == "pre" else "Avg. post-2022")
             for s in s2]
    with open(RESULTS / "table2.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model"] + head2)
        for m, per in t2.items():
            w.writerow([MODEL_NAMES[m]] + [f"{per[s]:.2f}" for s in s2])
    md = ["| Model | " + " | ".join(head2) + " |", "|---|" + "--:|" * len(s2)]
    md += ["| " + MODEL_NAMES[m] + " | " + " | ".join(f"{per[s]:.2f}%" for s in s2) + " |"
           for m, per in t2.items()]
    (RESULTS / "table2.md").write_text("\n".join(md) + "\n")

    s3 = SIG_SURVEYS_PRE + ["pre"] + POST_2022 + ["post"]
    head3 = [f"#{s} ({counts3[s]})" if s in counts3 else ("Avg. pre-2022" if s == "pre" else "Avg. post-2022")
             for s in s3]
    with open(RESULTS / "table3.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "prompt"] + head3)
        for (th, strat), per in t3.items():
            w.writerow([th, strat] + [f"{per[s]:.2f}" for s in s3])
    md = ["| Threshold | Prompt | " + " | ".join(head3) + " |", "|--:|---|" + "--:|" * len(s3)]
    md += [f"| {th} | {strat} | " + " | ".join(f"{per[s]:.2f}%" for s in s3) + " |"
           for (th, strat), per in t3.items()]
    (RESULTS / "table3.md").write_text("\n".join(md) + "\n")


def paper_check(t2, t3):
    lines = ["# Recomputed values vs. the paper", "",
             "Cells that differ from the published value by more than 0.01 points.", ""]
    surveys = PRE_2022 + POST_2022
    diff2 = [(MODEL_NAMES[m], f"#{s}", PAPER_T2[m][i], t2[m][s])
             for m in MODELS for i, s in enumerate(surveys) if abs(t2[m][s] - PAPER_T2[m][i]) > 0.011]
    diff3 = [(th, strat, f"#{s}", PAPER_T3[th][strat][i], t3[(th, strat)][s])
             for (th, strat) in t3 for i, s in enumerate(SIG_SURVEYS_PRE + POST_2022)
             if abs(t3[(th, strat)][s] - PAPER_T3[th][strat][i]) > 0.011]
    lines += [f"## Table 2: {28 - len(diff2)} of 28 cells match", ""]
    if diff2:
        lines += ["| Model | Survey | Paper | Recomputed |", "|---|---|--:|--:|"]
        lines += [f"| {a} | {b} | {c:.2f} | {d:.2f} |" for a, b, c, d in diff2]
    lines += ["", f"## Table 3: {60 - len(diff3)} of 60 cells match", ""]
    if diff3:
        lines += ["| Threshold | Prompt | Survey | Paper | Recomputed |", "|--:|---|---|--:|--:|"]
        lines += [f"| {a} | {b} | {c} | {d:.2f} | {e:.2f} |" for a, b, c, d, e in diff3]
    (RESULTS / "paper_check.md").write_text("\n".join(lines) + "\n")
    return len(diff2), len(diff3)


def figure2(rows, basic_col):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import gaussian_kde

    groups = {"Pre-2022 studies": [float(r[basic_col]) for r in rows if int(r["survey"]) in SIG_SURVEYS_PRE],
              "Post-2022 studies": [float(r[basic_col]) for r in rows if int(r["survey"]) in POST_2022]}
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for (label, v), color, hatch in zip(groups.items(), ["#4C5FD5", "#D5403B"], ["", "///"]):
        ax.hist(v, bins=20, density=True, alpha=0.55, color=color, edgecolor="black", hatch=hatch, label=label)
        x = np.linspace(min(v), max(v), 200)
        ax.plot(x, gaussian_kde(v)(x), color=color, lw=1.5)
    ax.set_xlabel("Similarity")
    ax.set_ylabel("Density")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(RESULTS / "fig2_similarity.png", dpi=200)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--basic-column", default="sim_basic", choices=["sim_basic", "sim_basic_all20"],
                    help="sim_basic reproduces the paper; sim_basic_all20 uses all 20 signatures")
    args = ap.parse_args()

    zs = read_csv(DATA / "zero_shot_labels.csv")
    sims = read_csv(DATA / "similarity_scores.csv")
    counts2 = {s: sum(int(r["survey"]) == s for r in zs) for s in PRE_2022 + POST_2022}
    counts3 = {s: sum(int(r["survey"]) == s for r in sims) for s in SIG_SURVEYS_PRE + POST_2022}
    t2, t3 = table2(zs), table3(sims, args.basic_column)
    write_tables(t2, t3, counts2, counts3)
    figure2(sims, args.basic_column)
    d2, d3 = paper_check(t2, t3)
    print(f"Table 2: {28 - d2}/28 cells match the paper; Table 3: {60 - d3}/60. "
          f"Details in {RESULTS / 'paper_check.md'}")


if __name__ == "__main__":
    main()
