#!/usr/bin/env python3
"""Benchmark the C++ serial renderer against the Python reference renderer.

For each resolution both implementations render the same scene/STL and we
measure wall-clock time over several repetitions. The produced PPM images are
compared pixel-by-pixel to make sure both renderers agree.

Usage:
    python benchmark/benchmark.py
    python benchmark/benchmark.py --sizes 100 200 400 --repeats 5
    python benchmark/benchmark.py --stl resources/stl/test.stl
"""

import argparse
import os
import statistics
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STL = os.path.join(REPO_ROOT, "resources", "stl", "test.stl")
PY_RENDERER = os.path.join(REPO_ROOT, "reference", "SimpleRenderWithSTL.py")
BUILD_DIR = os.path.join(REPO_ROOT, "build")
CPP_OUTPUT = os.path.join(REPO_ROOT, "output", "serial", "output.ppm")
PY_OUTPUT = os.path.join(REPO_ROOT, "output", "reference", "output.ppm")


def build_cpp() -> str:
    """Configure & build the C++ raytracer; return binary path."""
    print("Building C++ raytracer...")
    subprocess.run(["cmake", "-S", REPO_ROOT, "-B", BUILD_DIR],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["cmake", "--build", BUILD_DIR, "-j"],
                   check=True, stdout=subprocess.DEVNULL)
    binary = os.path.join(BUILD_DIR, "raytracer")
    if not os.path.isfile(binary):
        raise FileNotFoundError("Could not locate the built 'raytracer' binary.")
    return binary


def bench(cmd, repeats) -> tuple:
    """Run cmd `repeats` times; return (best, mean) wall-clock seconds."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE)
        times.append(time.perf_counter() - start)
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
                f"{result.stderr.decode(errors='ignore')}")
    return min(times), statistics.mean(times)


def images_match(path_a, path_b) -> bool:
    if not (os.path.isfile(path_a) and os.path.isfile(path_b)):
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        return fa.read() == fb.read()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stl", default=DEFAULT_STL, help="STL file to render")
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 200, 400],
                        help="square resolutions to benchmark (width=height)")
    parser.add_argument("--repeats", type=int, default=3,
                        help="repetitions per size (best & mean are reported)")
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print(f"STL file not found: {args.stl}", file=sys.stderr)
        return 1

    cpp_bin = build_cpp()

    # Run Python headless so matplotlib never tries to open a window.
    os.environ.setdefault("MPLBACKEND", "Agg")

    print(f"\nSTL: {args.stl}")
    print(f"Repeats per size: {args.repeats}\n")
    header = (f"{'size':>9} | {'C++ best':>9} {'C++ mean':>9} | "
              f"{'Py best':>9} {'Py mean':>9} | {'speedup':>8} | match")
    print(header)
    print("-" * len(header))

    for size in args.sizes:
        dims = [str(size), str(size)]
        cpp_best, cpp_mean = bench([cpp_bin, args.stl, *dims], args.repeats)
        py_best, py_mean = bench(
            [sys.executable, PY_RENDERER, args.stl, *dims, "--no-show"],
            args.repeats)
        speedup = py_best / cpp_best if cpp_best > 0 else float("inf")
        match = "yes" if images_match(CPP_OUTPUT, PY_OUTPUT) else "NO"
        print(f"{size:>4}x{size:<4} | {cpp_best:>8.3f}s {cpp_mean:>8.3f}s | "
              f"{py_best:>8.3f}s {py_mean:>8.3f}s | {speedup:>7.1f}x | {match}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
