import bpy
from ..functions import (
    basic_poll,
    object_visibility_set,
    list_canvases,
    list_selected_cutters,
    list_canvas_cutters,
    delete_empty_collection,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle Boolean Cutter
class OBJECT_OT_toggle_boolean_brush(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_brush"
    bl_label = "Toggle Boolean Cutter"
    bl_description = "Toggle this boolean cutter. If cutter isn't the active object it will be toggled for every canvas that uses it"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        canvas = list_canvases()
        if self.specified_cutter:
            specified_cutter = bpy.data.objects[self.specified_cutter]
            brushes = [specified_cutter]
        else:
            brushes = list_selected_cutters(context)

        if brushes:
            for obj in canvas:
                # toggle_slices_visibility
                if obj.bool_tool.slice == True:
                    if any(modifier.object in brushes for modifier in obj.modifiers):
                        obj.hide_viewport = not obj.hide_viewport
                        obj.hide_render = not obj.hide_render

                # toggle_modifiers_visibility
                for modifier in obj.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in brushes:
                            modifier.show_viewport = not modifier.show_viewport
                            modifier.show_render = not modifier.show_render

        else:
            self.report({'INFO'}, "No boolean cutters are selected")

        return {"FINISHED"}


# Remove Boolean Cutter
class OBJECT_OT_remove_boolean_brush(bpy.types.Operator):
    bl_idname = "object.remove_boolean_brush"
    bl_label = "Remove Boolean Cutter"
    bl_description = "Remove this boolean cutter. If cutter isn't the active object it will be removed from every canvas that uses it"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        canvas = list_canvases()
        if self.specified_cutter:
            specified_cutter = bpy.data.objects[self.specified_cutter]
            brushes = [specified_cutter]
        else:
            brushes = list_selected_cutters(context)

        if brushes:
            # delete_modifiers
            for obj in canvas:
                slice_obj = False
                for modifier in obj.modifiers:
                    if "boolean_" in modifier.name:
                        if modifier.object in brushes:
                            slice_obj = True
                            obj.modifiers.remove(modifier)

                # remove_slices
                if obj.bool_tool.slice == True:
                    if slice_obj:
                        bpy.data.objects.remove(obj)

                # remove_canvas_property_if_needed
                cutters, __ = list_canvas_cutters([obj])
                if len(cutters) == 0:
                    obj.bool_tool.canvas = False

            for brush in brushes:
                # restore_visibility
                brush.display_type = "TEXTURED"
                object_visibility_set(brush, value=True)
                brush.hide_render = False
                if obj.bool_tool.cutter:
                    obj.bool_tool.cutter = ""

                # remove_parent_&_collection
                brush.parent = None
                cutters_collection = bpy.data.collections.get("boolean_cutters")
                if cutters_collection in brush.users_collection:
                    bpy.data.collections.get("boolean_cutters").objects.unlink(brush)

            # purge_empty_collection
            delete_empty_collection()

        else:
            self.report({'INFO'}, "No boolean cutters are selected")
        
        return {"FINISHED"}


# Apply Boolean Cutter
class OBJECT_OT_apply_boolean_brush(bpy.types.Operator):
    bl_idname = "object.apply_boolean_brush"
    bl_label = "Apply Boolean Cutter"
    bl_description = "Apply this boolean cutter. If cutter isn't the active object it will be applied to every canvas that uses it"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        canvas = list_canvases()
        if self.specified_cutter:
            specified_cutter = bpy.data.objects[self.specified_cutter]
            brushes = [specified_cutter]
        else:
            brushes = list_selected_cutters(context)

        if brushes:
            for obj in canvas:
                context.view_layer.objects.active = obj
                for mod in obj.modifiers:
                    if "boolean_" in mod.name:
                        if mod.object in brushes:
                            try:
                                bpy.ops.object.modifier_apply(modifier=mod.name)
                            except:
                                context.active_object.data = context.active_object.data.copy()
                                bpy.ops.object.modifier_apply(modifier=mod.name)

                # remove_canvas_property_if_needed
                cutters, __ = list_canvas_cutters([obj])
                if len(cutters) == 0:
                    obj.bool_tool.canvas = False

            # purge_orphaned_brushes
            for brush in brushes:
                orphaned_mesh = brush.data
                bpy.data.objects.remove(brush)
                bpy.data.meshes.remove(orphaned_mesh)

            # purge_empty_collection
            delete_empty_collection()

        else:
            self.report({'INFO'}, "No boolean cutters are selected")

        return {"FINISHED"}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_toggle_boolean_brush,
    OBJECT_OT_remove_boolean_brush,
    OBJECT_OT_apply_boolean_brush,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
