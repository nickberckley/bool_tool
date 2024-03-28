import bpy


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
    


#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
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