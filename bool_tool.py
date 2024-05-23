import bpy, itertools
from .functions import (
    is_canvas,
    add_boolean_modifier,
    object_visibility_set,
    list_canvases,
    list_slices,
    list_selected_cutters,
    list_candidate_objects,
    list_canvas_cutters,
)


#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean():
    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        canvas = bpy.context.active_object
        brushes = list_candidate_objects(context)

        if self.mode == "SLICE":
            # create_slicer_clones
            clones = []
            for i in range(len(brushes)):
                clone = canvas.copy()
                clone.name = canvas.name + '_slice'
                clone.bool_tool.canvas = True
                clone.bool_tool.slice = True
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
                cutter_index = clone.bool_tool.cutters.add()
                cutter_index.cutter = brush


        for brush in brushes:
            # hide_brush
            brush.hide_render = True
            brush.display_type = "BOUNDS"
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
                cutters_collection.color_tag = "COLOR_01"
                bpy.context.view_layer.layer_collection.children[collection_name].exclude = True
            if cutters_collection not in brush.users_collection:
                cutters_collection.objects.link(brush)

            # add_modifier
            add_boolean_modifier(canvas, brush, "DIFFERENCE" if self.mode == "SLICE" else self.mode, prefs.solver)
            
            # custom_properties
            canvas.bool_tool.canvas = True
            brush.bool_tool.cutter = self.mode.capitalize()
            cutter_index = canvas.bool_tool.cutters.add()
            cutter_index.cutter = brush
            
        bpy.context.view_layer.objects.active = canvas
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "Boolean operator needs at least two objects selected")
            return {"CANCELLED"}

        return self.execute(context)


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_union"
    bl_label = "Boolean Cutter Union"
    bl_description = "Add boolean cutter to the active object set to Union"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "UNION"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_intersect"
    bl_label = "Boolean Cutter Intersection"
    bl_description = "Add boolean cutter to the active object set to Intersect"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "INTERSECT"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_difference"
    bl_label = "Boolean Cutter Difference"
    bl_description = "Add boolean cutter to the active object set to Difference"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_slice"
    bl_label = "Boolean Cutter Slice"
    bl_description = "Add boolean cutter to the active object set to Slice"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "SLICE"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean:
    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        canvas = bpy.context.active_object
        brushes = list_candidate_objects(context)
        
        for brush in brushes:
            # add_modifier
            add_boolean_modifier(canvas, brush, self.mode, prefs.solver, apply=True)

            # delete_brush
            bpy.data.objects.remove(brush)
                    
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "Boolean operator needs at least two objects selected")
            return {"CANCELLED"}

        return self.execute(context)


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_union"
    bl_label = "Boolean Union"
    bl_description = "Merge selected objects into active one with union boolean"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "UNION"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_difference"
    bl_label = "Boolean Difference"
    bl_description = "Subtract selected objects from active one using difference boolean"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_intersect"
    bl_label = "Boolean Intersect"
    bl_description = "Use intersect boolean to keep only parts of active object that are interesecting selected objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    mode = "INTERSECT"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator):
    bl_idname = "object.bool_tool_auto_slice"
    bl_label = "Boolean Slice"
    bl_description = "Slice active object along the selected objects with boolean operators. Will create slices as separate objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
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

        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "Boolean operator needs at least two objects selected")
            return {"CANCELLED"}

        return self.execute(context)



#### ------------------------------ /brush_utilities/ ------------------------------ ####

# Toggle Boolean Cutter
class OBJECT_OT_toggle_boolean_brush(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_brush"
    bl_label = "Toggle Boolean Cutter"
    bl_description = "Toggles the selected boolean cutter effect on the canvas objects"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

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

        return {"FINISHED"}


# Remove Boolean Cutter
class OBJECT_OT_remove_boolean_brush(bpy.types.Operator):
    bl_idname = "object.remove_boolean_brush"
    bl_label = "Remove Boolean Cutter"
    bl_description = "Removes boolean cutter properties from selected canvases"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

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
        
        return {"FINISHED"}


# Apply Boolean Cutter
class OBJECT_OT_apply_boolean_brush(bpy.types.Operator):
    bl_idname = "object.apply_boolean_brush"
    bl_label = "Apply Boolean Cutter"
    bl_description = "Apply this boolean cutter to the every canvas that uses it"
    bl_options = {"UNDO"}

    specified_cutter: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'

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

            # purge_orphaned_brushes
            for brush in brushes:
                orphaned_mesh = brush.data
                bpy.data.objects.remove(brush)
                bpy.data.meshes.remove(orphaned_mesh)

        return {"FINISHED"}



#### ------------------------------ /canvas_utilities/ ------------------------------ ####
    
# Toggle All Cutters
class OBJECT_OT_toggle_boolean_all(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_all"
    bl_label = "Toggle Boolean Cutters"
    bl_description = "Toggle all boolean cutters affecting active object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT' and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
        brushes = list_canvas_cutters(canvas)

        # toggle_cutters_visibility
        for brush in brushes:
            brush.hide_viewport = not brush.hide_viewport
            
        return {"FINISHED"}


# Remove All Cutters
class OBJECT_OT_remove_boolean_all(bpy.types.Operator):
    bl_idname = "object.remove_boolean_all"
    bl_label = "Remove Boolean Cutters"
    bl_description = "Remove all boolean cutters affecting active object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT' and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
        brushes = list_canvas_cutters(canvas)
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
        
        return {"FINISHED"}


# Apply All Cutters
class OBJECT_OT_apply_boolean_all(bpy.types.Operator):
    bl_idname = "object.apply_boolean_all"
    bl_label = "Apply All Boolean Cutters"
    bl_description = "Apply all boolean cutters of selected canvas objects"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT' and is_canvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if obj.bool_tool.canvas == True]
        brushes = list_canvas_cutters(canvas)
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

        return {"FINISHED"}



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
    
    OBJECT_OT_toggle_boolean_brush,
    OBJECT_OT_remove_boolean_brush,
    OBJECT_OT_apply_boolean_brush,

    OBJECT_OT_toggle_boolean_all,
    OBJECT_OT_remove_boolean_all,
    OBJECT_OT_apply_boolean_all,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")
    
    # brush_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_union.bl_idname, "NUMPAD_PLUS", "PRESS", ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_difference.bl_idname, "NUMPAD_MINUS", "PRESS", ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_intersect.bl_idname, "NUMPAD_ASTERIX", "PRESS", ctrl=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_brush_slice.bl_idname, "NUMPAD_SLASH", "PRESS", ctrl=True)
    
    # auto_operators
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_union.bl_idname, "NUMPAD_PLUS", "PRESS", ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_difference.bl_idname, "NUMPAD_MINUS", "PRESS", ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_intersect.bl_idname, "NUMPAD_ASTERIX", "PRESS", ctrl=True, shift=True)
    kmi = km.keymap_items.new(OBJECT_OT_boolean_auto_slice.bl_idname, "NUMPAD_SLASH", "PRESS", ctrl=True, shift=True)
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