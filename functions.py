import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def isCanvas(_obj):
    try:
        if _obj["Boolean Canvas"]:
            return True
    except:
        return False

def isBrush(_obj):
    try:
        if _obj["Boolean Brush"]:
            return True
    except:
        return False


# Set Object Visibility
def object_visibility_set(ob, value=False):
    ob.visible_camera = value
    ob.visible_diffuse = value
    ob.visible_glossy = value
    ob.visible_shadow = value
    ob.visible_transmission = value
    ob.visible_volume_scatter = value


# Find Canvas
def find_canvas(context):
    canvas = []
    for obj in bpy.context.view_layer.objects:
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
    for obj in bpy.context.view_layer.objects:
        if obj.get("Boolean Slice"):
            if len(obj.modifiers) >= 1:
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    if any('Bool Tool ' in modifier.name for modifier in obj.modifiers):
                        slices.append(obj)
    return slices
    

# Convert to Mesh
def convert_to_mesh(brush, canvas):
    # Store Selection
    selected_objects = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    brush.select_set(True)
    bpy.context.view_layer.objects.active = brush
    
    # Convert to Mesh
    bpy.ops.object.convert(target="MESH")
    
    # Restore Selection
    for obj in selected_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = canvas