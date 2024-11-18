import bpy, mathutils, math
from bpy_extras import view3d_utils
from .draw import get_bounding_box_coords
from .poll import is_linked


#### ------------------------------ FUNCTIONS ------------------------------ ####

def cursor_snap(self, context, event, mouse_pos):
    """Find the closest position on the overlay grid and snap the mouse on it"""

    region = context.region
    rv3d = context.region_data

    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active

    # get_the_grid_overlay
    grid_scale = space.overlay.grid_scale
    grid_subdivisions = space.overlay.grid_subdivisions

    # use_grid_scale_and_subdivision_to_get_the_increment
    increment = (grid_scale / grid_subdivisions)
    half_increment = increment / 2

    # convert_2d_location_of_the_mouse_in_3d
    for index, loc in enumerate(reversed(mouse_pos)):
        mouse_loc_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc, (0, 0, 0))

        # get_the_remainder_from_the_mouse_location_and_the_ratio (test_if_the_remainder_>_to_the_half_of_the_increment)
        for i in range(3):
            modulo = mouse_loc_3d[i] % increment
            if modulo < half_increment:
                modulo = -modulo
            else:
                modulo = increment - modulo

            # add_the_remainder_to_get_the_closest_location_on_the_grid
            mouse_loc_3d[i] = mouse_loc_3d[i] + modulo

        snap_loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, mouse_loc_3d)

        # replace_the_last_mouse_location_by_the_snapped_location
        if len(self.mouse_path) > 0:
            self.mouse_path[len(self.mouse_path) - (index + 1) ] = tuple(snap_loc_2d)


def is_inside_selection(context, obj, rect_min, rect_max):
    """Checks if the bounding box of an object intersects with the selection bounding box"""

    region = context.region
    rv3d = context.space_data.region_3d

    bound_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    bound_corners_2d = [view3d_utils.location_3d_to_region_2d(region, rv3d, corner) for corner in bound_corners]

    # check_if_2d_point_is_inside_rectangle_(defined_by_min_and_max_points)
    for corner_2d in bound_corners_2d:
        if corner_2d and (rect_min.x <= corner_2d.x <= rect_max.x and rect_min.y <= corner_2d.y <= rect_max.y):
            return True
    
    # check_if_any_part_of_the_bounding_box_intersects_the_selection_rectangle
    min_x = min(corner_2d.x for corner_2d in bound_corners_2d if corner_2d)
    max_x = max(corner_2d.x for corner_2d in bound_corners_2d if corner_2d)
    min_y = min(corner_2d.y for corner_2d in bound_corners_2d if corner_2d)
    max_y = max(corner_2d.y for corner_2d in bound_corners_2d if corner_2d)

    return not (max_x < rect_min.x or min_x > rect_max.x or max_y < rect_min.y or min_y > rect_max.y)


def selection_fallback(self, context, objects, include_cutters=False):
    """Selects mesh objects that fall inside given 2d rectangle coordinates"""
    """Used to get exactly which objects should be cut and avoid adding and applying unnecessary modifiers"""
    """NOTE: bounding box isn't always returning correct results for objects, but full surface check would be too expensive"""

    # convert_2d_rectangle_coordinates_to_world_coordinates
    if self.origin == 'EDGE':
        if self.shape == 'POLYLINE':
            x_values = [point[0] for point in self.mouse_path]
            y_values = [point[1] for point in self.mouse_path]
            rect_min = mathutils.Vector((min(x_values), min(y_values)))
            rect_max = mathutils.Vector((max(x_values), max(y_values)))
        else:
            rect_min = mathutils.Vector((min(self.mouse_path[0][0], self.mouse_path[1][0]),
                                         min(self.mouse_path[0][1], self.mouse_path[1][1])))
            rect_max = mathutils.Vector((max(self.mouse_path[0][0], self.mouse_path[1][0]),
                                         max(self.mouse_path[0][1], self.mouse_path[1][1])))

    elif self.origin == 'CENTER':
        # ensure_bounding_box_(needed_when_array_is_set_before_original_is_drawn)
        if len(self.center_origin) == 0:
            get_bounding_box_coords(self, self.verts)

        rect_min = mathutils.Vector((min(self.center_origin[0][0], self.center_origin[1][0]),
                                     min(self.center_origin[0][1], self.center_origin[1][1])))
        rect_max = mathutils.Vector((max(self.center_origin[0][0], self.center_origin[1][0]),
                                     max(self.center_origin[0][1], self.center_origin[1][1])))

    # ARRAY
    if self.rows > 1:
        rect_max.x = rect_min.x + (rect_max.x - rect_min.x) * self.rows + (self.rows_gap * (self.rows - 1))
    if self.columns > 1:
        rect_min.y = rect_max.y - (rect_max.y - rect_min.y) * self.columns - (self.columns_gap * (self.columns - 1))

    intersecting_objects = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        if obj == self.cutter:
            continue
        if (include_cutters == False) and obj.booleans.cutter != "":
            continue
        if (self.mode == 'DESTRUCTIVE') and obj.data.shape_keys:
            self.report({'ERROR'}, f"Modifiers can't be applied to {obj.name} because it has shape keys")
            continue
        if is_linked(context, obj):
            self.report({'ERROR'}, f"{obj.name} is linked and can not be carved")
            continue

        if is_inside_selection(context, obj, rect_min, rect_max):
            intersecting_objects.append(obj)

    return intersecting_objects


def raycast_from_cursor(region, rv3d, obj, xy):
    """Casts rays from cursor position and picks out mesh object (and its normals) underneath it"""
    # This function and everything down below is a (modified) code from '3D Hair Brush' by VFX Grace (GPL license)

    coords = xy[0] - region.x, xy[1] - region.y
    clamp = None
    if not rv3d.is_perspective and rv3d.view_perspective != 'CAMERA':
        clamp = rv3d.view_distance * 2

    # get_the_ray_from_the_viewport_and_mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coords)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coords, clamp=clamp)
    ray_target = ray_origin + view_vector

    # get_the_ray_relative_to_the_object
    obj_matrix = obj.matrix_world.copy()
    matrix_inv = obj_matrix.inverted()
    ray_origin_obj = matrix_inv @ ray_origin
    ray_target_obj = matrix_inv @ ray_target
    ray_direction_obj = ray_target_obj - ray_origin_obj

    # Raycast
    result, location, normal, index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

    return result, location, normal


def calc_unprojected_radius(obj_matrix, location, region, rv3d, pixel_rad):
    """"""

    world_location = obj_matrix @ location
    perspective_matrix = rv3d.perspective_matrix.copy()
    z_factor = math.fabs(world_location.dot(perspective_matrix[3].xyz) + perspective_matrix[3][3])
    if z_factor < 1e-6:
        z_factor = 1.0

    dx = 2.0 * pixel_rad * z_factor / region.width
    perspective_matrix.invert()
    delta = mathutils.Vector((perspective_matrix[0][0] * dx, perspective_matrix[1][0] * dx, perspective_matrix[2][0] * dx))
    radius_3d = delta.length

    scale = (obj_matrix.to_3x3() @ mathutils.Vector((1, 1, 1)).normalized()).length
    if scale == 0:
        scale = 1.0

    return radius_3d, radius_3d / scale


def calc_projected_radius(obj_matrix, location, region, rv3d, radius):
    """"""

    def location_3d_to_vector_3d(rv3d, location):
        if rv3d.is_perspective:
            p2 = rv3d.view_matrix @ mathutils.Vector((*location, 1.0))
            p2.xyz *= 2.0
            p2 = rv3d.view_matrix.inverted() @ p2
            return (location - p2.xyz).normalized()

        return rv3d.view_matrix.inverted().col[2].xyz.normalized()

    view = location_3d_to_vector_3d(rv3d, location)
    non_orthographic = view.copy()

    if math.fabs(non_orthographic.x) < 0.1:
        non_orthographic.x += 1.0
    elif math.fabs(non_orthographic.y) < 0.1:
        non_orthographic.y += 1.0
    else:
        non_orthographic.z += 1.0

    ortho = non_orthographic.cross(view).normalized()
    offset = location + ortho * radius
    p1 = view3d_utils.location_3d_to_region_2d(region, rv3d, location)
    p2 = view3d_utils.location_3d_to_region_2d(region, rv3d, offset)

    if p1 and p2:
        scale = (obj_matrix.to_3x3() @ mathutils.Vector((1, 1, 1)).normalized()).length
        if scale == 0:
            scale = 1.0

        return int((p1 - p2).length * scale)

    return 0
