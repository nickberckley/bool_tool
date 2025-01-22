import bpy, gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from .math import (
    draw_circle,
    draw_polygon,
    draw_array,
)


magic_number = 1.41
color = (0.48, 0.04, 0.04, 1.0)
secondary_color = (0.28, 0.04, 0.04, 1.0)

#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_shader(color, alpha, type, coords, size=1, indices=None):
    """Creates a batch for a draw type"""

    gpu.state.blend_set('ALPHA')

    if type == 'POINTS':
        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(size)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'POINTS', {"pos": coords}, indices=indices)

    elif type in 'LINES':
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)

    elif type in 'LINE_LOOP':
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": coords})

    if type == 'SOLID':
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

    if type == 'OUTLINE':
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        gpu.state.line_width_set(size)

    batch.draw(shader)
    gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')


def carver_shape_box(self, context, shape):
    """Shape overlay for box carver tool"""

    subdivision = self.subdivision if shape == 'CIRCLE' else 4
    rotation = 0 if shape == 'CIRCLE' else 45

    # Create Shape
    coords, indices, bounds = draw_circle(self, subdivision, rotation)
    self.verts = coords

    # Draw Shaders
    draw_shader(color, 0.4, 'SOLID', coords, size=2, indices=indices[:-2])
    if not self.rotate and not self.bevel:
        draw_shader(color, 0.6, 'OUTLINE', bounds, size=2)

    # Array
    if self.rows > 1 or self.columns > 1:
        carver_shape_array(self, coords, indices, 'SOLID')


    if self.snap:
        mini_grid(self, context)

    gpu.state.blend_set('NONE')


def carver_shape_polyline(self, context):
    """Shape overlay for polyline carver tool"""

    # Create Shape
    coords, indices, first_point, array_coords = draw_polygon(self)
    self.verts = list(dict.fromkeys(self.mouse_path))

    # Draw Shaders
    draw_shader(color, 1.0, 'POINTS', coords, size=5)
    draw_shader(color, 1.0, 'LINE_LOOP' if self.closed else 'LINES', coords, size=2)

    if self.closed and len(self.mouse_path) > 2:
        # polygon_fill
        draw_shader(color, 0.4, 'SOLID', coords, size=2, indices=indices[:-2])

    if (self.closed and len(coords) > 3) or (self.closed == False and len(coords) > 4):
        # circle_around_first_point
        draw_shader(color, 0.8, 'OUTLINE', first_point, size=3)

    # Array
    if len(self.mouse_path) > 2 and (self.rows > 1 or self.columns > 1):
        carver_shape_array(self, array_coords, indices, 'LINE_LOOP' if self.closed == False else 'SOLID')


    if self.snap:
        mini_grid(self, context)

    gpu.state.blend_set('NONE')


def carver_shape_array(self, verts, indices, shader):
    """Draws given shape for each row and column of the array"""

    rows, columns = draw_array(self, verts)
    self.duplicates = {**{f"row_{k}": v for k, v in rows.items()}, **{f"column_{k}": v for k, v in columns.items()}}

    if self.rows > 1:
        for i, duplicate in rows.items():
            draw_shader(secondary_color, 0.4, shader, duplicate, size=2, indices=indices[:-2])
    if self.columns > 1:
        for i, duplicate in columns.items():
            draw_shader(secondary_color, 0.4, shader, duplicate, size=2, indices=indices[:-2])


def mini_grid(self, context):
    """Draws snap mini-grid around the cursor based on the overlay grid"""

    region = context.region
    rv3d = context.region_data

    for i, area in enumerate(context.screen.areas):
        if area.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active
            screen_height = context.screen.areas[i].height
            screen_width = context.screen.areas[i].width

    # draw_the_snap_grid_(only_in_the_orthographic_view)
    if not space.region_3d.is_perspective:
        grid_scale = space.overlay.grid_scale
        grid_subdivisions = space.overlay.grid_subdivisions
        increment = (grid_scale / grid_subdivisions)

        # get_the_3d_location_of_the_mouse_forced_to_a_snap_value_in_the_operator
        mouse_coord = self.mouse_path[len(self.mouse_path) - 1]
        snap_loc = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_coord, (0, 0, 0))

        # add_the_increment_to_get_the_closest_location_on_the_grid
        snap_loc[0] += increment
        snap_loc[1] += increment

        # get_the_2d_location_of_the_snap_location
        snap_loc = view3d_utils.location_3d_to_region_2d(region, rv3d, snap_loc)

        # get_the_increment_value
        snap_value = snap_loc[0] - mouse_coord[0]

        # draw_lines_on_x_and_z_axis_from_the_cursor_through_the_screen
        grid_coords = [(0, mouse_coord[1]), (screen_width, mouse_coord[1]),
                        (mouse_coord[0], 0), (mouse_coord[0], screen_height)]

        grid_coords += [(mouse_coord[0] + snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] + snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] - snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] - snap_value),]

        draw_shader((1.0, 1.0, 1.0), 0.66, 'LINES', grid_coords, size=1.5)
