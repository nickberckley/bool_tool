import bpy


def is_canvas(obj):
    if not "Boolean Canvas" in obj:
        return False
    else:
        cutters = list_canvas_cutters([obj])
        if cutters != 0:
            return True
        else:
            return False



#### ------------------------------ /list_objects/ ------------------------------ ####

# List Candidate Objects
def list_candidate_objects(context):
    brushes = []
    for obj in context.selected_objects:
        if obj != context.active_object and obj.type in ("MESH", "CURVE", "FONT"):
            if obj.type in ("CURVE", "FONT"):
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
        if "Boolean Canvas" in obj:
            if len(obj.modifiers) >= 1:
                if any('BOOLEAN' in modifier.type for modifier in obj.modifiers):
                    canvas.append(obj)
    return canvas


# List Selected Cutters
def list_selected_cutters(context):
    cutters = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj != active_object and obj.type == "MESH":
                if 'Boolean Brush' in obj:
                    cutters.append(obj)

    if active_object:
        if 'Boolean Brush' in active_object:
            cutters.append(active_object)

    return cutters


# List Cutters for Context Canvases
def list_canvas_cutters(canvas):
    brushes = []
    for obj in canvas:
        for modifier in obj.modifiers:
            if modifier.type == "BOOLEAN" and "boolean_" in modifier.name:
                if modifier.object:
                    brushes.append(modifier.object)

    return brushes


# List Modifiers that Use Context Cutters
def list_cutter_modifiers(canvases, cutters):
    if not canvases:
        canvases = list_canvases()

    modifiers = []
    for obj in canvases:
        for modifier in obj.modifiers:
            if modifier.type == "BOOLEAN":
                if modifier.object in cutters:
                    modifiers.append(modifier)

    return modifiers


# List All Slices
def list_slices(context, brushes):
    slices = []
    for obj in context.view_layer.objects:
        if "Boolean Slice" in obj:
            if len(obj.modifiers) >= 1:
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    if any('boolean_' in modifier.name for modifier in obj.modifiers):
                        slices.append(obj)
    return slices


# List Context Cutter Users (Canvases)
def list_cutter_users(cutters):
    cutter_users = []
    canvas = list_canvases()
    for obj in canvas:
        for modifier in obj.modifiers:
            if modifier.type == "BOOLEAN" and modifier.object in cutters:
                cutter_users.append(obj)

    return cutter_users



#### ------------------------------ /set_properties/ ------------------------------ ####

# Add Boolean Modifier
def add_boolean_modifier(canvas, cutter, mode, apply=False):
    modifier = canvas.modifiers.new("boolean_" + cutter.name, "BOOLEAN")
    modifier.operation = mode
    modifier.object = cutter

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
    bpy.ops.object.convert(target="MESH")
    
    # restore_selection
    for obj in context.selected_objects:
        obj.select_set(True)
    context.view_layer.objects.active = stored_active