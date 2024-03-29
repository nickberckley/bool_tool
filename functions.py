import bpy


#### ------------------------------ /list_objects/ ------------------------------ ####

# List Candidate Objects
def list_candidate_objects(context):
    brushes = []
    for obj in context.selected_objects:
        if obj != context.active_object and (obj.type == "MESH" or obj.type == "CURVE"):
            if obj.type == "CURVE":
                if obj.data.bevel_depth != 0 or obj.data.extrude != 0:
                    convert_to_mesh(context, obj)
                    brushes.append(obj)
            else:
                brushes.append(obj)

    return brushes


# Find Canvas
def find_canvas(context):
    canvas = []
    for obj in context.view_layer.objects:
        if "Boolean Brush" not in obj and "Boolean Canvas" in obj:
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


# Find Modifiers that Use Active Cutter
def find_cutter_modifiers(context, cutters):
    canvases = find_canvas(context)

    modifiers = []
    for obj in canvases:
        for modifier in obj.modifiers:
            if modifier.type == "BOOLEAN":
                if modifier.object in cutters:
                    modifiers.append(modifier)

    return canvases, modifiers


# Find Slices
def find_slices(self, context, brushes):
    slices = []
    for obj in context.view_layer.objects:
        if obj.get("Boolean Slice"):
            if len(obj.modifiers) >= 1:
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    if any('Bool Tool ' in modifier.name for modifier in obj.modifiers):
                        slices.append(obj)
    return slices
    


#### ------------------------------ /set_properties/ ------------------------------ ####

# Set Object Visibility
def object_visibility_set(ob, value=False):
    ob.visible_camera = value
    ob.visible_diffuse = value
    ob.visible_glossy = value
    ob.visible_shadow = value
    ob.visible_transmission = value
    ob.visible_volume_scatter = value


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