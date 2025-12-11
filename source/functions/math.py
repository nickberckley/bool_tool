import bpy
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def setup_grid_3d(matrix, grid_size=10.0, subdivisions=10) -> tuple[list[Vector], list[Vector]]:
    """Generates the grid of 3D points on the given matrix."""

    points = []
    indices = []

    # Calculate the step size between points & numberof points per row/column.
    step = grid_size / subdivisions
    points_per_side = subdivisions + 1

    # Start offset (to center the grid).
    start = -grid_size / 2.0

    point_map = {}
    for i in range(points_per_side):
        for j in range(points_per_side):
            # Skip the four corner points.
            is_corner = ((i == 0 or i == points_per_side - 1) and
                         (j == 0 or j == points_per_side - 1))
            if is_corner:
                continue

            local_x = start + (i * step)
            local_y = start + (j * step)
            point_local = Vector((local_x, local_y, 0.0))

            # Transform point to world space using the matrix.
            point_world = matrix @ point_local

            point_map[(i, j)] = len(points)
            points.append(point_world)

    # Generate indices for GPU batch.
    # Horizontal lines (along j axis).
    for i in range(1, points_per_side - 1):
        for j in range(points_per_side - 1):
            if (i, j) in point_map and (i, j + 1) in point_map:
                index1 = point_map[(i, j)]
                index2 = point_map[(i, j + 1)]
                indices.append((index1, index2))

    # Vertical lines (along i axis).
    for j in range(1, points_per_side - 1):
        for i in range(points_per_side - 1):
            if (i, j) in point_map and (i + 1, j) in point_map:
                index1 = point_map[(i, j)]
                index2 = point_map[(i + 1, j)]
                indices.append((index1, index2))

    return points, indices


def distance_from_point_to_segment(point, start, end) -> float:
    """
    Calculates the shortest distance between a point and a segment.
    All three inputs should be `mathutils.Vector` objects.
    This is an alternative to `mathutils.geometry.intersect_point_line`.
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    segment = end - start
    start_to_point = point - start

    # projection_along_segment
    c1 = start_to_point.dot(segment)
    if c1 <= 0:
        return (point - start).length

    # segment_length_squared
    c2 = segment.dot(segment)
    if c2 <= c1:
        return (point - end).length

    t = c1 / c2
    closest_point = start + t * segment
    distance = (point - closest_point).length

    return distance


def region_2d_to_line_3d(region, rv3d, point_2d: Vector, line_origin: Vector, line_direction: Vector) -> tuple[Vector, Vector]:
    """
    Converts a 2D screen-space point into a 3D ray and finds closest
    points between that ray and a given 3D line.
    """

    if line_origin is None or line_direction is None:
        return None, None

    # Convert the screen-space 2D point Vector into a world-space 3D ray (origin + direction).
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, point_2d)
    ray_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, point_2d)

    # Find closest points to each other on each line (second line being a ray).
    closest_points = mathutils.geometry.intersect_line_line(ray_origin,
                                                            ray_origin + ray_direction,
                                                            line_origin,
                                                            line_origin + line_direction)

    return closest_points


def region_2d_to_plane_3d(region, rv3d, point_2d: Vector, plane: tuple[Vector]) -> Vector:
    """
    Converts a 2D screen-space point into a 3D point on a plane in world-space.
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    location, normal = plane

    # Convert the screen-space 2D point Vector into a world-space 3D ray (origin + direction).
    p3_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, point_2d)
    p3_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, point_2d)

    # Intersect the point with the plane.
    p3_on_plane = mathutils.geometry.intersect_line_plane(p3_origin, # First point of line.
                                                          p3_origin + p3_direction, # Second point of line.
                                                          location,  # `plane_co` (a point on the plane).
                                                          normal)    # `plane_no` (the direction the plane is facing).

    return p3_on_plane
