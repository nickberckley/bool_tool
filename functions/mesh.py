import bpy, bmesh, mathutils
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def create_cutter_shape(self, context):
    """Creates flat mesh from the vertices provided in `self.verts` (which is created by `carver_overlay`)"""

    far_limit = 10000.0
    coords = self.mouse_path[0][0], self.mouse_path[0][1]
    region = context.region
    rv3d = context.region_data
    depth_location = view3d_utils.region_2d_to_vector_3d(region, rv3d, coords)
    self.view_vector = depth_location

    faces = []
    vertices = []
    loc = []

    # Create Mesh & Object
    mesh = bpy.data.meshes.new('cutter_cube')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    obj = bpy.data.objects.new('cutter_cube', mesh)
    self.cutter = obj
    context.collection.objects.link(obj)

    # Orientation: VIEW
    plane_direction = depth_location.normalized()

    # Depth
    if self.depth == 'CURSOR':
        plane_point = context.scene.cursor.location
    elif self.depth == 'VIEW':
        plane_point = mathutils.Vector((0.0, 0.0, 0.0))


    # find_the_intersection_of_a_line_going_through_each_vertex_and_the_infinite_plane
    if self.shape == 'POLYLINE':
        for idx, vert in enumerate(list(dict.fromkeys(self.mouse_path))): # use_dict_to_remove_doubles
            vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, vert)
            p0 = view3d_utils.region_2d_to_location_3d(region, rv3d, vert, vec)
            p1 = p0 + plane_direction
            loc.append(mathutils.geometry.intersect_line_plane(p0, p1, plane_point, plane_direction))
            vertices.append(bm.verts.new(loc[idx]))

            if idx > 0:
                bm.edges.new([vertices[idx-1],vertices[idx]])

            faces.append(vertices[idx])
    else:
        for vert in self.verts:
            vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, vert)
            p0 = view3d_utils.region_2d_to_location_3d(region, rv3d, vert, vec)
            p1 = p0 + plane_direction
            faces.append(bm.verts.new(mathutils.geometry.intersect_line_plane(p0, p1, plane_point, plane_direction)))

    bm.verts.index_update()
    if self.shape == 'POLYLINE' and len(vertices) > 1:
        bm.edges.new([vertices[-1], vertices[0]])
    to_face = bm.faces.new(faces)


    # ARRAY
    rows = {}
    if self.rows > 1:
        screen_offset = ((self.gap_rows * 100), 0)
        for i in range(self.rows - 1):
            accumulated_offset = (screen_offset[0] * (i + 1), screen_offset[1] * (i + 1))
            rows[i] = duplicate_cutter_shape(self, bm, to_face, accumulated_offset)

    if self.columns > 1:
        screen_offset = ((0, -self.gap_rows * 100))
        for i in range(self.columns - 1):
            accumulated_offset = (screen_offset[0] * (i + 1), screen_offset[1] * (i + 1))
            duplicate_cutter_shape(self, bm, to_face, accumulated_offset)
            for i, row in rows.items():
                duplicate_cutter_shape(self, bm, row, accumulated_offset)

    bm.to_mesh(mesh)


def duplicate_cutter_shape(self, bm, face, offset):
    """Creates array from duplicated cutter shapes"""

    def screen_space_offset_to_world_offset(region, rv3d, screen_offset):
        screen_offset_vector = mathutils.Vector(screen_offset)
        center_2d = mathutils.Vector((region.width / 2, region.height / 2))
        
        # convert_center_and_offset_to_world_space
        start_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, center_2d, (0, 0, 0))
        end_2d = center_2d + screen_offset_vector
        end_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, end_2d, (0, 0, 0))

        world_offset = end_3d - start_3d
        return world_offset

    # screen-space_offset
    region = bpy.context.region
    rv3d = bpy.context.space_data.region_3d
    offset = screen_space_offset_to_world_offset(region, rv3d, offset)

    new_verts = []
    for vert in face.verts:
        new_vert = bm.verts.new(vert.co + offset)
        new_verts.append(new_vert)
    duplicated_face = bm.faces.new(new_verts)

    return duplicated_face


def extrude(self, mesh):
    """Extrudes cutter face (created by carve operation) along view vector to create a non-manifold mesh"""

    bm = bmesh.new()
    bm.from_mesh(mesh)
    faces = [f for f in bm.faces]

    # move_the_mesh_towards_view
    box_bounding = combined_bounding_box(self.selected_objects)
    for face in faces:
        for vert in face.verts:
            # vert.co += -self.view_vector * box_bounding
            vert.co += -self.view_vector * box_bounding

    # extrude_the_face
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts_extruded = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]
    for v in verts_extruded:
        v.co += self.view_vector * box_bounding * 2

    # correct_normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()


def combined_bounding_box(objects):
    """Calculate the combined bounding box of multiple objects."""
    
    min_corner = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_corner = mathutils.Vector((-float('inf'), -float('inf'), -float('inf')))

    for obj in objects:
        # Transform the bounding box corners to world space
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]

        for corner in bbox_corners:
            min_corner.x = min(min_corner.x, corner.x)
            min_corner.y = min(min_corner.y, corner.y)
            min_corner.z = min(min_corner.z, corner.z)
            max_corner.x = max(max_corner.x, corner.x)
            max_corner.y = max(max_corner.y, corner.y)
            max_corner.z = max(max_corner.z, corner.z)

    # Calculate the diagonal of the combined bounding box
    bounding_box_diag = (max_corner - min_corner).length
    return bounding_box_diag
