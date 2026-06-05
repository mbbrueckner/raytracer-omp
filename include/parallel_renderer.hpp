#pragma once

#include <iostream>

#include "utils/io.hpp"
#include "utils/scene.hpp"
#include "utils/triangle.hpp"
#include "utils/vec3.hpp"

namespace raytrace {
namespace parallel {

#ifndef RAYTRACER_OUTPUT_DIR
#define RAYTRACER_OUTPUT_DIR "output"
#endif

int to_byte(double value) {
  return std::max(0, std::min(255, static_cast<int>(255 * value)));
}

void render(int width,
            int height,
            const std::string& stl_file,
            const utils::Vec3& C,
            const utils::Vec3& cam_lookat,
            const utils::Vec3& cam_up,
            const utils::Vec3& light) {
  const utils::Vec3 forward = (cam_lookat - C).normalize();
  const utils::Vec3 right = forward.cross(cam_up).normalize();
  const utils::Vec3 actual_up = right.cross(forward).normalize();
  const double fov = M_PI / 3;
  const double aspect = static_cast<double>(width) / height;

  utils::Scene scene;
  try {
    std::vector<utils::Triangle> triangles =
        utils::io::load_stl(stl_file, utils::Vec3(0.8, 0.8, 0.8));
    std::cout << "Loaded " << triangles.size() << " triangles from STL\n";
    scene.add_triangles(triangles);
  } catch (const std::runtime_error&) {
    std::cout << "STL file not found - rendering empty scene\n";
  }

  std::vector<std::array<int, 3>> pixels(static_cast<std::size_t>(width) *
                                         height);

#pragma omp parallel for collapse(2) schedule(dynamic, 16)
  for (int j = 0; j < height; ++j) {
    for (int i = 0; i < width; ++i) {
      const double x =
          (2 * (i + 0.5) / (width + 1) - 1) * std::tan(fov / 2) * aspect;
      const double y = -(2 * (j + 0.5) / (height + 1) - 1) * std::tan(fov / 2);
      const utils::Vec3 D = (right * x + actual_up * y + forward).normalize();
      const utils::Vec3 color = scene.trace(C, D, light);
      pixels[j * width + i] = {
          to_byte(color.x), to_byte(color.y), to_byte(color.z)};
    }
  }

  raytrace::utils::io::write_ppm(
      std::string(RAYTRACER_OUTPUT_DIR) + "/parallel/output.ppm",
      width,
      height,
      pixels);
}

}  // namespace parallel
}  // namespace raytrace