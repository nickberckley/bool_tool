import bpy
import itertools
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
    is_canvas,
    destructive_op_confirmation,
)
from ..functions.misc import (
    _guess_toggle_state,
)
from ..functions.modifier import (
    apply_modifiers,
)
from ..functions.object import (
    object_visibility_set,
    delete_empty_collection,
    delete_cutter,
    restore_cutter,
    change_parent,
)
from ..functions.list import (
    list_canvas_slices,
    list_canvas_cutters,
    list_cutter_users,
    list_selected_canvases,
    list_unused_cutters,
    list_pre_boolean_modifiers,
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
        slices = list_canvas_slices(canvases)

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
                if mod.type == 'BOOLEAN' and mod.object in cutters:
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
        slices = list_canvas_slices(canvases)

        # Remove Slices
        for slice in slices:
            if slice in canvases:
                canvases.remove(slice)
            delete_cutter(slice)

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
                    delete_cutter(cutter)
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
    bl_description = "Apply all boolean cutters on selected canvases"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)


    def invoke(self, context, event):
        # Filter canvases.
        self.canvases = list_selected_canvases(context)
        if len(self.canvases) == 0:
            self.report({'WARNING'}, "No valid canvases selected")
            return {'CANCELLED'}

        return destructive_op_confirmation(self, context, event, self.canvases, title="Apply Boolean Cutters")


    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences

        cutters, __ = list_canvas_cutters(self.canvases)
        slices = list_canvas_slices(self.canvases)

        # Select all faces of the cutter so that newly created faces in canvas
        # are also selected after applying the modifier.
        for cutter in cutters:
            for face in cutter.data.polygons:
                face.select = True

        for canvas in itertools.chain(self.canvases, slices):
            context.view_layer.objects.active = canvas

            # Apply Modifiers
            if prefs.apply_order == 'ALL':
                modifiers = [mod for mod in canvas.modifiers]
            elif prefs.apply_order == 'BEFORE':
                modifiers = list_pre_boolean_modifiers(canvas)
            elif prefs.apply_order == 'BOOLEANS':
                modifiers = [mod for mod in canvas.modifiers if mod.type == 'BOOLEAN']

            apply_modifiers(context, canvas, modifiers)

            # remove_boolean_properties
            canvas.booleans.canvas = False
            canvas.booleans.slice = False


        # Purge Orphaned Cutters
        unused_cutters, leftovers = list_unused_cutters(cutters, self.canvases, slices, do_leftovers=True)

        purged_cutters = []
        for cutter in unused_cutters:
            if cutter not in purged_cutters:
                # Transfer Children
                for child in cutter.children:
                    change_parent(context, child, cutter.parent)

                # Purge
                delete_cutter(cutter)
                purged_cutters.append(cutter)

        # purge_empty_collection
        if prefs.use_collection:
            delete_empty_collection()


        # Change Leftover Cutter Parent
        if prefs.parent:
            for cutter in leftovers:
                if cutter.parent in self.canvases:
                    other_canvases = list_cutter_users([cutter]).keys()
                    change_parent(context, cutter, list(other_canvases)[0])

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
