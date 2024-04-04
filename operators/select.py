import bpy
from ..functions import (
    list_canvases,
    list_selected_cutters,
    list_canvas_cutters,
    list_cutter_users,
)

#### ------------------------------ OPERATORS ------------------------------ ####

# Select Cutter Canvas
class OBJECT_OT_select_cutter_canvas(bpy.types.Operator):
    bl_idname = "object.select_cutter_canvas"
    bl_label = "Select Boolean Canvas"
    bl_description = "Select all the objects that use selected objects as boolean cutters"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT' and "Boolean Brush" in context.active_object

    def execute(self, context):
        brushes = list_selected_cutters(context)
        canvas = list_cutter_users(brushes)

        # select_canvases
        bpy.ops.object.select_all(action='DESELECT')
        for obj in canvas:
            obj.select_set(True)

        return {"FINISHED"}


# Select All Cutters
class OBJECT_OT_select_boolean_all(bpy.types.Operator):
    bl_idname = "object.select_boolean_all"
    bl_label = "Select Boolean Cutters"
    bl_description = "Select all boolean cutters affecting active object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT' and 'Boolean Canvas' in context.active_object

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if "Boolean Canvas" in obj]
        brushes = list_canvas_cutters(canvas)

        # select_cutters
        bpy.ops.object.select_all(action='DESELECT')
        for brush in brushes:
            brush.select_set(True)
            
        return {"FINISHED"}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_select_cutter_canvas,
    OBJECT_OT_select_boolean_all,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)