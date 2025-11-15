import bpy
from collections import defaultdict
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
    is_linked,
    is_instanced_data,
    list_candidate_objects,
    destructive_op_confirmation,
)
from ..functions.modifier import (
    add_boolean_modifier,
    apply_modifiers,
)
from ..functions.object import (
    set_cutter_properties,
    change_parent,
    create_slice,
    delete_cutter,
)
from ..functions.list import (
    list_pre_boolean_modifiers,
)


#### ------------------------------ PROPERTIES ------------------------------ ####

class ModifierProperties():
    material_mode: bpy.props.EnumProperty(
        name = "Materials",
        description = "Method for setting materials on the new faces",
        items = (('INDEX', "Index Based", ("Set the material on new faces based on the order of the material slot lists. If a material doesn't exist on the\n"
                                           "modifier object, the face will use the same material slot or the first if the object doesn't have enough slots.")),
                 ('TRANSFER', "Transfer", ("Transfer materials from non-empty slots to the result mesh, adding new materials as necessary.\n"
                                           "For empty slots, fall back to using the same material index as the operand mesh."))),
        default = 'INDEX',
    )
    use_self: bpy.props.BoolProperty(
        name = "Self Intersection",
        description = "Allow self-intersection in operands",
        default = False,
    )
    use_hole_tolerant: bpy.props.BoolProperty(
        name = "Hole Tolerant",
        description = "Better results when there are holes (slower)",
        default = False,
    )
    double_threshold: bpy.props.FloatProperty(
        name = "Overlap Threshold",
        description = "Threshold for checking overlapping geometry",
        subtype = 'DISTANCE',
        min = 0, max = 1, precision = 12, step = 0.0001,
        default = 0.000001,
    )

    def draw(self, context):
        prefs = context.preferences.addons[base_package].preferences

        layout = self.layout
        layout.use_property_split = True

        if prefs.solver == 'EXACT':
            layout.prop(self, "material_mode")
            layout.prop(self, "use_self")
            layout.prop(self, "use_hole_tolerant")
        elif prefs.solver == 'FLOAT':
            layout.prop(self, "double_threshold")



#### ------------------------------ /brush_boolean/ ------------------------------ ####

class BrushBoolean(ModifierProperties):
    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context)


    def invoke(self, context, event):
        # Abort if there are less than 2 selected objects.
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "Boolean operator needs at least two selected objects")
            return {'CANCELLED'}

        # Abort if active object is linked.
        if is_linked(context, context.active_object):
            self.report({'WARNING'}, "Boolean operators cannot be performed on linked objects")
            return {'CANCELLED'}

        return self.execute(context)


    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        canvas = context.active_object
        cutters = list_candidate_objects(self, context, context.active_object)

        if len(cutters) == 0:
            return {'CANCELLED'}

        # Create slices.
        if self.mode == "SLICE":
            for cutter in cutters:
                """NOTE: Slices need to be created in a separate loop to avoid inheriting boolean modifiers that the operator adds."""
                slice = create_slice(context, canvas, modifier=True)
                add_boolean_modifier(self, context, slice, cutter, "INTERSECT", prefs.solver, pin=prefs.pin)

        for cutter in cutters:
            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            set_cutter_properties(context, canvas, cutter, self.mode, parent=prefs.parent, collection=prefs.use_collection)
            add_boolean_modifier(self, context, canvas, cutter, mode, prefs.solver, pin=prefs.pin)

        canvas.booleans.canvas = True

        return {'FINISHED'}


class OBJECT_OT_boolean_brush_union(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_union"
    bl_label = "Boolean Union (Brush)"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "UNION"


class OBJECT_OT_boolean_brush_intersect(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_intersect"
    bl_label = "Boolean Intersection (Brush)"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "INTERSECT"


class OBJECT_OT_boolean_brush_difference(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_difference"
    bl_label = "Boolean Difference (Brush)"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_brush_slice(bpy.types.Operator, BrushBoolean):
    bl_idname = "object.boolean_brush_slice"
    bl_label = "Boolean Slice (Brush)"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "SLICE"



#### ------------------------------ /auto_boolean/ ------------------------------ ####

class AutoBoolean(ModifierProperties):
    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context)


    def invoke(self, context, event):
        # Abort if there are less than 2 selected objects.
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "Boolean operator needs at least two selected objects")
            return {'CANCELLED'}

        # Abort if active object is linked.
        if is_linked(context, context.active_object):
            self.report({'ERROR'}, "Modifiers cannot be applied to linked object")
            return {'CANCELLED'}

        return destructive_op_confirmation(self, context, event, [context.active_object], title="Auto Boolean")


    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        canvas = context.active_object
        cutters = list_candidate_objects(self, context, context.active_object)
        new_modifiers = defaultdict(list)

        if len(cutters) == 0:
            return {'CANCELLED'}

        # Create slices.
        if self.mode == "SLICE":
            for cutter in cutters:
                """NOTE: Slices need to be created in a separate loop to avoid inheriting boolean modifiers that the operator adds."""
                slice = create_slice(context, canvas)
                modifier = add_boolean_modifier(self, context, slice, cutter, "INTERSECT", prefs.solver, pin=prefs.pin)
                new_modifiers[slice].append(modifier)
                slice.select_set(True)

        for cutter in cutters:
            # Add boolean modifier on canvas.
            mode = "DIFFERENCE" if self.mode == "SLICE" else self.mode
            modifier = add_boolean_modifier(self, context, canvas, cutter, mode, prefs.solver, pin=prefs.pin)
            new_modifiers[canvas].append(modifier)

            # Transfer cutters children to canvas.
            for child in cutter.children:
                change_parent(child, canvas)

            # Select all faces of the cutter so that newly created faces in canvas
            # are also selected after applying the modifier.
            for face in cutter.data.polygons:
                face.select = True

        # Apply modifiers on canvas & slices.
        for obj, modifiers in new_modifiers.items():
            modifiers = self._get_modifiers_to_apply(prefs, obj, modifiers)
            apply_modifiers(context, obj, modifiers)

        # Delete cutters.
        for cutter in cutters:
            delete_cutter(cutter)

        return {'FINISHED'}


    def _get_modifiers_to_apply(self, prefs, obj, new_modifiers) -> list:
        """Returns a list of modifiers that need to be applied based on add-on preferences."""

        if prefs.apply_order == 'ALL':
            modifiers = [mod for mod in obj.modifiers]
        elif prefs.apply_order == 'BOOLEANS':
            modifiers = new_modifiers
        elif prefs.apply_order == 'BEFORE':
            modifiers = list_pre_boolean_modifiers(obj)

        return modifiers


class OBJECT_OT_boolean_auto_union(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_union"
    bl_label = "Boolean Union (Auto)"
    bl_description = "Merge selected objects into active one"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "UNION"


class OBJECT_OT_boolean_auto_difference(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_difference"
    bl_label = "Boolean Difference (Auto)"
    bl_description = "Subtract selected objects from active one"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "DIFFERENCE"


class OBJECT_OT_boolean_auto_intersect(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_intersect"
    bl_label = "Boolean Intersect (Auto)"
    bl_description = "Only keep the parts of the active object that are interesecting selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "INTERSECT"


class OBJECT_OT_boolean_auto_slice(bpy.types.Operator, AutoBoolean):
    bl_idname = "object.boolean_auto_slice"
    bl_label = "Boolean Slice (Auto)"
    bl_description = "Slice active object along the selected ones. Will create slices as separate objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode = "SLICE"



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_brush_union,
    OBJECT_OT_boolean_brush_difference,
    OBJECT_OT_boolean_brush_intersect,
    OBJECT_OT_boolean_brush_slice,

    OBJECT_OT_boolean_auto_union,
    OBJECT_OT_boolean_auto_difference,
    OBJECT_OT_boolean_auto_intersect,
    OBJECT_OT_boolean_auto_slice,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    # Brush Operators
    kmi = km.keymap_items.new("object.boolean_brush_union", 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_difference", 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_intersect", 'NUMPAD_ASTERIX', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_brush_slice", 'NUMPAD_SLASH', 'PRESS', ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    # Auto Operators
    kmi = km.keymap_items.new("object.boolean_auto_union", 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_difference", 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_intersect", 'NUMPAD_ASTERIX', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.boolean_auto_slice", 'NUMPAD_SLASH', 'PRESS', ctrl=True, shift=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
