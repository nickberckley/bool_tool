import bpy
import gpu
import math
import mathutils
from bpy_extras import view3d_utils
from mathutils import Vector
from gpu_extras.batch import batch_for_shader


#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_shader(type, color, alpha, coords, size=1, indices=None):
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
        gpu.state.depth_test_set('NONE')
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (color[0], color[1], color[2], alpha))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

    batch.draw(shader)
    gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')


def draw_bmesh_faces(faces, world_matrix):
    """
    Get world-space vertex pairs and indices from `bmesh` face. To be used in GPU batch.
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    if not faces:
        return None, None

    vertices = []
    indices = []

    vert_index_map = {}
    vert_count = 0
    for face in faces:
        face_indices = []

        # Collect unique vertices only (avoid storing verts that are shared by faces multiple times).
        # (Iterating over face corners because unlike `face.verts` they're ordered).
        for loop in face.loops:
            vert = loop.vert
            co = world_matrix @ Vector(vert.co)

            if vert not in vert_index_map:
                vertices.append(co)
                vert_index_map[vert] = vert_count
                face_indices.append(vert_count)
                vert_count += 1
            else:
                face_indices.append(vert_index_map[vert])

        # Triangulate face and map local indices to global vertex indices.
        if len(face_indices) >= 3:
            try:
                face_verts_co = [vertices[idx] for idx in face_indices]
                tris = mathutils.geometry.tessellate_polygon([face_verts_co])
                for tri in tris:
                    indices.append((face_indices[tri[0]], face_indices[tri[1]], face_indices[tri[2]]))
            except:
                # Fallback to simple fan triangulation if tessellation fails.
                for i in range(1, len(face_indices) - 1):
                    indices.append((face_indices[0], face_indices[i], face_indices[i + 1]))

    return vertices, indices


def draw_bmesh_edges(edges, world_matrix):
    """Convert bmesh edges into world-space vertex pairs to be used in GPU batch."""

    if not edges:
        return None

    vertices = []
    for edge in edges:
        v1 = world_matrix @ edge.verts[0].co
        v2 = world_matrix @ edge.verts[1].co
        vertices.append(v1)
        vertices.append(v2)

    return vertices


def draw_circle_around_point(context, obj, vert, radius, segments):
    """
    Draws the screen-aligned circle around given vertex of the object.
    Returns the list of vertices for GPU batch.
    """

    region = context.region
    rv3d = context.region_data
    vert_world = obj.matrix_world @ vert.co
    radius = min(radius, 25)

    vertices = []
    for i in range(segments + 1):
        angle = i * (2 * math.pi / segments)

        # Calculate offset and vertex position in screen-space.
        offset_x = radius * math.cos(angle)
        offset_y = radius * math.sin(angle)
        vert_screen = view3d_utils.location_3d_to_region_2d(region, rv3d, vert_world)

        if vert_screen:
            # Add offset in screen-space and convert back to world-space.
            circle_screen = Vector((vert_screen.x + offset_x, vert_screen.y + offset_y))
            circle_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, circle_screen, vert_world)
            vertices.append(circle_3d)

    return vertices


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
