import bpy, itertools
from .functions import isCanvas, isBrush, convert_to_mesh, object_visibility_set, find_canvas, find_slices

#### ------------------------------ OPERATORS ------------------------------ ####

# Brush Boolean operators
class BrushBoolean():
    def execute(self, context):
        canvas = bpy.context.active_object

        # List Brushes
        brushes = []
        for obj in bpy.context.selected_objects:
            if obj != bpy.context.active_object and (obj.type == "MESH" or obj.type == "CURVE"):
                brushes.append(obj)
                if obj.type == "CURVE":
                    if obj.data.bevel_depth != 0 or obj.data.extrude != 0:
                        convert_to_mesh(obj, canvas)
                    else:
                        brushes.remove(obj)
        
        if self.mode == "SLICE":
            # Create Slicer Clones
            clones = []
            for i in range(len(brushes)):
                clone = canvas.copy()
                clone.name = canvas.name + '_slice'
                clone["Boolean Canvas"] = True
                clone["Boolean Slice"] = True
                clone.parent = canvas
                clone.matrix_parent_inverse = canvas.matrix_world.inverted()
                context.collection.objects.link(clone)
                clones.append(clone)
                
                # Add to Correct Collection
                canvas_coll = canvas.users_collection[0]
                if canvas_coll != context.view_layer.active_layer_collection.collection:
                    canvas_coll.objects.link(clone)
                for coll in clone.users_collection:
                    if coll != canvas_coll:
                        coll.objects.unlink(clone)
                
                # Remove Other Modifiers
                for mod in clone.modifiers:
                    if "Bool Tool " in mod.name:
                        clone.modifiers.remove(mod)
                
            # Add to Local View
            for brush, clone in zip(brushes, clones):
                space_data = context.space_data
                is_local_view = bool(space_data.local_view)
                if is_local_view:
                    clone.local_view_set(space_data, True)

                sliceMod = clone.modifiers.new("Bool Tool " + brush.name, "BOOLEAN")
                sliceMod.object = brush
                sliceMod.operation = "INTERSECT"
        
        for brush in brushes:
            # Hide Object
            brush.hide_render = True
            brush.display_type = "BOUNDS"
            object_visibility_set(brush, value=False)
            brush.parent = canvas
            brush.matrix_parent_inverse = canvas.matrix_world.inverted()

            # Add Modifiers
            newMod = canvas.modifiers.new("Bool Tool " + brush.name, "BOOLEAN")
            newMod.object = brush
            if self.mode == "SLICE":
                newMod.operation = "DIFFERENCE"
            else:
                newMod.operation = self.mode
            
            # Custom Properties
            canvas["Boolean Canvas"] = True
            brush["Boolean Brush"] = self.mode.capitalize()
            
            bpy.context.view_layer.objects.active = canvas
        
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "At least two objects must be selected")
            return {"CANCELLED"}

        return self.execute(context)


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_union"
    bl_label = "Boolean Brush Union"
    bl_description = "Add boolean brush to the canvas object set to Union"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "UNION"

class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_intersect"
    bl_label = "Boolean Brush Intersection"
    bl_description = "Add boolean brush to the canvas object set to Intersect"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "INTERSECT"

class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_difference"
    bl_label = "Boolean Brush Difference"
    bl_description = "Add boolean brush to the canvas object set to Difference"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "DIFFERENCE"

class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.bool_tool_brush_slice"
    bl_label = "Boolean Brush Slice"
    bl_description = "Add boolean brush to the canvas object set to Slice"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "SLICE"



# Auto Boolean operators
class AutoBoolean:
    def execute(self, context):
        canvas = bpy.context.active_object
        brushes = []
        for obj in bpy.context.selected_objects:
            if obj != bpy.context.active_object and (obj.type == "MESH" or obj.type == "CURVE"):
                brushes.append(obj)
                if obj.type == "CURVE":
                    if obj.data.bevel_depth >= 0.001 or obj.data.extrude >= 0.001:
                        convert_to_mesh(obj, canvas)
                    else:
                        brushes.remove(obj)
        
        for brush in brushes:
            mod = canvas.modifiers.new("Auto Boolean", "BOOLEAN") # add modifier
            mod.show_viewport = False
            mod.operation = self.mode
            mod.object = brush
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(brush) # delete brush
                    
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "At least two objects must be selected")
            return {"CANCELLED"}

        return self.execute(context)


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_union"
    bl_label = "Bool Tool Union"
    bl_description = "Combine selected objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "UNION"

class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_difference"
    bl_label = "Bool Tool Difference"
    bl_description = "Subtract selected objects from active object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "DIFFERENCE"

class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.bool_tool_auto_intersect"
    bl_label = "Bool Tool Intersect"
    bl_description = "Keep only intersecting geometry"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    mode = "INTERSECT"

class OBJECT_OT_boolean_auto_slice(bpy.types.Operator):
    bl_idname = "object.bool_tool_auto_slice"
    bl_label = "Bool Tool Slice"
    bl_description = "Slice active object along the selected objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    def boolean_mod(self, obj, ob, mode, ob_delete=True):
        mod = obj.modifiers.new("Auto Boolean", "BOOLEAN")
        mod.operation = mode
        mod.object = ob

        context_override = {'object': obj}
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.modifier_apply(modifier=mod.name)

        if ob_delete:
            bpy.data.objects.remove(ob)
            
    def execute(self, context):
        space_data = context.space_data
        is_local_view = bool(space_data.local_view)
        canvas = bpy.context.active_object
#        canvas.select_set(False)
        
        brushes = []
        for obj in bpy.context.selected_objects:
            if obj != bpy.context.active_object and (obj.type == "MESH" or obj.type == "CURVE"):
                brushes.append(obj)
                if obj.type == "CURVE":
                    if obj.data.bevel_depth >= 0.001 or obj.data.extrude >= 0.001:
                        convert_to_mesh(obj, canvas)
                    else:
                        brushes.remove(obj)

        for brush in brushes:
            # Copy Canvas
            canvas_copy = canvas.copy()
            canvas_copy.data = canvas.data.copy()
            for coll in canvas.users_collection:
                coll.objects.link(canvas_copy)
            if is_local_view:
                canvas_copy.local_view_set(space_data, True)

            self.boolean_mod(canvas, brush, "DIFFERENCE", ob_delete=False)
            self.boolean_mod(canvas_copy, brush, "INTERSECT")
            
            canvas_copy.select_set(True)

            context.view_layer.objects.active = canvas_copy

        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "At least two objects must be selected")
            return {"CANCELLED"}

        return self.execute(context)



# Brush Utility Operators
class OBJECT_OT_toggle_boolean_brush(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_brush"
    bl_label = "Toggle Boolean Brush"
    bl_description = "Toggles the selected boolean brush effect on the canvas objects"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isBrush(context.active_object)

    def execute(self, context):
        # Define Brushes
        brushes = []
        for obj in bpy.context.selected_objects:
            if isBrush(context.active_object):
                brushes.append(obj)
        
        # Find Canvas
        canvas = find_canvas(context, brushes)

        set = "None"
        for obj in canvas:
            boolean_slice = obj.get("Boolean Slice")
            if boolean_slice is not None and boolean_slice == True:
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    if obj.hide_viewport == False:
                        obj.hide_viewport = True
                        obj.hide_render = True
                    else:
                        obj.hide_viewport = False
                        obj.hide_render = False
                
            for mod in obj.modifiers:
                if "Bool Tool " in mod.name:
                    if mod.object in brushes:
                        if set == "None":
                            if mod.show_viewport:
                                mod.show_viewport = False
                                mod.show_render = False
                            else:
                                mod.show_viewport = True
                                mod.show_render = True
                        else:
                            if set == "True":
                                mod.show_viewport = True
                            else:
                                mod.show_viewport = False
        return {"FINISHED"}


class OBJECT_OT_remove_boolean_brush(bpy.types.Operator):
    bl_idname = "object.remove_boolean_brush"
    bl_label = "Remove Boolean Brush"
    bl_description = "Removes boolean brush properties from selected objects"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isBrush(context.active_object)

    def execute(self, context):
        # Define Brushes
        brushes = []
        for obj in bpy.context.selected_objects:
            if isBrush(context.active_object):
                brushes.append(obj)
        
        # Find Canvas
        canvas = find_canvas(context, brushes)

        for obj in canvas:
            slice_obj = False
            for mod in obj.modifiers:
                if "Bool Tool " in mod.name:
                    if mod.object in brushes:
                        slice_obj = True
                        obj.modifiers.remove(mod)
            boolean_slice = obj.get("Boolean Slice")
            if boolean_slice is not None and boolean_slice == True:
                if slice_obj:
                    bpy.data.objects.remove(obj)

        for brush in brushes:
            brush.display_type = "TEXTURED"
            del brush["Boolean Brush"]
            object_visibility_set(brush, value=True)
            brush.hide_render = False
        
        return {"FINISHED"}


class OBJECT_OT_apply_boolean_brush(bpy.types.Operator):
    bl_idname = "object.apply_boolean_brush"
    bl_label = "Apply Boolean Brush"
    bl_description = "Apply this boolean brush to the every canvas that uses it"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isBrush(context.active_object)

    def execute(self, context):
        # Define Brushes
        brushes = []
        for obj in bpy.context.selected_objects:
            if isBrush(context.active_object):
                brushes.append(obj)
        
        # Find Canvas
        canvas = find_canvas(context, brushes)
                
        for obj in canvas:
            for mod in obj.modifiers:
                if "Bool Tool " in mod.name:
                    if mod.object in brushes:
                        context.view_layer.objects.active = obj
                        try:
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                        except:
                            context.active_object.data = context.active_object.data.copy()
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                        bpy.ops.object.select_all(action="TOGGLE")
                        bpy.ops.object.select_all(action="DESELECT")

        # Garbage Collector
        for brush in brushes:
            brush.select_set(True)
            bpy.ops.object.delete()
        return {"FINISHED"}



# Canvas Utility Operators
class OBJECT_OT_toggle_boolean_all(bpy.types.Operator):
    bl_idname = "object.toggle_boolean_all"
    bl_label = "Toggle Boolean Brushes"
    bl_description = "Toggles all boolean brush effects on active canvas"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isCanvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if "Boolean Canvas" in obj]

        brushes = set()
        for obj in canvas:
            brushes.update(i.object for i in obj.modifiers if i.type == "BOOLEAN" and "Bool Tool " in i.name)
        brushes = list(brushes)

        for brush in brushes:
            if brush.hide_viewport == False:
                brush.hide_viewport = True
            else:
                brush.hide_viewport = False
            
        return {"FINISHED"}


class OBJECT_OT_remove_boolean_all(bpy.types.Operator):
    bl_idname = "object.remove_boolean_all"
    bl_label = "Bool Tool Remove"
    bl_description = "Removes all Bool Tool config assigned to it"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isCanvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if "Boolean Canvas" in obj]

        brushes = set()
        for obj in canvas:
            brushes.update(i.object for i in obj.modifiers if i.type == "BOOLEAN" and "Bool Tool " in i.name)
        brushes = list(brushes)

        # Remove Slices
        slices = find_slices(self, context, brushes)
        for obj in slices:
            bpy.data.objects.remove(obj)
            if obj in canvas:
                canvas.remove(obj)

        # Remove Modifiers
        for obj in canvas:
            for mod in obj.modifiers:
                if "Bool Tool " in mod.name:
                    if mod.object in brushes:
                        obj.modifiers.remove(mod)
            del obj["Boolean Canvas"]
            
            if obj.get("Boolean Slice"):
                bpy.data.objects.remove(obj)
                
        # Free Brushes that No Longe Have Canvases
        other_canvas = find_canvas(context, brushes)
        for obj in other_canvas:
            if obj in canvas:
                other_canvas.remove(obj)
            else:
                if any(modifier.object in brushes for modifier in obj.modifiers):
                    brushes[:] = [brush for brush in brushes if brush not in [modifier.object for modifier in obj.modifiers]]
        
        for obj in brushes:
            obj.display_type = "TEXTURED"
            obj.hide_render = False
            object_visibility_set(obj, value=True)
            if obj.get("Boolean Brush"):
                del obj["Boolean Brush"]
        
        return {"FINISHED"}


class OBJECT_OT_apply_boolean_all(bpy.types.Operator):
    bl_idname = "object.apply_boolean_all"
    bl_label = "Apply All Boolean Brushes"
    bl_description = "Apply all boolean brushes of selected canvas objects"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH' and isCanvas(context.active_object)

    def execute(self, context):
        canvas = [obj for obj in bpy.context.selected_objects if "Boolean Canvas" in obj]

        brushes = set()
        for obj in canvas:
            brushes.update(i.object for i in obj.modifiers if i.type == "BOOLEAN" and "Bool Tool " in i.name)
        brushes = list(brushes)
        
        slices = find_slices(self, context, brushes)
        
        # Apply Modifiers
        for obj in itertools.chain(canvas, slices):
            for mod in obj.modifiers:
                if "Bool Tool " in mod.name:
                    bpy.context.view_layer.objects.active = obj
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except:
                        context.active_object.data = context.active_object.data.copy()
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        
            del obj["Boolean Canvas"]
            if obj.get("Boolean Slice"):
                del obj["Boolean Slice"]
        
        # Delete Brushes that No Longer Have Canvases
        other_canvas = find_canvas(context, brushes)
        for obj in other_canvas:
            if obj not in canvas:
                if obj not in slices:
                    if any(modifier.object in brushes for modifier in obj.modifiers):
                        brushes[:] = [brush for brush in brushes if brush not in [modifier.object for modifier in obj.modifiers]]
        
        for obj in brushes:
            bpy.data.objects.remove(obj)
        
        return {"FINISHED"}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_boolean_auto_union,
    OBJECT_OT_boolean_auto_difference,
    OBJECT_OT_boolean_auto_intersect,
    OBJECT_OT_boolean_auto_slice,
    
    OBJECT_OT_toggle_boolean_brush,
    OBJECT_OT_toggle_boolean_all,
    OBJECT_OT_remove_boolean_brush,
    OBJECT_OT_remove_boolean_all,
    OBJECT_OT_apply_boolean_all,
    OBJECT_OT_apply_boolean_brush,
    
    OBJECT_OT_boolean_brush_union,
    OBJECT_OT_boolean_brush_difference,
    OBJECT_OT_boolean_brush_intersect,
    OBJECT_OT_boolean_brush_slice,
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