import bpy
import itertools
from .. import __package__ as base_package

from ..functions.poll import (
    basic_poll,
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
    list_canvases,
    list_selected_cutters,
    list_canvas_cutters,
    list_canvas_slices,
    list_cutter_users,
)


#### ------------------------------ OPERATORS ------------------------------ ####

# Toggle Boolean Cutter
class OBJECT_OT_boolean_toggle_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_toggle_cutter"
    bl_label = "Toggle Boolean Cutter"
    bl_description = "Toggle this boolean cutter. If cutter is the active object it will be toggled for every canvas that uses it"
    bl_options = {'UNDO'}

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )
    specified_modifier: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def execute(self, context):
        # Create lists of cutters & canvases.
        if self.method == 'SPECIFIED':
            cutters = [context.scene.objects[self.specified_cutter]]
            canvases = [context.scene.objects[self.specified_canvas]]
            modifiers = [canvases[0].modifiers.get(self.specified_modifier)]
            slices = list_canvas_slices(canvases)
        elif self.method == 'ALL':
            cutters = list_selected_cutters(context)
            canvases = list_cutter_users(cutters)
            modifiers = list(itertools.chain.from_iterable(canvases.values()))

        if len(cutters) == 0:
            self.report({'INFO'}, "Boolean cutters are not selected")
            return {'CANCELLED'}

        if not canvases:
            return {'CANCELLED'}

        state = _guess_toggle_state(modifiers)
        state = True if state == "On" else False

        # Toggle Modifiers
        for mod in modifiers:
            mod.show_viewport = not state
            mod.show_render = not state

        # Hide Slices
        if self.method == 'ALL':
            for canvas in canvases:
                if canvas.booleans.slice == True:
                    slice = canvas
                    if any(modifier.object in cutters for modifier in slice.modifiers):
                        slice.hide_viewport = state
                        slice.hide_render = state
                        slice.hide_set(state)

        elif self.method == 'SPECIFIED':
            for slice in slices:
                for mod in slice.modifiers:
                    if mod.type == 'BOOLEAN' and mod.object in cutters:
                        mod.show_viewport = not state
                        mod.show_render = not state

                        slice.hide_viewport = state
                        slice.hide_render = state
                        slice.hide_set(state)

            # Hide Unused Cutters
            for cutter in cutters:
                other_canvases = list_cutter_users([cutter], exclude=canvases + slices).keys()
                if len(other_canvases) == 0:
                    cutter.hide_viewport = state
                    cutter.hide_set(state)

        return {'FINISHED'}


# Remove Boolean Cutter
class OBJECT_OT_boolean_remove_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_remove_cutter"
    bl_label = "Remove Boolean Cutter"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if properties.specified_cutter:
            return ("Remove this cutter and the Boolean modifier that uses it.\n"
                    "If the cutter is not used by any other canvas it will be deleted from the scene")
        else:
            return ("Remove selected Boolean cutters from all canvases that uses them; restore their visibility")

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )

    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )
    specified_modifier: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences

        # Create lists of cutters & canvases.
        if self.method == 'SPECIFIED':
            cutters = [context.scene.objects[self.specified_cutter]]
            canvases = {
                context.scene.objects[self.specified_canvas]:
                [context.scene.objects[self.specified_canvas].modifiers.get(self.specified_modifier)]
            }
        elif self.method == 'ALL':
            cutters = list_selected_cutters(context)
            canvases = list_cutter_users(cutters)

        if len(cutters) == 0:
            self.report({'INFO'}, "Boolean cutters are not selected")
            return {'CANCELLED'}

        if not canvases:
            return {'CANCELLED'}

        # Remove Slices
        slices = list_canvas_slices(canvases.keys())
        for slice in slices:
            for mod in slice.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in cutters:
                    if slice in canvases:
                        del canvases[slice]
                    delete_cutter(slice)

        for canvas, modifiers in canvases.items():
            # Remove Modifiers
            for mod in modifiers:
                canvas.modifiers.remove(mod)

            # Unset canvas property if it's no longer needed.
            other_cutters, __ = list_canvas_cutters([canvas])
            if len(other_cutters) == 0:
                canvas.booleans.canvas = False

        if self.method == 'SPECIFIED':
            other_canvases = list_cutter_users(cutters, exclude=list(canvases.keys())).keys()
            if len(other_canvases) == 0:
                # Delete Unused Cutters
                delete_cutter(cutters[0])
            else:
                # Change Cutter Parent
                if prefs.parent and cutters[0].parent in canvases:
                    new_parent = next(c for c in other_canvases if not c.booleans.slice)
                    change_parent(context, cutters[0], new_parent, inverse=True)

        elif self.method == 'ALL':
            for cutter in cutters:
                # Restore Unused Cutters
                restore_cutter(context, cutter,
                                unparent=prefs.parent and cutter.parent in canvases,
                                unlink_collection=prefs.use_collection)

        # Purge Empty Collection
        if prefs.use_collection:
            delete_empty_collection()

        return {'FINISHED'}


# Apply Boolean Cutter
class OBJECT_OT_boolean_apply_cutter(bpy.types.Operator):
    bl_idname = "object.boolean_apply_cutter"
    bl_label = "Apply Boolean Cutter"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if properties.specified_cutter:
            return ("Apply the modifier using this Boolean cutter")
        else:
            return ("Apply this Boolean cutter to every canvas object that uses it")

    method: bpy.props.EnumProperty(
        name = "Method",
        items = (('ALL', "All", "Remove cutter from all canvases that use it"),
                 ('SPECIFIED', "Specified", "Remove cutter from specified canvas")),
        default = 'ALL',
    )
    specified_cutter: bpy.props.StringProperty(
    )
    specified_canvas: bpy.props.StringProperty(
    )

    delete: bpy.props.BoolProperty(
        name = "Delete Unused Cutter",
        description = "Completely remove the cutter object if it's not used by any other canvas",
        default = True,
    )

    @classmethod
    def poll(cls, context):
        return basic_poll(cls, context, check_active=False)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "delete")

    def invoke(self, context, event):
        # Filter Objects
        if self.method == 'SPECIFIED':
            canvases = [context.scene.objects[self.specified_canvas]]
        elif self.method == 'ALL':
            cutters = list_selected_cutters(context)
            canvases = list_cutter_users(cutters).keys()

        return destructive_op_confirmation(self, context, event, canvases, title="Apply Boolean Cutter")

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        # Create lists of cutters & canvases.
        if self.method == 'SPECIFIED':
            cutters = [context.scene.objects[self.specified_cutter]]
            canvases = [context.scene.objects[self.specified_canvas]]
            slices = list_canvas_slices(canvases)
        elif self.method == 'ALL':
            cutters = list_selected_cutters(context)
            canvases = list_cutter_users(cutters).keys()
            slices = []

        if len(cutters) == 0:
            self.report({'INFO'}, "Boolean cutters are not selected")
            return {'CANCELLED'}

        if not canvases:
            return {'CANCELLED'}

        # Select all faces of the cutter so that newly created faces in canvas
        # are also selected after applying the modifier.
        for cutter in cutters:
            for face in cutter.data.polygons:
                face.select = True

        # Apply Modifiers
        for canvas in itertools.chain(canvases, slices):
            boolean_mods = []
            for mod in canvas.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in cutters:
                    boolean_mods.append(mod)

            if boolean_mods:
                cutters_list_index = canvas.booleans.modifiers_list_index
                apply_modifiers(context, canvas, boolean_mods)
                canvas.booleans.modifiers_list_index = cutters_list_index - 1

                # Unset canvas property if it's no longer needed.
                other_cutters, __ = list_canvas_cutters([canvas])
                if len(other_cutters) == 0:
                    canvas.booleans.canvas = False
                canvas.booleans.slice = False
                canvas.booleans.slice_of = None

        for cutter in cutters:
            other_canvases = list_cutter_users([cutter], exclude=canvases).keys()
            if len(other_canvases) == 0:
                # Delete Unused Cutters
                if self.delete:
                    delete_cutter(cutter)

                # Restore Unused Cutters
                else:
                    restore_cutter(context, cutter,
                                   unparent=prefs.parent and cutter.parent in canvases,
                                   unlink_collection=prefs.use_collection)
            else:
                # Change Cutter Parent
                if prefs.parent and cutters[0].parent in canvases:
                    new_parent = next(c for c in other_canvases if not c.booleans.slice)
                    change_parent(context, cutters[0], new_parent, inverse=True)

        # Purge Empty Collection
        if prefs.use_collection:
            delete_empty_collection()

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_boolean_toggle_cutter,
    OBJECT_OT_boolean_remove_cutter,
    OBJECT_OT_boolean_apply_cutter,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("object.boolean_apply_cutter", 'NUMPAD_ENTER', 'PRESS', ctrl=True)
    kmi.properties.method = 'ALL'
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
