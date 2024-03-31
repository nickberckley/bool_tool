import bpy


#### ------------------------------ MENUS ------------------------------ ####

class VIEW3D_MT_boolean(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Auto Boolean")
        layout.operator('object.bool_tool_auto_difference', text="Difference", icon="SELECT_SUBTRACT")
        layout.operator('object.bool_tool_auto_union', text="Union", icon="SELECT_EXTEND")
        layout.operator('object.bool_tool_auto_intersect', text="Intersect", icon="SELECT_INTERSECT")
        layout.operator('object.bool_tool_auto_slice', text="Slice", icon="SELECT_DIFFERENCE")

        layout.separator()
        layout.label(text="Brush Boolean")
        layout.operator('object.bool_tool_brush_difference', text="Difference", icon="SELECT_SUBTRACT")
        layout.operator('object.bool_tool_brush_union', text="Union", icon="SELECT_EXTEND")
        layout.operator('object.bool_tool_brush_intersect', text="Intersect", icon="SELECT_INTERSECT")
        layout.operator('object.bool_tool_brush_slice', text="Slice", icon="SELECT_DIFFERENCE")

        # canvas_operators
        active_object = context.active_object
        if "Boolean Canvas" in active_object and any(modifier.name.startswith('boolean_') for modifier in active_object.modifiers):
            layout.separator()
            layout.operator('object.toggle_boolean_all', text="Toggle All")
            layout.operator('object.apply_boolean_all', text="Apply All")
            layout.operator('object.remove_boolean_all', text="Remove All")

        # cutter_operators
        if "Boolean Brush" in active_object:
            layout.separator()
            layout.operator('object.toggle_boolean_brush', text="Toggle Cutter")
            layout.operator('object.apply_boolean_brush', text="Apply Cutter")
            layout.operator('object.remove_boolean_brush', text="Remove Cutter")


def bool_tool_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu('VIEW3D_MT_boolean')



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    VIEW3D_MT_boolean,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # MENU
    bpy.types.VIEW3D_MT_object.append(bool_tool_menu)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")
    kmi = km.keymap_items.new("wm.call_menu", 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = "VIEW3D_MT_boolean"
    kmi.active = True
    addon_keymaps.append(km)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.remove(bool_tool_menu)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()