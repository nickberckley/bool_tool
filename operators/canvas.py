import bpy, itertools
from ..functions import (
    basic_poll,
    is_canvas,
    object_visibility_set,
    list_canvases,
    list_slices,
    list_canvas_cutters,
    delete_empty_collection,
    filter_unused_cutters,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle All Cutters
class OBJECT_OT_toggle_boolean_all(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_all"
    bl_label = "Toggle Boolean Cutters"
    bl_description = "Toggle all boolean cutters affecting selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.booleans.canvas == True]
        brushes, modifiers = list_canvas_cutters(canvas)

        # toggle_modifiers
        for mod in modifiers:
            mod.show_viewport = not mod.show_viewport
            mod.show_render = not mod.show_render

        # list_cutters_only_used_by_active_canvas
        other_canvas = list_canvases()
        for obj in other_canvas:
            if obj not in canvas:
                if any(modifier.object in brushes and modifier.show_viewport for modifier in obj.modifiers):
                    brushes[:] = [brush for brush in brushes if brush not in [modifier.object for modifier in obj.modifiers]]

        # toggle_cutters_visibility
        for brush in brushes:
            brush.hide_viewport = not brush.hide_viewport

        return {'FINISHED'}


# Remove All Cutters
class OBJECT_OT_remove_boolean_all(bpy.types.Operator):
    bl_idname = "object.remove_boolean_all"
    bl_label = "Remove Boolean Cutters"
    bl_description = "Remove all boolean cutters from selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.booleans.canvas == True]
        brushes, __ = list_canvas_cutters(canvas)
        slices = list_slices(context, brushes)

        # remove_slices
        for slice in slices:
            bpy.data.objects.remove(slice)
            if slice in canvas:
                canvas.remove(slice)

        for obj in canvas:
            # remove_modifiers
            for modifier in obj.modifiers:
                if modifier.type == 'BOOLEAN' and "boolean_" in modifier.name:
                    if modifier.object in brushes:
                        obj.modifiers.remove(modifier)

            # remove_boolean_properties
            if obj.booleans.canvas == True:
                obj.booleans.canvas = False

        filter_unused_cutters(brushes, canvas, slices)

        for brush in brushes:
            # restore_visibility
            brush.display_type = 'TEXTURED'
            object_visibility_set(brush, value=True)
            brush.hide_render = False
            if brush.booleans.cutter:
                brush.booleans.cutter = ""

            # remove_parent_&_collection
            brush.parent = None
            cutters_collection = bpy.data.collections.get("boolean_cutters")
            if cutters_collection in brush.users_collection:
                bpy.data.collections.get("boolean_cutters").objects.unlink(brush)

        # purge_empty_collection
        delete_empty_collection()

        return {'FINISHED'}


# Apply All Cutters
class OBJECT_OT_apply_boolean_all(bpy.types.Operator):
    bl_idname = "object.apply_boolean_all"
    bl_label = "Apply All Boolean Cutters"
    bl_description = "Apply all boolean cutters on selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.booleans.canvas == True]
        brushes, __ = list_canvas_cutters(canvas)
        slices = list_slices(context, brushes)

        # apply_modifiers
        for obj in itertools.chain(canvas, slices):
            bpy.context.view_layer.objects.active = obj
            for modifier in obj.modifiers:
                if "boolean_" in modifier.name:
                    try:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    except:
                        context.active_object.data = context.active_object.data.copy()
                        bpy.ops.object.modifier_apply(modifier=modifier.name)

            # remove_custom_properties
            if obj.booleans.canvas == True:
                obj.booleans.canvas = False
            if obj.booleans.slice == True:
                obj.booleans.slice = False

        # purge_orphans
        filter_unused_cutters(brushes, canvas, slices)

        purged_cutters = []
        for brush in brushes:
            if brush not in purged_cutters:
                orphaned_mesh = brush.data
                bpy.data.objects.remove(brush)
                bpy.data.meshes.remove(orphaned_mesh)
                purged_cutters.append(brush)

        # purge_empty_collection
        delete_empty_collection()

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_toggle_boolean_all,
    OBJECT_OT_remove_boolean_all,
    OBJECT_OT_apply_boolean_all,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
