import bpy
from .. import __package__ as base_package
from ..functions import (
    basic_poll,
    add_boolean_modifier,
    object_visibility_set,
    list_candidate_objects,
)


#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean():
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        canvas = bpy.context.active_object
        brushes = list_candidate_objects(context)

        if self.mode == "SLICE":
            # create_slicer_clones
            clones = []
            for i in range(len(brushes)):
                clone = canvas.copy()
                clone.name = canvas.name + "_slice"
                clone.booleans.canvas = True
                clone.booleans.slice = True
                clone.parent = canvas
                clone.matrix_parent_inverse = canvas.matrix_world.inverted()
                context.collection.objects.link(clone)
                clones.append(clone)

                # add_to_canvas_collections
                canvas_colls = canvas.users_collection
                for collection in canvas_colls:
                    if collection != context.view_layer.active_layer_collection.collection:
                        collection.objects.link(clone)

                for coll in clone.users_collection:
                    if coll not in canvas_colls:
                        coll.objects.unlink(clone)

                # remove_other_modifiers
                for mod in clone.modifiers:
                    if "boolean_" in mod.name:
                        clone.modifiers.remove(mod)

            for brush, clone in zip(brushes, clones):
                # add_slices_to_local_view
                space_data = context.space_data
                if space_data.local_view:
                    clone.local_view_set(space_data, True)

                # modifiers_on_slices
                add_boolean_modifier(clone, brush, "INTERSECT", prefs.solver)
                cutter_index = clone.booleans.cutters.add()
                cutter_index.cutter = brush


        for brush in brushes:
            # hide_brush
            brush.hide_render = True
            brush.display_type = 'WIRE' if prefs.wireframe else 'BOUNDS'
            object_visibility_set(brush, value=False)
            brush.parent = canvas
            brush.matrix_parent_inverse = canvas.matrix_world.inverted()

            # cutters_collection
            collection_name = "boolean_cutters"
            cutters_collection = bpy.data.collections.get(collection_name)
            if cutters_collection is None:
                cutters_collection = bpy.data.collections.new(collection_name)
                context.scene.collection.children.link(cutters_collection)
                cutters_collection.hide_viewport = True
                cutters_collection.hide_render = True
                cutters_collection.color_tag = 'COLOR_01'
                bpy.context.view_layer.layer_collection.children[collection_name].exclude = True
            if cutters_collection not in brush.users_collection:
                cutters_collection.objects.link(brush)

            # add_modifier
            add_boolean_modifier(canvas, brush, "DIFFERENCE" if self.mode == "SLICE" else self.mode, prefs.solver)

            # custom_properties
            canvas.booleans.canvas = True
            brush.booleans.cutter = self.mode.capitalize()
            cutter_index = canvas.booleans.cutters.add()
            cutter_index.cutter = brush

        bpy.context.view_layer.objects.active = canvas
        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_union"
    bl_label = "Boolean Cutter Union"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_intersect"
    bl_label = "Boolean Cutter Intersection"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_difference"
    bl_label = "Boolean Cutter Difference"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_slice"
    bl_label = "Boolean Cutter Slice"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "SLICE"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean:
    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        canvas = bpy.context.active_object
        brushes = list_candidate_objects(context)

        for brush in brushes:
            # add_modifier
            add_boolean_modifier(canvas, brush, self.mode, prefs.solver, apply=True)

            # delete_brush
            bpy.data.objects.remove(brush)

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_union"
    bl_label = "Boolean Union"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "UNION"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_difference"
    bl_label = "Boolean Difference"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_intersect"
    bl_label = "Boolean Intersect"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    mode = "INTERSECT"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator):
    bl_idname = "object.bool_tool_auto_slice"
    bl_label = "Boolean Slice"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(context)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        canvas = context.active_object
        brushes = list_candidate_objects(context)

        for brush in brushes:
            # copy_canvas
            canvas_copy = canvas.copy()
            canvas_copy.name = canvas.name + "_slice"
            canvas_copy.data = canvas.data.copy()
            canvas_copy.data.name = canvas.data.name + "_slice"
            for collection in canvas.users_collection:
                collection.objects.link(canvas_copy)

            # add_to_local_view
            space_data = context.space_data
            if space_data.local_view:
                canvas_copy.local_view_set(space_data, True)

            # add_modifiers
            add_boolean_modifier(canvas, brush, "DIFFERENCE", prefs.solver, apply=True)
            add_boolean_modifier(canvas_copy, brush, "INTERSECT", prefs.solver, apply=True)

            bpy.data.objects.remove(brush)
            canvas_copy.select_set(True)
            context.view_layer.objects.active = canvas_copy

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, "Boolean operator needs at least two objects selected")
            return {'CANCELLED'}

        return self.execute(context)



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_boolean_brush_union,
    OBJECT_OT_boolean_brush_difference,
    OBJECT_OT_boolean_brush_intersect,
    OBJECT_OT_boolean_brush_slice,

    OBJECT_OT_boolean_auto_union,
    OBJECT_OT_boolean_auto_difference,
    OBJECT_OT_boolean_auto_intersect,
    OBJECT_OT_boolean_auto_slice,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    # brush_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_union.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_difference.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_intersect.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_slice.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl=True)

    # auto_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_union.bl_idname, 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_difference.bl_idname, 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_intersect.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_slice.bl_idname, 'NUMPAD_SLASH', 'PRESS', ctrl=True, shift=True)
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
