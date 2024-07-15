import bpy, itertools
from .. import __package__ as base_package
from ..functions import (
    basic_poll,
    is_canvas,
    object_visibility_set,
    list_canvases,
    list_canvas_slices,
    list_canvas_cutters,
    list_cutter_users,
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
        slices = list_canvas_slices(canvas)

        # toggle_modifiers
        for mod in modifiers:
            mod.show_viewport = not mod.show_viewport
            mod.show_render = not mod.show_render

        # Hide Slices
        for slice in slices:
            slice.hide_viewport = not slice.hide_viewport
            for mod in slice.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in brushes:
                    mod.show_viewport = not mod.show_viewport
                    mod.show_render = not mod.show_render

        unused_brushes, __ = filter_unused_cutters(brushes, canvas, slices, include_visible=True)

        # toggle_cutters_visibility
        for brush in unused_brushes:
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
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = [obj for obj in bpy.context.selected_objects if obj.booleans.canvas == True]
        brushes, __ = list_canvas_cutters(canvas)
        slices = list_canvas_slices(canvas)

        # Remove Slices
        for slice in slices:
            bpy.data.objects.remove(slice)
            if slice in canvas:
                canvas.remove(slice)

        for obj in canvas:
            # Remove Modifiers
            for modifier in obj.modifiers:
                if modifier.type == 'BOOLEAN' and "boolean_" in modifier.name:
                    if modifier.object in brushes:
                        obj.modifiers.remove(modifier)

            # remove_boolean_properties
            if obj.booleans.canvas == True:
                obj.booleans.canvas = False


        # Restore Orphaned Cutters
        unused_brushes, leftovers = filter_unused_cutters(brushes, canvas, slices, do_leftovers=True)

        for brush in unused_brushes:
            # restore_visibility
            brush.display_type = 'TEXTURED'
            object_visibility_set(brush, value=True)
            brush.hide_render = False
            if brush.booleans.cutter:
                brush.booleans.cutter = ""

            # remove_parent_&_collection
            if prefs.parent:
                brush.parent = None
            cutters_collection = bpy.data.collections.get("boolean_cutters")
            if cutters_collection in brush.users_collection:
                bpy.data.collections.get("boolean_cutters").objects.unlink(brush)

        # purge_empty_collection
        delete_empty_collection()


        # Change Leftover Cutter Parent
        if prefs.parent:
            for cutter in leftovers:
                if cutter.parent in canvas:
                    other_canvases = list_cutter_users([cutter])
                    cutter.parent = other_canvases[0]

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
        prefs = bpy.context.preferences.addons[base_package].preferences

        canvas = [obj for obj in bpy.context.selected_objects if obj.booleans.canvas == True]
        brushes, __ = list_canvas_cutters(canvas)
        slices = list_canvas_slices(canvas)

        # Apply Modifiers
        for obj in itertools.chain(canvas, slices):
            bpy.context.view_layer.objects.active = obj
            for modifier in obj.modifiers:
                if "boolean_" in modifier.name:
                    try:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    except:
                        context.active_object.data = context.active_object.data.copy()
                        bpy.ops.object.modifier_apply(modifier=modifier.name)

            # remove_boolean_properties
            obj.booleans.canvas = False
            obj.booleans.slice = False


        # Purge Orphaned Cutters
        unused_brushes, leftovers = filter_unused_cutters(brushes, canvas, slices, do_leftovers=True)

        purged_cutters = []
        for brush in unused_brushes:
            if brush not in purged_cutters:
                orphaned_mesh = brush.data
                bpy.data.objects.remove(brush)
                bpy.data.meshes.remove(orphaned_mesh)
                purged_cutters.append(brush)

        # purge_empty_collection
        delete_empty_collection()


        # Change Leftover Cutter Parent
        if prefs.parent:
            for cutter in leftovers:
                if cutter.parent in canvas:
                    other_canvases = list_cutter_users([cutter])
                    cutter.parent = other_canvases[0]

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
