import bpy
import bmesh
import mathutils
from contextlib import contextmanager
from .. import __package__ as base_package


#### ------------------------------ FUNCTIONS ------------------------------ ####

def set_cutter_properties(context, cutter, mode, display='BOUNDS', collection=True):
    """Ensures cutter is properly set: has right properties, is hidden, in a collection & parented"""

    # Hide Cutters
    cutter.hide_render = True
    cutter.display_type = display
    cutter.lineart.usage = 'EXCLUDE'
    object_visibility_set(cutter, value=False)

    # Cutters Collection
    if collection:
        cutters_collection = ensure_collection(context)
        if cutters_collection not in cutter.users_collection:
            cutters_collection.objects.link(cutter)

    # add_boolean_property
    cutter.booleans.cutter = mode.capitalize()


def object_visibility_set(obj, value=False):
    "Sets object visibility properties to either True or False"

    obj.visible_camera = value
    obj.visible_diffuse = value
    obj.visible_glossy = value
    obj.visible_shadow = value
    obj.visible_transmission = value
    obj.visible_volume_scatter = value


def convert_to_mesh(context, obj):
    "Converts active object into mesh (applying all modifiers and shape keys in process)"

    # store_selection
    stored_active = context.active_object
    stored_selection = context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')

    # Convert
    obj.select_set(True)
    context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')

    # restore_selection
    for obj in stored_selection:
        obj.select_set(True)
    context.view_layer.objects.active = stored_active


def ensure_collection(context):
    """Checks the existance of boolean cutters collection and creates it if it doesn't exist"""

    prefs = context.preferences.addons[base_package].preferences

    collection_name = prefs.collection_name
    cutters_collection = bpy.data.collections.get(collection_name)

    if cutters_collection is None:
        cutters_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(cutters_collection)
        cutters_collection.hide_render = True
        cutters_collection.color_tag = 'COLOR_01'
        # cutters_collection.hide_viewport = True
        # context.view_layer.layer_collection.children[collection_name].exclude = True

    return cutters_collection


def delete_empty_collection():
    """Removes boolean cutters collection if it has no more objects in it"""

    prefs = bpy.context.preferences.addons[base_package].preferences

    collection = bpy.data.collections.get(prefs.collection_name)
    if collection and not collection.objects:
        bpy.data.collections.remove(collection)


def delete_cutter(cutter):
    """Deletes cutter object and purges it's mesh data"""

    orphaned_mesh = cutter.data
    bpy.data.objects.remove(cutter)
    if orphaned_mesh.users == 0:
        bpy.data.meshes.remove(orphaned_mesh)


def change_parent(obj, parent, force=False, inverse=False):
    """Changes or removes parent from cutter object while keeping the transformation"""

    if obj.parent is not None:
        if not force:
            return

    matrix_copy = obj.matrix_world.copy()
    obj.parent = parent
    if inverse:
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = matrix_copy


def create_slice(context, canvas, modifier=False):
    """Creates copy of canvas to be used as slice"""

    slice = canvas.copy()
    slice.data = canvas.data.copy()
    slice.name = slice.data.name = canvas.name + "_slice"
    change_parent(slice, canvas)

    # Set Boolean Properties
    if modifier == True:
        slice.booleans.canvas = True
        slice.booleans.slice = True
        slice.booleans.slice_of = canvas

    # Add to Canvas Collections
    for coll in canvas.users_collection:
        coll.objects.link(slice)

    # add_slices_to_local_view
    if context.space_data.local_view:
        slice.local_view_set(context.space_data, True)

    return slice


def set_object_origin(obj, bm, point='CENTER', custom=None):
    """Sets object origin to given position by shifting vertices"""

    # Center of the bounding box.
    if point == 'CENTER':
        position_local = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
        position_world = obj.matrix_world @ position_local

    elif point == 'CUSTOM':
        position_local = custom
        position_world = obj.matrix_world @ custom

    mat = mathutils.Matrix.Translation(position_local)
    bmesh.ops.transform(bm, matrix=mat.inverted(), verts=bm.verts)
    bm.to_mesh(obj.data)

    obj.location = position_world


@contextmanager
def hide_objects(context, exceptions: list):
    """Hides objects during the context, and restores their visibility afterwards."""

    hidden_objects = []
    for obj in context.scene.objects:
        if obj in exceptions:
            continue
        if obj.hide_get() == False:
            hidden_objects.append(obj)
            obj.hide_set(True)

    try:
        yield

    finally:
        for obj in hidden_objects:
            obj.hide_set(False)
