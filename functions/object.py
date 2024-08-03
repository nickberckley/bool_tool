import bpy, bmesh
from .. import __package__ as base_package


#### ------------------------------ FUNCTIONS ------------------------------ ####

def add_boolean_modifier(canvas, cutter, mode, solver, apply=False, pin=False):
    "Adds boolean modifier with specified cutter and properties to a single object"

    prefs = bpy.context.preferences.addons[base_package].preferences

    modifier = canvas.modifiers.new("boolean_" + cutter.name, 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver
    if prefs.show_in_editmode:
        modifier.show_in_editmode = True

    if pin:
        index = canvas.modifiers.find(modifier.name)
        canvas.modifiers.move(index, 0)

    if apply:
        if bpy.context.object.mode != "OBJECT":
            """Applying boolean modifier in mesh edit mode:"""
            """1. Hiding other visible modifiers and creating new (temporary) mesh from evaluated object"""
            """2. Transfering temporary mesh to `bmesh` to update active mesh in edit mode"""
            """3. Removing boolean modifier and purging temporary mesh"""
            """4. Restoring visibility of other modifiers from (1)"""

            visible_modifiers = []
            for mod in canvas.modifiers:
                if mod == modifier:
                    continue
                if mod.show_viewport == True:
                    visible_modifiers.append(mod)
                    mod.show_viewport = False

            evaluated_obj = canvas.evaluated_get(bpy.context.evaluated_depsgraph_get())
            temp_data = bpy.data.meshes.new_from_object(evaluated_obj)

            bm = bmesh.from_edit_mesh(canvas.data)
            bm.clear()
            bm.from_mesh(temp_data)
            bmesh.update_edit_mesh(canvas.data)
            evaluated_obj.to_mesh_clear()

            canvas.modifiers.remove(modifier)
            bpy.data.meshes.remove(temp_data)

            for mod in visible_modifiers:
                mod.show_viewport = True

        else:
            context_override = {'object': canvas, 'mode': "OBJECT"}
            with bpy.context.temp_override(**context_override):
                bpy.ops.object.modifier_apply(modifier=modifier.name)


def set_cutter_properties(context, canvas, cutter, mode, hide=False):
    """Ensures cutter is properly set: has right properties, is hidden, in collection & parented"""

    prefs = bpy.context.preferences.addons[base_package].preferences

    # Hide Cutters
    cutter.hide_render = True
    cutter.display_type = 'WIRE' if prefs.wireframe else 'BOUNDS'
    object_visibility_set(cutter, value=False)
    if hide:
        cutter.hide_set(True)

    # parent_to_active_canvas
    if prefs.parent and cutter.parent == None:
        cutter.parent = canvas
        cutter.matrix_parent_inverse = canvas.matrix_world.inverted()

    # Cutters Collection
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


def convert_to_mesh(context, brush):
    "Converts active object into mesh"

    # store_selection
    stored_active = context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    brush.select_set(True)
    context.view_layer.objects.active = brush

    # Convert
    bpy.ops.object.convert(target='MESH')

    # restore_selection
    for obj in context.selected_objects:
        obj.select_set(True)
    context.view_layer.objects.active = stored_active


def ensure_collection(context):
    """Checks the existance of "boolean_cutters" collection and creates it if it doesn't exist"""
    """Returns "boolean_cutters" collection"""

    collection_name = "boolean_cutters"
    cutters_collection = bpy.data.collections.get(collection_name)

    if cutters_collection is None:
        cutters_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(cutters_collection)
        cutters_collection.hide_viewport = True
        cutters_collection.hide_render = True
        cutters_collection.color_tag = 'COLOR_01'
        context.view_layer.layer_collection.children[collection_name].exclude = True

    return cutters_collection


def delete_empty_collection():
    """Removes "boolean_cutters" collection if it has no more objects in it"""

    collection = bpy.data.collections.get("boolean_cutters")
    if not collection.objects:
        bpy.data.collections.remove(collection)


def delete_cutter(context, cutter):
    """Deletes cutter object and purges it's mesh data"""

    orphaned_mesh = cutter.data
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(orphaned_mesh)


def create_slice(context, canvas, slices, modifier=False):
    """Creates copy of canvas to be used as slice"""

    prefs = bpy.context.preferences.addons[base_package].preferences

    slice = canvas.copy()
    context.collection.objects.link(slice)
    slice.data = canvas.data.copy()
    slice.name = slice.data.name = canvas.name + "_slice"

    # parent_to_canvas
    if prefs.parent:
        slice.parent = canvas
        slice.matrix_parent_inverse = canvas.matrix_world.inverted()

    # set_boolean_properties
    if modifier == True:
        slice.booleans.canvas = True
        slice.booleans.slice = True
        slice.booleans.slice_of = canvas
    slices.append(slice)

    # add_to_canvas_collections
    canvas_colls = canvas.users_collection
    for collection in canvas_colls:
        if collection != context.view_layer.active_layer_collection.collection:
            collection.objects.link(slice)

    for coll in slice.users_collection:
        if coll not in canvas_colls:
            coll.objects.unlink(slice)

    # remove_other_modifiers
    for mod in slice.modifiers:
        if "boolean_" in mod.name:
            slice.modifiers.remove(mod)

    # add_slices_to_local_view
    space_data = context.space_data
    if space_data.local_view:
        slice.local_view_set(space_data, True)
