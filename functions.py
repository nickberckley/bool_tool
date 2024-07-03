import bpy


#### ------------------------------ /polls/ ------------------------------ ####

def basic_poll(context):
    if context.mode == 'OBJECT':
        if context.active_object is not None:
            if context.active_object.type == 'MESH':
                return True


def is_canvas(obj):
    if obj.booleans.canvas == False:
        return False
    else:
        cutters, __ = list_canvas_cutters([obj])
        if len(cutters) != 0:
            return True
        else:
            return False



#### ------------------------------ /list_objects/ ------------------------------ ####

# List Candidate Objects
def list_candidate_objects(context):
    brushes = []
    for obj in context.selected_objects:
        if obj != context.active_object and obj.type in ('MESH', 'CURVE', 'FONT'):
            if obj.type in ('CURVE', 'FONT'):
                if obj.data.bevel_depth != 0 or obj.data.extrude != 0:
                    convert_to_mesh(context, obj)
                    brushes.append(obj)
            else:
                brushes.append(obj)

    return brushes


# List All Canvases
def list_canvases():
    canvas = []
    for obj in bpy.data.objects:
        if is_canvas(obj):
            canvas.append(obj)

    return canvas


# List Selected Cutters
def list_selected_cutters(context):
    cutters = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj != active_object and obj.type == 'MESH':
                if obj.booleans.cutter:
                    cutters.append(obj)

    if active_object:
        if active_object.booleans.cutter:
            cutters.append(active_object)

    return cutters


# List Cutters for Context Canvases
def list_canvas_cutters(canvas):
    cutters = []
    modifiers = []
    for obj in canvas:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and "boolean_" in modifier.name:
                if modifier.object:
                    cutters.append(modifier.object)
                    modifiers.append(modifier)

    return cutters, modifiers


# List Modifiers that Use Context Cutters
def list_cutter_modifiers(canvases, cutters):
    if not canvases:
        canvases = list_canvases()

    modifiers = []
    for obj in canvases:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN':
                if modifier.object in cutters:
                    modifiers.append(modifier)

    return modifiers


def list_canvas_slices(canvases):
    """Returns list of slices for specified canvases"""

    slices = []
    for obj in bpy.data.objects:
        if obj.booleans.slice:
            if obj.booleans.slice_of in canvases:
                slices.append(obj)

    return slices


# List Context Cutter Users (Canvases)
def list_cutter_users(cutters):
    cutter_users = []
    canvas = list_canvases()
    for obj in canvas:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object in cutters:
                cutter_users.append(obj)

    return cutter_users



#### ------------------------------ /set_properties/ ------------------------------ ####

# Add Boolean Modifier
def add_boolean_modifier(canvas, cutter, mode, solver, apply=False):
    modifier = canvas.modifiers.new("boolean_" + cutter.name, 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver

    if apply:
        context_override = {'object': canvas}
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.modifier_apply(modifier=modifier.name)


# Set Object Visibility
def object_visibility_set(obj, value=False):
    obj.visible_camera = value
    obj.visible_diffuse = value
    obj.visible_glossy = value
    obj.visible_shadow = value
    obj.visible_transmission = value
    obj.visible_volume_scatter = value


# Convert to Mesh
def convert_to_mesh(context, brush):
    # store_selection
    stored_active = context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    brush.select_set(True)
    context.view_layer.objects.active = brush

    # convert_to_mesh
    bpy.ops.object.convert(target='MESH')

    # restore_selection
    for obj in context.selected_objects:
        obj.select_set(True)
    context.view_layer.objects.active = stored_active


# Delete Empty Collection
def delete_empty_collection():
    collection = bpy.data.collections.get("boolean_cutters")
    if not collection.objects:
        bpy.data.collections.remove(collection)


# Create Slice
def create_slice(context, canvas, slices, modifier=False):
    slice = canvas.copy()
    context.collection.objects.link(slice)
    slice.data = canvas.data.copy()
    slice.name = slice.data.name = canvas.name + "_slice"

    # parent_to_canvas
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


def filter_unused_cutters(cutters, *canvas, include_visible=False):
    """Takes in list of cutters and returns only those that have no other user besides specified canvas"""
    """When `include_visible` is True it will return cutters that aren't used by any visible modifiers"""

    other_canvas = list_canvases()
    for obj in other_canvas:
        if obj not in canvas:
            if include_visible:
                if any(modifier.object in cutters and modifier.show_viewport for modifier in obj.modifiers):
                    cutters[:] = [cutter for cutter in cutters if cutter not in [modifier.object for modifier in obj.modifiers]]
            else:
                if any(modifier.object in cutters for modifier in obj.modifiers):
                    cutters[:] = [cutter for cutter in cutters if cutter not in [modifier.object for modifier in obj.modifiers]]

    return cutters
