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
CPP_S_OUTPUT = os.path.join(REPO_ROOT, "output", "serial", "output.ppm")
CPP_P_OUTPUT = os.path.join(REPO_ROOT, "output", "parallel", "output.ppm")
PY_OUTPUT = os.path.join(REPO_ROOT, "output", "reference", "output.ppm")


def build_cpp() -> dict:
    """Configure & build the C++ raytracer; return binary path."""
    print("Building C++ raytracer...")
    subprocess.run(["cmake", "-S", REPO_ROOT, "-B", BUILD_DIR],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["cmake", "--build", BUILD_DIR, "-j"],
                   check=True, stdout=subprocess.DEVNULL)
    
    serial_binary = os.path.join(BUILD_DIR, "raytracer_serial")
    if not os.path.isfile(serial_binary):
        raise FileNotFoundError("Could not locate the built 'raytracer_serial' binary.")
    
    parallel_binary = os.path.join(BUILD_DIR, "raytracer_parallel")
    if not os.path.isfile(parallel_binary):
        raise FileNotFoundError("Could not locate the built 'raytracer_parallel' binary.")
    return {
        "serial"  : serial_binary,
        "parallel": parallel_binary
        }


def speedup(slow, fast) -> float:
    """How many times faster `fast` is than `slow` (∞ if fast is 0s)."""
    return slow / fast if fast > 0 else float("inf")


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


def images_match(path_a, path_b, path_c) -> bool:
    if not (os.path.isfile(path_a) and os.path.isfile(path_b)and os.path.isfile(path_c)):
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb, open(path_c, "rb") as fc:
        return fa.read() == fb.read() == fc.read()


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

    cpp_bins = build_cpp()
    cpp_s_bin = cpp_bins["serial"]
    cpp_p_bin = cpp_bins["parallel"]

    # Run Python headless so matplotlib never tries to open a window.
    os.environ.setdefault("MPLBACKEND", "Agg")

    print(f"\nSTL: {args.stl}")
    print(f"Repeats per size: {args.repeats}\n")
    header = (f"{'size':>9} | "
              f"{'C++ serial (best/mean)':>22} | "
              f"{'C++ parallel (best/mean)':>24} | "
              f"{'Python (best/mean)':>20} | "
              f"{'S/Py':>6} {'P/Py':>6} {'P/S':>6} | match")
    print(header)
    print("-" * len(header))

    for size in args.sizes:
        dims = [str(size), str(size)]
        cpp_s_best, cpp_s_mean = bench([cpp_s_bin, args.stl, *dims], args.repeats)
        cpp_p_best, cpp_p_mean = bench([cpp_p_bin, args.stl, *dims], args.repeats)
        py_best, py_mean = bench(
            [sys.executable, PY_RENDERER, args.stl, *dims, "--no-show"],
            args.repeats)
        # Three meaningful ratios: each C++ build against the Python
        # reference, and the parallel build against the serial one (the
        # actual OpenMP scaling).
        serial_vs_py   = speedup(py_best, cpp_s_best)
        parallel_vs_py = speedup(py_best, cpp_p_best)
        parallel_vs_serial = speedup(cpp_s_best, cpp_p_best)
        match = "yes" if images_match(CPP_S_OUTPUT, CPP_P_OUTPUT, PY_OUTPUT) else "NO"
        print(f"{size:>4}x{size:<4} | "
              f"{cpp_s_best:>9.3f}s {cpp_s_mean:>9.3f}s  | "
              f"{cpp_p_best:>10.3f}s {cpp_p_mean:>10.3f}s  | "
              f"{py_best:>8.3f}s {py_mean:>8.3f}s  | "
              f"{serial_vs_py:>5.1f}x {parallel_vs_py:>5.1f}x "
              f"{parallel_vs_serial:>5.1f}x | {match}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
