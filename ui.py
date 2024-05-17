import bpy


# #### ------------------------------ FUNCTIONS ------------------------------ ####

def update_sidebar_category(self, context):
    try:
        bpy.utils.unregister_class(VIEW3D_PT_boolean)
        bpy.utils.unregister_class(VIEW3D_PT_boolean_properties)
    except:
        pass

    VIEW3D_PT_boolean.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean)
    
    VIEW3D_PT_boolean_properties.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean_properties)



# #### ------------------------------ UI ------------------------------ ####

def boolean_operators_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    col.operator('object.bool_tool_auto_difference', text="Difference", icon="SELECT_SUBTRACT")
    col.operator('object.bool_tool_auto_union', text="Union", icon="SELECT_EXTEND")
    col.operator('object.bool_tool_auto_intersect', text="Intersect", icon="SELECT_INTERSECT")
    col.operator('object.bool_tool_auto_slice', text="Slice", icon="SELECT_DIFFERENCE")

    col.separator()
    col.label(text="Brush Boolean")
    col.operator('object.bool_tool_brush_difference', text="Difference", icon="SELECT_SUBTRACT")
    col.operator('object.bool_tool_brush_union', text="Union", icon="SELECT_EXTEND")
    col.operator('object.bool_tool_brush_intersect', text="Intersect", icon="SELECT_INTERSECT")
    col.operator('object.bool_tool_brush_slice', text="Slice", icon="SELECT_DIFFERENCE")


def boolean_extras_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    # canvas_operators
    active_object = context.active_object
    if "Boolean Canvas" in active_object and any(modifier.name.startswith('boolean_') for modifier in active_object.modifiers):
        col.separator()
        col.operator('object.toggle_boolean_all', text="Toggle All Cuters")
        col.operator('object.apply_boolean_all', text="Apply All Cutters")
        col.operator('object.remove_boolean_all', text="Remove All Cutters")

    # cutter_operators
    if "Boolean Brush" in active_object:
        col.separator()
        col.operator('object.toggle_boolean_brush', text="Toggle Cutter")
        col.operator('object.apply_boolean_brush', text="Apply Cutter")
        col.operator('object.remove_boolean_brush', text="Remove Cutter")



#### ------------------------------ PANELS ------------------------------ ####

# Boolean Operators Panel
class VIEW3D_PT_boolean(bpy.types.Panel):
    bl_label = "Boolean"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        preferences = bpy.context.preferences.addons[__package__].preferences
        return preferences.show_in_sidebar

    def draw(self, context):
        boolean_operators_menu(self, context)


# Properties Panel
class VIEW3D_PT_boolean_properties(bpy.types.Panel):
    bl_label = "Properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        preferences = bpy.context.preferences.addons[__package__].preferences
        return preferences.show_in_sidebar and context.active_object and ("Boolean Brush" in context.active_object or "Boolean Canvas" in context.active_object)

    def draw(self, context):
        boolean_extras_menu(self, context)



#### ------------------------------ MENUS ------------------------------ ####

# Object Mode Menu
class VIEW3D_MT_boolean(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean"

    def draw(self, context):
        boolean_operators_menu(self, context)
        boolean_extras_menu(self, context)


def bool_tool_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu('VIEW3D_MT_boolean')


def boolean_select_menu(self, context):
    layout = self.layout
    active_obj = context.active_object
    if active_obj:
        if "Boolean Canvas" in active_obj or "Boolean Brush" in active_obj:
            layout.separator()

        if "Boolean Canvas" in active_obj:
            layout.operator('object.select_boolean_all', text="Select Boolean Cutters")
        if "Boolean Brush" in active_obj:
            layout.operator('object.select_cutter_canvas', text="Select Boolean Canvas")



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    VIEW3D_MT_boolean,
    VIEW3D_PT_boolean,
    VIEW3D_PT_boolean_properties,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # sidebar_category
    prefs = bpy.context.preferences.addons[__package__].preferences
    update_sidebar_category(prefs, bpy.context)
    
    # MENU
    bpy.types.VIEW3D_MT_object.append(bool_tool_menu)
    bpy.types.VIEW3D_MT_select_object.append(boolean_select_menu)

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
    bpy.types.VIEW3D_MT_select_object.remove(boolean_select_menu)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()