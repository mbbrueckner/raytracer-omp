#pragma once

#include <algorithm>
#include <cmath>
#include <vector>

#include "triangle.hpp"
#include "vec3.hpp"

namespace raytrace {
namespace utils {

class Scene {
 private:
  std::vector<Triangle> objects;

 public:
  Scene() = default;
  void add_triangles(const std::vector<Triangle>& triangles) {
    objects.insert(objects.end(), triangles.begin(), triangles.end());
  }

  Vec3 trace(const Vec3& C, const Vec3& D, const Vec3& Light) const {
    std::optional<Hit> closest = std::nullopt;

    for (const Triangle& obj : objects) {
      std::optional<Hit> hit = obj.intersect(C, D);

      if (hit.has_value() &&
          (!closest.has_value() || hit.value().alpha < closest.value().alpha))
        closest.swap(hit);
    }
    if (!closest.has_value()) return Vec3(1., 1., 1.);

    const Vec3 hit_point = C + D * closest.value().alpha;
    const Vec3 L = (hit_point - Light).normalize();
    const double diffuse = std::max(0.0, -closest.value().normal.dot(L));

    return closest.value().color * diffuse;
  }
};

}  // namespace utils
}  // namespace raytrace