#!/usr/bin/env python3
"""Benchmark the C++ serial and parallel ray tracer against the Python reference.

For each resolution and thread count the parallel renderer is timed over
several repetitions. Speedup S(p) = T(1)/T(p) and efficiency E(p) = S(p)/p
are computed and printed. Images are compared pixel-by-pixel against the
serial and Python reference outputs.

Usage:
    python benchmark/benchmark.py
    python benchmark/benchmark.py --sizes 512 1024 --repeats 5
    python benchmark/benchmark.py --threads 1 2 4 8 --stl resources/stl/test.stl
"""

import argparse
import csv
import numpy as np
import os
import statistics
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STL = os.path.join(REPO_ROOT, "resources", "stl", "test.stl")
PY_RENDERER = os.path.join(REPO_ROOT, "reference", "SimpleRenderWithSTL.py")
BUILD_DIR = os.path.join(REPO_ROOT, "build")
CPP_S_OUTPUT = os.path.join(REPO_ROOT, "output", "serial", "output.ppm")
CPP_P_OUTPUT = os.path.join(REPO_ROOT, "output", "parallel", "output.ppm")
PY_OUTPUT = os.path.join(REPO_ROOT, "output", "reference", "output.ppm")

FIELDS = ["impl", "size", "threads", "t_best", "t_mean", "speedup", "efficiency"]


def build_cpp() -> dict:
    """Configure & build the C++ raytracer; return binary paths."""
    print("Building C++ raytracer...")
    subprocess.run(["cmake", "-S", REPO_ROOT, "-B", BUILD_DIR],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["cmake", "--build", BUILD_DIR, "-j"],
                   check=True, stdout=subprocess.DEVNULL)

    serial_binary = os.path.join(BUILD_DIR, "raytracer_serial")
    if not os.path.isfile(serial_binary):
        raise FileNotFoundError("Could not locate 'raytracer_serial' binary.")

    parallel_binary = os.path.join(BUILD_DIR, "raytracer_parallel")
    if not os.path.isfile(parallel_binary):
        raise FileNotFoundError("Could not locate 'raytracer_parallel' binary.")

    return {"serial": serial_binary, "parallel": parallel_binary}


def bench(cmd, repeats, env=None) -> tuple:
    """Run cmd `repeats` times; return (best, mean) wall-clock seconds."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, env=env)
        times.append(time.perf_counter() - start)
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
                f"{result.stderr.decode(errors='ignore')}")
    return min(times), statistics.mean(times)


def read_ppm_pixels(path):
    with open(path) as f:
        lines = [l for l in f if not l.startswith('#')]
    # P3 header: magic, width height, maxval, then pixels
    data = ' '.join(lines[3:]).split()
    return np.array(data, dtype=int)

def images_match(path_a, path_b, path_c) -> bool:
    if not all(os.path.isfile(p) for p in (path_a, path_b, path_c)):
        return False
    a, b, c = read_ppm_pixels(path_a), read_ppm_pixels(path_b), read_ppm_pixels(path_c)
    return np.allclose(a, b, atol=1) and np.allclose(a, c, atol=1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stl", default=DEFAULT_STL,
                        help="STL file to render")
    parser.add_argument("--sizes", type=int, nargs="+", default=[256, 512, 1024],
                        help="square resolutions to benchmark (width=height)")
    parser.add_argument("--threads", type=int, nargs="+", default=[1, 2, 4, 8],
                        help="OMP_NUM_THREADS values to test")
    parser.add_argument("--repeats", type=int, default=3,
                        help="repetitions per configuration")
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print(f"STL file not found: {args.stl}", file=sys.stderr)
        return 1

    cpp_bins = build_cpp()
    cpp_s_bin = cpp_bins["serial"]
    cpp_p_bin = cpp_bins["parallel"]

    os.environ.setdefault("MPLBACKEND", "Agg")

    print(f"\nSTL: {args.stl}")
    print(f"Repeats per configuration: {args.repeats}")

    results = []

    for size in args.sizes:
        dims = [str(size), str(size)]

        print(f"\n{'='*70}")
        print(f"Resolution: {size}x{size}")
        print(f"{'='*70}\n")

        # Serial baseline 
        s_best, s_mean = bench([cpp_s_bin, args.stl, *dims], args.repeats)
        print(f"  Serial   (p=1):  best={s_best:.4f}s  mean={s_mean:.4f}s")
        results.append({
            "impl": "serial",
            "size": size,
            "threads": 1,
            "t_best": round(s_best, 6),
            "t_mean": round(s_mean, 6),
            "speedup": 1.0,
            "efficiency": 1.0,
        })

        # Python reference 
        py_best, py_mean = bench(
            [sys.executable, PY_RENDERER, args.stl, *dims, "--no-show"],
            args.repeats)
        print(f"  Python   (p=1):  best={py_best:.4f}s  mean={py_mean:.4f}s"
              f"    ->  {py_best/s_best:.2f}x vs Serial")
        results.append({
            "impl": "python",
            "size": size,
            "threads": 1,
            "t_best": round(py_best, 6),
            "t_mean": round(py_mean, 6),
            "speedup": round(py_best / s_best, 4),
            "efficiency": "",
        })

        # Parallel runs 
        parallel_results = []
        for p in args.threads:
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = str(p)
            p_best, p_mean = bench([cpp_p_bin, args.stl, *dims], args.repeats,
                                   env=env)
            vs_serial = s_best / p_best
            vs_python = py_best / p_best
            print(f"  Parallel (p={p}):  best={p_best:.4f}s  mean={p_mean:.4f}s"
                  f"    ->  {vs_serial:.2f}x vs Serial   {vs_python:.1f}x vs Python")
            parallel_results.append((p, p_best, p_mean))

        # Scaling table 
        print()
        header = (f"  {'p':>4} | {'T(p) best':>10} {'T(p) mean':>10} | "
                  f"{'S(p)':>6} {'E(p)':>6} | match")
        print(header)
        print("  " + "-" * (len(header) - 2))

        for p, p_best, p_mean in parallel_results:
            sp    = s_best / p_best
            ep    = sp / p
            match = ("yes" if images_match(CPP_S_OUTPUT, CPP_P_OUTPUT, PY_OUTPUT)
                     else "NO")
            print(f"  {p:>4} | {p_best:>9.4f}s {p_mean:>9.4f}s | "
                  f"{sp:>6.3f} {ep:>6.3f} | {match}")
            results.append({
                "impl": "parallel",
                "size": size,
                "threads": p,
                "t_best": round(p_best, 6),
                "t_mean": round(p_mean, 6),
                "speedup": round(sp, 4),
                "efficiency": round(ep, 4),
            })

    csv_path = os.path.join(REPO_ROOT, "benchmark","results", "results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults written to {csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
