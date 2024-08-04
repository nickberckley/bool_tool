import bpy, gpu, mathutils, math
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils


color = (0.48, 0.04, 0.04, 1.0)

#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_shader(color, alpha, type, coords, size=1, indices=None):
    """Creates a batch for a draw type"""

    gpu.state.blend_set('ALPHA')

    if type == 'POINTS':
        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(size)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
        batch.draw(shader)

    elif type == 'LINES':
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", size)
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
        batch.draw(shader)

    if type == 'SOLID':
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # shader.bind()
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
        batch.draw(shader)

    gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')


def carver_overlay(self, context):
    """Shape (rectangle, circle) overlay for carver tool"""

    if len(self.mouse_path) > 1:
        x0 = self.mouse_path[0][0]
        y0 = self.mouse_path[0][1]
        x1 = self.mouse_path[1][0]
        y1 = self.mouse_path[1][1]

    if self.shape == 'CIRCLE':
        tris_verts, __ = draw_circle(self, x0, y0, self.subdivision, 0)
        coords = tris_verts[1:] # remove_the_vertex_in_the_center
    elif self.shape == 'BOX':
        tris_verts, __ = draw_circle(self, x0, y0, 4, 45)
        coords = tris_verts[1:] # remove_the_vertex_in_the_center
    self.verts = coords

    draw_shader(color, 0.4, 'SOLID', coords, size=2)
    if self.snap and self.move == False:
        mini_grid(self, context, color)

    gpu.state.blend_set('NONE')


def draw_circle(self, mouse_pos_x, mouse_pos_y, subdivision, rotation):
    """Returns the coordinates & indices of a circle using a triangle fan"""

    def create_2d_circle(self, step, rotation=0):
        """Create the vertices of a 2d circle at (0, 0)"""

        verts = []
        for angle in range(0, 360, int(step)):
            verts.append(math.cos(math.radians(angle + rotation)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / 2))
            verts.append(math.sin(math.radians(angle + rotation)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / 2))
            verts.append(0.0)

        verts.append(math.cos(math.radians(0.0 + rotation)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / 2))
        verts.append(math.sin(math.radians(0.0 + rotation)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / 2))
        verts.append(0.0)

        return verts

    tris_verts = []
    indices = []
    segments = int(360 / (360 / subdivision))
    # rotation = (self.mouse_path[1][1] - self.mouse_path[0][1]) / 2

    verts = create_2d_circle(self, 360 / int(subdivision), rotation)

    # Grow from the Center
    if self.origin:
        # create_the_first_vertex_at_mouse_position_for_the_center_of_the_circle
        tris_verts.append(mathutils.Vector((mouse_pos_x + self.position_y , mouse_pos_y + self.position_y)))

        # for_each_vertex_of_the_circle_add_the_mouse_position_and_the_translation
        for idx in range(int(len(verts) / 3) - 1):
            tris_verts.append(mathutils.Vector((verts[idx * 3] + mouse_pos_x + self.position_x, verts[idx * 3 + 1] + mouse_pos_y + self.position_y)))
            i1 = idx + 1
            i2 = idx + 2 if idx + 2 <= segments else 1
            indices.append((0, i1, i2))

    # Grow from the Top Left Corner
    if self.origin == False:
        min_x = min(verts[0::3]) if self.mouse_path[1][0] > mouse_pos_x else -min(verts[0::3])
        min_y = min(verts[1::3]) if self.mouse_path[1][1] > mouse_pos_y else -min(verts[1::3])

        for idx in range(len(verts) // 3):
            tris_verts.append(mathutils.Vector((
                verts[idx * 3] - min_x + mouse_pos_x + self.position_x,
                verts[idx * 3 + 1] - min_y + mouse_pos_y + self.position_y,
                verts[idx * 3 + 2])))

    return tris_verts, indices


def mini_grid(self, context, color):
    """Draws snap mini-grid around the cursor based on the overlay grid"""

    region = context.region
    rv3d = context.region_data

    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
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

        # Draw
        grid_coords += [(mouse_coord[0] + snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] + snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] + 25 + snap_value),
                        (mouse_coord[0] - snap_value, mouse_coord[1] - 25 - snap_value),
                        (mouse_coord[0] + 25 + snap_value, mouse_coord[1] - snap_value),
                        (mouse_coord[0] - 25 - snap_value, mouse_coord[1] - snap_value),]
        draw_shader(color, 0.66, 'LINES', grid_coords, size=2)
