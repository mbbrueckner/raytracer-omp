#pragma once

#include <array>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "triangle.hpp"
#include "vec3.hpp"

namespace raytrace {
namespace utils {
namespace io {

inline std::vector<Triangle> load_stl(const std::string& path,
                                      const Vec3& color) {
  std::vector<Triangle> tris;
  std::ifstream file(path);

  if (!file) {
    throw std::runtime_error("STL file not found: " + path);
  }

  std::vector<Vec3> verts;
  std::string line;
  while (std::getline(file, line)) {
    std::istringstream iss(line);
    std::string keyword;
    double x, y, z;
    if ((iss >> keyword >> x >> y >> z) && keyword == "vertex") {
      verts.emplace_back(x, y, z);
      if (verts.size() == 3) {
        tris.push_back(Triangle{verts[0], verts[1], verts[2], color});
        verts.clear();
      }
    }
  }
  return tris;
}

inline void write_ppm(const std::string& fname,
                      int width,
                      int height,
                      const std::vector<std::array<int, 3>>& pixels) {
  const std::filesystem::path path(fname);
  if (path.has_parent_path()) {
    std::filesystem::create_directories(path.parent_path());
  }
  std::ofstream file(fname);
  if (!file) {
    throw std::runtime_error("Could not open output file: " + fname);
  }
  file << "P3\n" << width << " " << height << "\n255\n";
  for (const std::array<int, 3>& px : pixels) {
    file << px[0] << " " << px[1] << " " << px[2] << "\n";
  }
}

}  // namespace io
}  // namespace utils
}  // namespace raytrace
