import bpy
import bmesh
import mathutils
from contextlib import contextmanager
from .. import __package__ as base_package


#### ------------------------------ FUNCTIONS ------------------------------ ####

def add_boolean_modifier(self, context, obj, cutter, mode, solver, pin=False, redo=True):
    "Adds boolean modifier with specified cutter and properties to a single object"

    if bpy.app.version < (5, 0, 0) and solver == 'FLOAT':
        solver = 'FAST'

    prefs = context.preferences.addons[base_package].preferences

    modifier = obj.modifiers.new("boolean_" + cutter.name, 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver

    # Set solver options (inherited from operator properties).
    if redo:
        modifier.material_mode = self.material_mode
        modifier.use_self = self.use_self
        modifier.use_hole_tolerant = self.use_hole_tolerant
        modifier.double_threshold = self.double_threshold

    if prefs.show_in_editmode:
        modifier.show_in_editmode = True

    # Move modifier to the index 0 (make it first in the stack).
    if pin:
        index = obj.modifiers.find(modifier.name)
        obj.modifiers.move(index, 0)

    return modifier


def apply_modifiers(context, obj, modifiers: list, single_user=False):
    """
    Apply modifiers on object.
    Instead of using `bpy.ops.object.modifier_apply`, this function uses
    `bpy.data.meshes.new_from_object` built-in function to create a temporary
    mesh from the evaluated object (basically with visible modifiers applied).
    Temporary mesh is then transferred to objects mesh with `bmesh`.

    This method is up to 2x faster, although it's considered experimental
    and may fail in some cases, so a fallback to `bpy.ops.object.modifier_apply` is kept.
    """

    try:
        with hide_modifiers(obj, excluding=modifiers):
            # Create a temporary mesh from evaluated object.
            evaluated_obj = obj.evaluated_get(context.evaluated_depsgraph_get())
            temp_data = bpy.data.meshes.new_from_object(evaluated_obj)

            # Create `bmesh` from temporary mesh and update edit mesh.
            if context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                bm.clear()
                bm.from_mesh(temp_data)
                bmesh.update_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(temp_data)
                bm.to_mesh(obj.data)
            bm.free()
            evaluated_obj.to_mesh_clear()

            # Remove modifiers and purge temporary mesh.
            bpy.data.meshes.remove(temp_data)
            for mod in modifiers:
                obj.modifiers.remove(mod)

            # Remove shape keys if there are any.
            # (after above operations none of the shape keys have any effect).
            if obj.data.shape_keys:
                obj.shape_key_clear()

    # Use `bpy.ops` operator to apply modifiers if above fails.
    except Exception as e:
        print("Error applying modifiers with `bmesh` method:", e, "falling back to `bpy.ops` method")

        context_override = {"object": obj, "mode": 'OBJECT'}
        with context.temp_override(**context_override):
            # Apply shape keys if there are any.
            if obj.data.shape_keys:
                bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

            for mod in modifiers:
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    if single_user:
                        # Make single user and then try applying.
                        context.active_object.data = context.active_object.data.copy()
                        bpy.ops.object.modifier_apply(modifier=mod.name)


def set_cutter_properties(context, canvas, cutter, mode, parent=True, hide=False, collection=True):
    """Ensures cutter is properly set: has right properties, is hidden, in a collection & parented"""

    prefs = context.preferences.addons[base_package].preferences

    # Hide Cutters
    cutter.hide_render = True
    cutter.display_type = 'WIRE' if prefs.wireframe else 'BOUNDS'
    cutter.lineart.usage = 'EXCLUDE'
    object_visibility_set(cutter, value=False)
    if hide:
        cutter.hide_set(True)

    # parent_to_active_canvas
    if parent and cutter.parent == None:
        cutter.parent = canvas
        cutter.matrix_parent_inverse = canvas.matrix_world.inverted()

    # Cutters Collection
    if collection:
        cutters_collection = ensure_collection(context)
        if cutters_collection not in cutter.users_collection:
            cutters_collection.objects.link(cutter)
        if cutter.booleans.carver and parent == False:
            context.collection.objects.unlink(cutter)

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


def change_parent(object, parent):
    """Changes or removes parent from cutter object while keeping the transformation"""

    matrix_copy = object.matrix_world.copy()
    object.parent = parent
    object.matrix_world = matrix_copy


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


def set_object_origin(obj, position=False):
    """Sets object origin to given position by shifting vertices"""

    # default_to_center_of_bounding_box_if_no_position_provided
    if position == False:
        position = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())

    mat = mathutils.Matrix.Translation(position - obj.location)
    obj.location = position
    obj.data.transform(mat.inverted())
    obj.data.update()


@contextmanager
def hide_modifiers(obj, excluding: list):
    """Hides all modifiers of a given object in viewport except those in excluding list"""

    visible_modifiers = []
    for mod in obj.modifiers:
        if mod in excluding:
            continue
        if mod.show_viewport == True:
            visible_modifiers.append(mod)
            mod.show_viewport = False

    try:
        yield
    finally:
        for mod in visible_modifiers:
            mod.show_viewport = True
