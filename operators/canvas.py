import bpy, itertools
from ..functions import (
    basic_poll,
    is_canvas,
    object_visibility_set,
    list_canvases,
    list_slices,
    list_canvas_cutters,
    delete_empty_collection,
)


#### ------------------------------ OPERATORS ------------------------------ ####
    
# Toggle All Cutters
class OBJECT_OT_toggle_boolean_all(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_all"
    bl_label = "Toggle Boolean Cutters"
    bl_description = "Toggle all boolean cutters affecting selected canvases"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
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
            
        return {"FINISHED"}


# Remove All Cutters
class OBJECT_OT_remove_boolean_all(bpy.types.Operator):
    bl_idname = "object.remove_boolean_all"
    bl_label = "Remove Boolean Cutters"
    bl_description = "Remove all boolean cutters from selected canvases"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
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
                if "boolean_" in modifier.name:
                    if modifier.object in brushes:
                        obj.modifiers.remove(modifier)

            if obj.bool_tool.canvas == True:
                obj.bool_tool.canvas == False
                
        # only_free_cutters_that_other_objects_dont_use
        other_canvas = list_canvases()
        for obj in other_canvas:
            if obj not in (canvas, slices):
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    brushes[:] = [brush for brush in brushes if brush not in [modifier.object for modifier in obj.modifiers]]
        
        for brush in brushes:
            # restore_visibility
            brush.display_type = "TEXTURED"
            object_visibility_set(brush, value=True)
            brush.hide_render = False
            if brush.bool_tool.cutter:
                brush.bool_tool.cutter = ""

            # remove_parent_&_collection
            brush.parent = None
            cutters_collection = bpy.data.collections.get("boolean_cutters")
            if cutters_collection in brush.users_collection:
                bpy.data.collections.get("boolean_cutters").objects.unlink(brush)

        # purge_empty_collection
        delete_empty_collection()
        
        return {"FINISHED"}


# Apply All Cutters
class OBJECT_OT_apply_boolean_all(bpy.types.Operator):
    bl_idname = "object.apply_boolean_all"
    bl_label = "Apply All Boolean Cutters"
    bl_description = "Apply all boolean cutters on selected canvases"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return basic_poll(context) and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
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
            if obj.bool_tool.canvas == True:
                obj.bool_tool.canvas = False
            if obj.bool_tool.slice == True:
                obj.bool_tool.slice = False

        # only_delete_cutters_that_other_objects_dont_use
        other_canvas = list_canvases()
        for obj in other_canvas:
            if obj not in (canvas, slices):
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    brushes[:] = [brush for brush in brushes if brush not in [modifier.object for modifier in obj.modifiers]]

        # purge_orphans
        purged_cutters = []
        for brush in brushes:
            if brush not in purged_cutters:
                orphaned_mesh = brush.data
                bpy.data.objects.remove(brush)
                bpy.data.meshes.remove(orphaned_mesh)
                purged_cutters.append(brush)

        # purge_empty_collection
        delete_empty_collection()

        return {"FINISHED"}


# Select Boolean Brush
class OBJECT_OT_boolean_cutter_select(bpy.types.Operator):
    bl_idname = "object.boolean_cutter_select"
    bl_label = "Select Boolean Cutter"
    bl_description = "Select object that is used as boolean cutter by this modifier"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        if context.area.type == 'PROPERTIES' and context.space_data.context == 'MODIFIER':
            modifier = context.object.modifiers.active
            if modifier and modifier.type == "BOOLEAN":
                cutter = modifier.object

                bpy.ops.object.select_all(action='DESELECT')
                cutter.select_set(True)
                context.view_layer.objects.active = cutter

        return {"FINISHED"}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_toggle_boolean_all,
    OBJECT_OT_remove_boolean_all,
    OBJECT_OT_apply_boolean_all,

    OBJECT_OT_boolean_cutter_select,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name='Property Editor', space_type='PROPERTIES')
    kmi = km.keymap_items.new("object.boolean_cutter_select", type='LEFTMOUSE', value='DOUBLE_CLICK')
    kmi.active = True
    addon_keymaps.append(km)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
