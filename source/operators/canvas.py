import bpy
import itertools
from .. import __package__ as base_package

from ..functions.canvas import (
    list_selected_canvases,
    list_canvas_cutters,
    list_canvas_slices,
)
from ..functions.cutter import (
    list_cutter_users,
    restore_cutter,
)
from ..functions.modifier import (
    apply_modifiers,
    get_modifiers_to_apply,
    is_boolean_modifier,
)
from ..functions.object import (
    change_parent,
    delete_object,
)
from ..functions.poll import (
    basic_poll,
    destructive_op_confirmation,
    _guess_toggle_state,
)
from ..functions.scene import (
    delete_empty_collection,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle All Cutters
class OBJECT_OT_boolean_toggle_all(bpy.types.Operator):
    bl_idname = "object.boolean_toggle_all"
    bl_label = "Toggle Boolean Cutters"
    bl_description = "Toggle all boolean cutters affecting selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def execute(self, context):
        # Filter canvases.
        canvases = list_selected_canvases(context)
        if len(canvases) == 0:
            self.report({'WARNING'}, "No valid canvases selected")
            return {'CANCELLED'}

        cutters, modifiers = list_canvas_cutters(canvases)
        modifiers = list(itertools.chain.from_iterable(modifiers.values()))
        slices = list_canvas_slices(context, canvases)

        state = _guess_toggle_state(modifiers)
        state = True if state == "On" else False

        # Toggle Modifiers
        for mod in modifiers:
            mod.show_viewport = not state
            mod.show_render = not state

        # Hide Slices
        for slice in slices:
            slice.hide_viewport = state
            slice.hide_render = state
            slice.hide_set(state)
            for mod in slice.modifiers:
                if not is_boolean_modifier(mod):
                    continue
                if mod.object in cutters:
                    mod.show_viewport = not state
                    mod.show_render = not state

        # Hide Unused Cutters
        for cutter in cutters:
            other_canvases = list_cutter_users([cutter], exclude=canvases + slices).keys()
            if len(other_canvases) == 0:
                cutter.hide_viewport = state
                cutter.hide_set(state)

        return {'FINISHED'}


# Remove All Cutters
class OBJECT_OT_boolean_remove_all(bpy.types.Operator):
    bl_idname = "object.boolean_remove_all"
    bl_label = "Remove Boolean Cutters"
    bl_description = "Remove all boolean cutters from selected canvases"
    bl_options = {'REGISTER', 'UNDO'}

    delete_cutters: bpy.props.BoolProperty(
        name = "Delete Unused Cutters",
        description = "Completely remove cutters if they're not used by any other remaining canvas",
        default = True,
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences

        # Filter canvases.
        canvases = list_selected_canvases(context)
        if len(canvases) == 0:
            self.report({'WARNING'}, "No valid canvases selected")
            return {'CANCELLED'}

        cutters, modifiers = list_canvas_cutters(canvases)
        slices = list_canvas_slices(context, canvases)

        # Remove Slices
        for slice in slices:
            if slice in canvases:
                canvases.remove(slice)
            delete_object(slice)

        # Remove Modifiers
        for canvas, mods in modifiers.items():
            for mod in mods:
                canvas.modifiers.remove(mod)
            canvas.booleans.canvas = False

        for cutter in list(cutters):
            other_canvases = list_cutter_users([cutter], exclude=canvases + slices).keys()
            if len(other_canvases) == 0:
                # Delete Unused Cutters
                if self.delete_cutters or cutter.booleans.carver:
                    delete_object(cutter)
                    continue

                # Restore Unused Cutters
                restore_cutter(context, cutter,
                               unparent=prefs.parent and cutter.parent in canvases,
                               unlink_collection=prefs.use_collection)

            else:
                # Change Cutter Parent
                if prefs.parent and cutter.parent in canvases:
                    new_parent = next(c for c in other_canvases if not c.booleans.slice)
                    change_parent(context, cutter, new_parent, inverse=True)

        # Purge Empty Collection
        if prefs.use_collection:
            delete_empty_collection()

        return {'FINISHED'}


# Apply All Cutters
class OBJECT_OT_boolean_apply_all(bpy.types.Operator):
    bl_idname = "object.boolean_apply_all"
    bl_label = "Apply All Boolean Cutters"
    bl_description = "Apply all Boolean cutters to selected canvases"
    bl_options = {'REGISTER', 'UNDO'}

    delete_cutters: bpy.props.BoolProperty(
        name = "Delete Unused Cutters",
        description = "Completely remove cutters if they're not used by any other remaining canvas",
        default = True,
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def invoke(self, context, event):
        # Filter canvases.
        canvases = list_selected_canvases(context)
        if len(canvases) == 0:
            self.report({'WARNING'}, "No valid canvases selected")
            return {'CANCELLED'}

        return destructive_op_confirmation(self, context, event, canvases, title="Apply Boolean Cutters")

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences

        canvases = list_selected_canvases(context)
        cutters, __ = list_canvas_cutters(canvases)
        slices = list_canvas_slices(context, canvases)

        # Select all faces of the cutter so that newly created faces in canvas
        # are also selected after applying the modifier.
        for cutter in cutters:
            for face in cutter.data.polygons:
                face.select = True

        for canvas in itertools.chain(canvases, slices):
            # Apply Modifiers
            boolean_mods = [mod for mod in canvas.modifiers if is_boolean_modifier(mod)]
            modifiers = get_modifiers_to_apply(context, canvas)
            apply_modifiers(context, canvas, modifiers)

            # Remove Boolean Properties
            canvas.booleans.canvas = False
            canvas.booleans.slice = False
            canvas.booleans.slice_of = None

        for cutter in list(cutters):
            # Delete Unused Cutters
            other_canvases = list_cutter_users([cutter]).keys()
            if len(other_canvases) == 0:
                # Delete Unused Cutters & Transfer Children
                if self.delete_cutters or cutter.booleans.carver:
                    for child in cutter.children:
                        change_parent(context, child, cutter.parent, inverse=True)
                    delete_object(cutter)

                # Restore Unused Cutters
                else:
                    restore_cutter(context, cutter,
                                   unparent=prefs.parent and cutter.parent in canvases,
                                   unlink_collection=prefs.use_collection)
            else:
                # Change Cutter Parent
                if prefs.parent and cutter.parent in canvases:
                    new_parent = next(c for c in other_canvases if not c.booleans.slice)
                    change_parent(context, cutter, new_parent, inverse=True)

        # Purge Empty Collection
        if prefs.use_collection:
            delete_empty_collection()

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_toggle_all,
    OBJECT_OT_boolean_remove_all,
    OBJECT_OT_boolean_apply_all,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("object.boolean_apply_all", 'NUMPAD_ENTER', 'PRESS', shift=True, ctrl=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
