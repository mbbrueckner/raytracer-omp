#!/usr/bin/env python3
"""Plot benchmark results from results.csv.

Produces two figures:
  1. Runtime comparison  - serial, python, parallel(p) per resolution
  2. Speedup plot        - S(n; p) vs ideal linear + Amdahl fit

Usage:
    python benchmark/plot.py
    python benchmark/plot.py --csv benchmark/results/results.csv --out plots/
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(REPO_ROOT, "benchmark", "results", "results.csv")
DEFAULT_OUT = os.path.join(REPO_ROOT, "benchmark", "results")


def amdahl(p, alpha):
    """Amdahl's law: S(n; p) = 1 / (alpha + (1 - alpha) / p)"""
    return 1.0 / (alpha + (1.0 - alpha) / p)


def plot_runtime(df, out_dir):
    sizes = sorted(df["size"].unique())
    x = np.arange(len(sizes))
    labels = [f"{s}×{s}" for s in sizes]

    serial_times = [df[(df["impl"] == "serial")  & (df["size"] == s)]["t_best"].values[0] for s in sizes]
    python_times = [df[(df["impl"] == "python")  & (df["size"] == s)]["t_best"].values[0] for s in sizes]

    thread_counts = sorted(df[df["impl"] == "parallel"]["threads"].unique())
    parallel_by_p = {
        p: [df[(df["impl"] == "parallel") & (df["size"] == s) & (df["threads"] == p)]["t_best"].values[0]
            for s in sizes]
        for p in thread_counts
    }

    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.15
    n_bars = 2 + len(thread_counts)
    offsets = np.linspace(-(n_bars - 1) / 2, (n_bars - 1) / 2, n_bars) * width

    ax.bar(x + offsets[0], serial_times, width, label="C++ serial",  color="steelblue")
    ax.bar(x + offsets[1], python_times, width, label="Python",       color="tomato")
    for idx, p in enumerate(thread_counts):
        ax.bar(x + offsets[2 + idx], parallel_by_p[p], width,
               label=f"parallel p={p}", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Resolution")
    ax.set_ylabel("T(n; p)  [s]")
    ax.set_title("Runtime comparison")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(out_dir, "runtime.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def plot_speedup(df, out_dir):
    sizes = sorted(df[df["impl"] == "parallel"]["size"].unique())
    fig, axes = plt.subplots(1, len(sizes), figsize=(6 * len(sizes), 5))
    if len(sizes) == 1:
        axes = [axes]

    for ax, size in zip(axes, sizes):
        sub = df[(df["impl"] == "parallel") & (df["size"] == size)].sort_values("threads")
        threads  = sub["threads"].values
        speedups = sub["speedup"].values

        # Amdahl fit
        try:
            popt, _ = curve_fit(amdahl, threads, speedups, p0=[0.05], bounds=(0, 1))
            alpha_fit = popt[0]
            p_dense = np.linspace(1, threads.max(), 200)
            ax.plot(p_dense, amdahl(p_dense, alpha_fit), "r--",
                    label=f"Amdahl fit  α={alpha_fit:.3f}")
            print(f"  {size}×{size}: serial fraction α={alpha_fit:.4f}  "
                  f"(theoretical max speedup 1/α ≈ {1/alpha_fit:.1f}×)")
        except Exception as e:
            print(f"  Amdahl fit failed for {size}×{size}: {e}")

        # Ideal linear speedup
        p_range = np.array([1, threads.max()])
        ax.plot(p_range, p_range, "k:", label="ideal linear")

        # Measured
        ax.plot(threads, speedups, "bo-", label="measured S(n; p)")

        ax.set_xlabel("Threads p")
        ax.set_ylabel("S(n; p)")
        ax.set_title(f"{size}×{size}")
        ax.set_xticks(threads)
        ax.legend()
        ax.grid(alpha=0.3)

    fig.tight_layout()
    path = os.path.join(out_dir, "speedup.png")
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=DEFAULT_CSV, help="path to results.csv")
    parser.add_argument("--out", default=DEFAULT_OUT, help="output directory for plots")
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 1

    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.csv)

    print("\n Runtime plot ")
    plot_runtime(df, args.out)

    print("\n Speedup plot + Amdahl fit ")
    plot_speedup(df, args.out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
