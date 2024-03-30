import bpy
from bpy.app.handlers import persistent
from .functions import (
    add_boolean_modifier,
    list_selected_cutters,
    list_cutter_users,
)

#### ------------------------------ OPERATORS ------------------------------ ####

# Select Boolean Brush
class OBJECT_OT_boolean_cutter_select(bpy.types.Operator):
    bl_idname = "object.boolean_cutter_select"
    bl_label = "Select Boolean Cutter"
    bl_description = ("Select object that is used as boolean cutter by this modifier. \n"
                    "Shift-Click to preserve current selection and make cutter object active")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and bpy.context.mode == 'OBJECT' and bpy.context.active_object.type == 'MESH'

    extend: bpy.props.BoolProperty(
        name = "Extend Selection",
        default = False,
    )

    def execute(self, context):
        if context.area.type == 'PROPERTIES' and context.space_data.context == 'MODIFIER':
            modifier = context.object.modifiers.active
            if modifier and modifier.type == "BOOLEAN":
                cutter = modifier.object
                
                # deselect_everything
                if not self.extend:
                    bpy.ops.object.select_all(action='DESELECT')

                # select_cutter
                cutter.select_set(True)
                context.view_layer.objects.active = cutter

        return {"FINISHED"}

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)


# Duplicate Modifier for Duplicated Cutters
@persistent
def duplicate_boolean_modifier(scene, depsgraph):
    if bpy.context.active_object and bpy.context.active_object.type == "MESH":
        cutters = list_selected_cutters(bpy.context)

        # find_original_cutter
        original_cutters = []
        for cutter in cutters:
            if 'Boolean Brush' in cutter:
                if ".0" in cutter.name:
                    if ".001" in cutter.name:
                        original_name = cutter.name.split('.')[0]
                    else:
                        name, number = cutter.name.rsplit('.', 1)
                        previous_number = str(int(number) - 1).zfill(len(number))
                        original_name = name + '.' + previous_number

                    for obj in bpy.data.objects:
                        if obj.name == original_name:
                            if 'Boolean Brush' in obj:
                                original_cutters.append(obj)

        # duplicate_modifiers
        if original_cutters:
            canvases = list_cutter_users(original_cutters)
            for canvas in canvases:
                if "Boolean Slice" in canvas:
                    return
                
                for cutter in cutters:
                    if canvas == cutter:
                        return

                    if not any(modifier.object == cutter for modifier in canvas.modifiers):
                        for modifier in canvas.modifiers:
                            if modifier.type == "BOOLEAN" and modifier.object in original_cutters:
                                add_boolean_modifier(canvas, cutter, modifier.operation)



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    OBJECT_OT_boolean_cutter_select,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.depsgraph_update_pre.append(duplicate_boolean_modifier)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name='Property Editor', space_type='PROPERTIES')
    kmi = km.keymap_items.new("object.boolean_cutter_select", type='LEFTMOUSE', value='DOUBLE_CLICK')
    kmi.active = True
    addon_keymaps.append(km)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.depsgraph_update_pre.remove(duplicate_boolean_modifier)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()