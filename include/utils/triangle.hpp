#pragma once

#include <optional>

#include "vec3.hpp"

namespace raytrace {
namespace utils {

constexpr double eps = 1e-6;

struct Hit {
  double alpha;
  Vec3 normal, color;
};

struct Triangle {
  Vec3 T1, T2, T3, color;

  std::optional<Hit> intersect(const Vec3& C, const Vec3& D) const {
    const Vec3 E1 = T2 - T1;
    const Vec3 E2 = T3 - T1;

    const Vec3 U = D.cross(E2);
    const double beta = E1.dot(U);
    if (std::abs(beta) < eps) return std::nullopt;

    const double beta_inv = 1.0 / beta;
    const Vec3 V = C - T1;

    const double lambda2 = V.dot(U) * beta_inv;
    if (lambda2 < 0 || lambda2 > 1) return std::nullopt;

    const double lambda3 = D.dot(V.cross(E1)) * beta_inv;
    if (lambda3 < 0 || lambda2 + lambda3 > 1) return std::nullopt;

    const double alpha = E2.dot(V.cross(E1)) * beta_inv;
    if (alpha <= eps) return std::nullopt;

    const Vec3 normal = E1.cross(E2).normalize();
    return Hit{alpha, normal, color};
  }
};

}  // namespace utils
}  // namespace raytrace