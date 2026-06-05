import argparse
import math
import os
import matplotlib.pyplot as plt
import numpy as np

from dataclasses import dataclass
from typing import List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PPM = os.path.join(REPO_ROOT, "output", "reference", "output.ppm")

@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, k: float):
        return Vec3(self.x * k, self.y * k, self.z * k)

    __rmul__ = __mul__

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalize(self):
        l = self.length()
        if l == 0:
            return Vec3(0, 0, 0)
        return self * (1.0 / l)

@dataclass
class Hit:
    alpha: float
    normal: Vec3
    color: Vec3

@dataclass
class Triangle:
    T1: Vec3
    T2: Vec3
    T3: Vec3
    color: Vec3
    def intersect(self, C, D):
        eps = 1e-6
        E1   = self.T2 - self.T1
        E2   = self.T3 - self.T1
        U    = D.cross(E2)
        beta = E1.dot(U)
        if -eps < beta < eps:
            return None
        beta_inv = 1.0 / beta
        V = C - self.T1
        lambda2 = V.dot(U)*beta_inv
        if lambda2 < 0 or lambda2 > 1:
            return None
        lambda3 = D.dot(V.cross(E1))*beta_inv
        if lambda3 < 0 or lambda2 + lambda3 > 1:
            return None
        alpha = E2.dot(V.cross(E1))*beta_inv
        if alpha <= eps:
            return None
        normal = E1.cross(E2).normalize()
        return Hit(alpha, normal, self.color)

    
# -------- Scene --------
class Scene:
    def __init__(self):
        self.objects: List[Triangle] = []
       

    def add_triangles(self, objs: List[Triangle]):
        self.objects.extend(objs)

    def trace(self, C, D, Light):
        closest: Optional[Hit] = None
        for obj in self.objects:
            hit = obj.intersect(C, D)
            if hit and (closest is None or hit.alpha < closest.alpha):
                closest = hit
        if closest is None:
            return Vec3(1., 1., 1.0)
        hit_point = C + D * closest.alpha
        L = (hit_point-Light).normalize()
        diffuse = max(0.0, -closest.normal.dot(L))
        return closest.color * diffuse

# -------- STL Loader Ascii--------
def load_stl(path: str, color: Vec3):
    tris: List[Triangle] = []
    with open(path, "r", errors="ignore") as f:
        verts = []
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0] == "vertex":
                v = Vec3(float(parts[1]), float(parts[2]), float(parts[3]))
                verts.append(v)
                if len(verts) == 3:
                    tris.append(Triangle(verts[0], verts[1], verts[2], color))
                    verts = []
    return tris

# -------- Write 2D graphic --------
def write_ppm(fname, width, height, pixels):
    parent = os.path.dirname(fname)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(fname, "w") as f:
        f.write(f"P3\n{width} {height}\n255\n")
        for r, g, b in pixels:
            f.write(f"{r} {g} {b}\n")

# -------- Show 2D graphic --------
def show_image( width, height, pixels):
    image_array = np.array(pixels, dtype=np.uint8).reshape((height, width, 3))
    plt.figure(figsize=(10, 7))
    plt.imshow(image_array)
    plt.axis('off')  # Hide pixel coordinates
    #plt.title(f"Ray Traced Render ({width}x{height})")
    plt.show()


# -------- Render --------
def render(width=100, height=100, stl_file="test.stl",
           C = Vec3(20, -20, 20),
           cam_lookat=Vec3(0, 0, 0),
           cam_up=Vec3(0, 0, 1),
           light = Vec3(20, -20, 20),
           show=True):
    
    forward = (cam_lookat - C).normalize()
    right = forward.cross(cam_up).normalize()
    actual_up = right.cross(forward).normalize()
    fov = math.pi / 3
    aspect = width / height
    scene = Scene()
    try:
        tris = load_stl(stl_file, Vec3(0.8, 0.8, 0.8))
        scene.add_triangles(tris)
        print(f"Loaded {len(tris)} triangles from STL")
    except FileNotFoundError:
        print("STL file not found — rendering empty scene")

    pixels: List[Tuple[int, int, int]] = []
    for j in range(height):
        for i in range(width):
            x = (2 * (i + 0.5) / (width+1) - 1) * math.tan(fov / 2) * aspect
            y = -(2 * (j + 0.5) / (height+1) - 1) * math.tan(fov / 2)
            D = (right * x + actual_up * y + forward).normalize()
            color = scene.trace(C, D, light)
            r = max(0,min(255, int(255 * color.x)))
            g = max(0,min(255, int(255 * color.y)))
            b = max(0,min(255, int(255 * color.z)))
            pixels.append((r, g, b))

    write_ppm(OUTPUT_PPM, width, height, pixels)
    if show:
        show_image( width, height, pixels)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple STL ray tracer")
    parser.add_argument("stl_file", help="path to the STL file")
    parser.add_argument("width", type=int, nargs="?", default=600, help="image width")
    parser.add_argument("height", type=int, nargs="?", default=600, help="image height")
    parser.add_argument("--no-show", dest="show", action="store_false",
                        help="render without opening the matplotlib window")
    args = parser.parse_args()

    cam_pos=Vec3(20, -20, 10)
    cam_lookat=Vec3(0, 0, 3)
    cam_up=Vec3(0, 0, 1)
    light_source = Vec3(20, -20, 5)
    render(args.width, args.height, args.stl_file, cam_pos, cam_lookat, cam_up,
           light_source, show=args.show)
