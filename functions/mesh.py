import bpy, bmesh, mathutils
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def create_cut_rectangle(self, context):
    """Creates rectangle mesh that is going to be used by Carver tool"""

    far_limit = 10000.0
    coords = self.mouse_path[0][0], self.mouse_path[0][1]
    region = context.region
    rv3d = context.region_data
    depth_location = view3d_utils.region_2d_to_vector_3d(region, rv3d, coords)
    self.view_vector = depth_location

    # Create Mesh & Object
    faces = []
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
    for v_co in self.rectangle_coords:
        vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, v_co)
        p0 = view3d_utils.region_2d_to_location_3d(region, rv3d,v_co, vec)
        p1 = p0 + plane_direction
        faces.append(bm.verts.new(mathutils.geometry.intersect_line_plane(p0, p1, plane_point, plane_direction)))

    bm.verts.index_update()
    to_face = bm.faces.new(faces)
    bm.to_mesh(mesh)


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
