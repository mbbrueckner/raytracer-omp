#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "parallel_renderer.hpp"
#include "utils/vec3.hpp"

using raytrace::utils::Vec3;

int main(int argc, char* argv[]) {
  if (argc < 2) {
    throw std::invalid_argument(
        std::format("Usage: {} <stl_file> [width] [height]", argv[0]));
  }

  const std::string stl_file = argv[1];

  int width = 600;
  int height = 600;
  if (argc > 2) width = std::stoi(argv[2]);
  if (argc > 3) height = std::stoi(argv[3]);

  const Vec3 cam_pos(20, -20, 10);
  const Vec3 cam_lookat(0, 0, 3);
  const Vec3 cam_up(0, 0, 1);
  const Vec3 light_source(20, -20, 5);

  raytrace::parallel::render(
      width, height, stl_file, cam_pos, cam_lookat, cam_up, light_source);
  return 0;
}
