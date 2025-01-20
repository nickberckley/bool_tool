import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def bool_tool_manual_map():
    url_manual_prefix = "https://github.com/nickberckley/bool_tool/wiki/"

    # Carver
    url_manual_mapping = (("bpy.ops.object.carve", "Carver"),
                          # Brush Boolean
                          ("bpy.ops.object.boolean_brush_union", "Boolean-Operators"),
                          ("bpy.ops.object.boolean_brush_intersect", "Boolean-Operators"),
                          ("bpy.ops.object.boolean_brush_difference", "Boolean-Operators"),
                          ("bpy.ops.object.boolean_brush_slice", "Boolean-Operators"),
                          # Auto Boolean
                          ("bpy.ops.object.boolean_auto_union", "Boolean-Operators#auto-boolean-operators"),
                          ("bpy.ops.object.boolean_auto_intersect", "Boolean-Operators#auto-boolean-operators"),
                          ("bpy.ops.object.boolean_auto_difference", "Boolean-Operators#auto-boolean-operators"),
                          ("bpy.ops.object.boolean_auto_slice", "Boolean-Operators#auto-boolean-operators"),
                          # Cutter Utilities
                          ("bpy.ops.object.boolean_toggle_cutter", "Utility-Operators#toggle-cutter"),
                          ("bpy.ops.object.boolean_remove_cutter", "Utility-Operators#remove-cutter"),
                          ("bpy.ops.object.boolean_apply_cutter", "Utility-Operators#apply-cutter"),
                          # Canvas Utilities
                          ("bpy.ops.object.boolean_toggle_all", "Utility-Operators#toggle-all-cutters"),
                          ("bpy.ops.object.boolean_remove_all", "Utility-Operators#remove-all-cutters"),
                          ("bpy.ops.object.boolean_apply_all", "Utility-Operators#apply-all-cutters"),
                          # Select
                          ("bpy.ops.object.select_cutter_canvas", "Utility-Operators#select-operators"),
                          ("bpy.ops.object.boolean_select_all", "Utility-Operators#select-operators"),
    )

    return url_manual_prefix, url_manual_mapping



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # MANUAL
    bpy.utils.register_manual_map(bool_tool_manual_map)

def unregister():
    # MANUAL
    bpy.utils.unregister_manual_map(bool_tool_manual_map)
