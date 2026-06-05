#pragma once

#include <cmath>

namespace raytrace {
namespace utils {

class Vec3 {
 public:
  double x, y, z;
  Vec3(const double x, const double y, const double z) : x(x), y(y), z(z) {}

  double dot(const Vec3& other) const {
    return x * other.x + y * other.y + z * other.z;
  }

  Vec3 cross(const Vec3& other) const {
    return {y * other.z - z * other.y,
            z * other.x - x * other.z,
            x * other.y - y * other.x};
  }

  double length() const { return std::sqrt(dot(*this)); }

  Vec3 normalize() const {
    double l = length();
    if (l == 0) return {0, 0, 0};
    return *this * (1.0 / l);
  }
};

inline Vec3 operator+(const Vec3& lhs, const Vec3& rhs) {
  return {lhs.x + rhs.x, lhs.y + rhs.y, lhs.z + rhs.z};
}

inline Vec3 operator-(const Vec3& lhs, const Vec3& rhs) {
  return {lhs.x - rhs.x, lhs.y - rhs.y, lhs.z - rhs.z};
}

inline Vec3 operator*(const Vec3& lhs, const Vec3& rhs) {
  return {lhs.x * rhs.x, lhs.y * rhs.y, lhs.z * rhs.z};
}

inline Vec3 operator*(const double scalar, const Vec3& rhs) {
  return {scalar * rhs.x, scalar * rhs.y, scalar * rhs.z};
}

inline Vec3 operator*(const Vec3& lhs, const double scalar) {
  return scalar * lhs;
}

}  // namespace utils
}  // namespace raytrace