import bpy
import bmesh
import mathutils
import math
from bpy_extras import view3d_utils

from .object import hide_objects
from .types import Ray


#### ------------------------------ FUNCTIONS ------------------------------ ####

def extrude_face(bm, face):
    """Extrudes cutter face (created by carve operation) along view vector to create a non-manifold mesh"""

    bm.faces.ensure_lookup_table()

    # Extrude
    result = bmesh.ops.extrude_face_region(bm, geom=[bm.faces[face.index]])

    # Offset extruded vertices.
    extruded_verts = [v for v in result['geom'] if isinstance(v, bmesh.types.BMVert)]
    extruded_edges = [e for e in result['geom'] if isinstance(e, bmesh.types.BMEdge)]
    extruded_faces = [f for f in result['geom'] if isinstance(f, bmesh.types.BMFace)]

    return extruded_verts, extruded_edges, extruded_faces


def shade_smooth_by_angle(bm, mesh, angle=30):
    """Replication of "Auto Smooth" functionality: Marks faces as smooth, sharp edges (by angle) as sharp"""

    for f in bm.faces:
        f.smooth = True

    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue

        face1, face2 = edge.link_faces
        if face1.normal.length <= 0 or face2.normal.length <= 0:\
            continue

        edge_angle = math.degrees(face1.normal.angle(face2.normal))
        if edge_angle < 0:
            continue
        if edge_angle < angle:
            continue

        edge.smooth = False

    bm.to_mesh(mesh)


def are_intersecting(obj_a, obj_b):
    """Checks if bounding boxes of two given objects intersect."""

    def world_bounds(obj):
        corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        zs = [c.z for c in corners]
        return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

    (ax0, ax1), (ay0, ay1), (az0, az1) = world_bounds(obj_a)
    (bx0, bx1), (by0, by1), (bz0, bz1) = world_bounds(obj_b)

    return (
        ax1 >= bx0 and ax0 <= bx1 and
        ay1 >= by0 and ay0 <= by1 and
        az1 >= bz0 and az0 <= bz1
    )


def ensure_attribute(bm, name, domain):
    """Ensure that the attribute with the given name and domain exists on mesh."""

    if domain == 'EDGE':
        attr = bm.edges.layers.float.get(name)
        if not attr:
            attr = bm.edges.layers.float.new(name)

    elif domain == 'VERTEX':
        attr = bm.verts.layers.float.get(name)
        if not attr:
            attr = bm.verts.layers.float.new(name)

    return attr


def raycast(context, position, objects):
    """Cast a ray in the scene to get the surface on any of the given objects."""

    region = context.region
    rv3d = context.region_data
    depsgraph = context.view_layer.depsgraph

    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, position)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, position)

    # Cast Ray
    with hide_objects(context, exceptions=objects):
        hit, location, normal, index, object, matrix = context.scene.ray_cast(depsgraph, origin, direction)
        ray = Ray(hit, location, normal, index, object, matrix)

    return ray
