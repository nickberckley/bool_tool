import bpy
from .functions import is_canvas


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_sidebar_category(self, context):
    try:
        bpy.utils.unregister_class(VIEW3D_PT_boolean)
        bpy.utils.unregister_class(VIEW3D_PT_boolean_properties)
        bpy.utils.unregister_class(VIEW3D_PT_boolean_cutters)
    except:
        pass

    VIEW3D_PT_boolean.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean)

    VIEW3D_PT_boolean_properties.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean_properties)

    VIEW3D_PT_boolean_cutters.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean_cutters)



#### ------------------------------ /ui/ ------------------------------ ####

def boolean_operators_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    col.operator("object.bool_tool_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.bool_tool_auto_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.bool_tool_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.bool_tool_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')

    col.separator()
    col.label(text="Brush Boolean")
    col.operator("object.bool_tool_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.bool_tool_brush_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.bool_tool_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.bool_tool_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')


def boolean_extras_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    # canvas_operators
    active_object = context.active_object
    if active_object.booleans.canvas == True and any(modifier.name.startswith("boolean_") for modifier in active_object.modifiers):
        col.separator()
        col.operator("object.toggle_boolean_all", text="Toggle All Cuters")
        col.operator("object.apply_boolean_all", text="Apply All Cutters")
        col.operator("object.remove_boolean_all", text="Remove All Cutters")

    # cutter_operators
    if active_object.booleans.cutter:
        col.separator()
        col.operator("object.toggle_boolean_brush", text="Toggle Cutter")
        col.operator("object.apply_boolean_brush", text="Apply Cutter")
        col.operator("object.remove_boolean_brush", text="Remove Cutter")



#### ------------------------------ /panels/ ------------------------------ ####

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
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.show_in_sidebar

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
        prefs = bpy.context.preferences.addons[__package__].preferences
        return (prefs.show_in_sidebar and context.active_object
                    and (is_canvas(context.active_object) or context.active_object.booleans.cutter))

    def draw(self, context):
        boolean_extras_menu(self, context)


# Cutters Panel
class VIEW3D_PT_boolean_cutters(bpy.types.Panel):
    bl_label = "Cutters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.show_in_sidebar and context.active_object and is_canvas(context.active_object)

    def draw(self, context):
        canvas = context.active_object
        active_index = canvas.booleans.cutters_active_index
        active_cutter = canvas.booleans.cutters[active_index].cutter

        # ui_list
        row = self.layout.row(align=False)
        col = row.column()
        col.template_list("VIEW3D_UL_boolean_cutters",
            list_id = "Boolean Cutters",
            dataptr = canvas,
            propname = "modifiers",
            active_dataptr = canvas.booleans,
            active_propname = "cutters_active_index",
            rows = 4,
        )

        # buttons
        col = row.column(align=True)
        col.operator("object.apply_boolean_brush", text="", icon='CHECKMARK').specified_cutter = active_cutter.name
        col.operator("object.remove_boolean_brush", text="", icon='X').specified_cutter = active_cutter.name



#### ------------------------------ /menus/ ------------------------------ ####

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
    layout.menu("VIEW3D_MT_boolean")


def boolean_select_menu(self, context):
    layout = self.layout
    active_obj = context.active_object
    if active_obj:
        if active_obj.booleans.canvas == True or active_obj.booleans.cutter:
            layout.separator()

        if active_obj.booleans.canvas == True:
            layout.operator("object.select_boolean_all", text="Select Boolean Cutters")
        if active_obj.booleans.cutter:
            layout.operator("object.select_cutter_canvas", text="Select Boolean Canvas")



#### ------------------------------ /ui_list/ ------------------------------ ####

class VIEW3D_UL_boolean_cutters(bpy.types.UIList):
    """List of boolean cutters for active canvas object"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        # select_&_label
        if item.operation == 'DIFFERENCE':
            icon = 'SELECT_SUBTRACT'
        elif item.operation == 'UNION':
            icon = 'SELECT_EXTEND'
        elif item.operation == 'INTERSECT':
            icon = 'SELECT_INTERSECT'

        row = layout.row(align=True)
        row.label(text="", icon=icon)
        row.label(text=item.object.name)

        # # toggle
        # EnableIcon = "RESTRICT_VIEW_ON"
        # toggle = row.operator("object.toggle_boolean_brush", icon=EnableIcon, text="")
        # toggle.specified_cutter = item.name


    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []

        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        filtered_items = self.get_props_filtered_items()

        for i, item in enumerate(items):
            if not item in filtered_items:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def get_props_filtered_items(self):
        canvas = bpy.context.object
        filtered_cutters = []
        if canvas.booleans.canvas == True:
            for modifier in canvas.modifiers:
                if modifier.type == 'BOOLEAN':
                    if not modifier.object:
                        return
                    else:
                        filtered_cutters.append(modifier)

        return filtered_cutters



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    VIEW3D_MT_boolean,
    VIEW3D_UL_boolean_cutters,
    VIEW3D_PT_boolean,
    VIEW3D_PT_boolean_properties,
    VIEW3D_PT_boolean_cutters,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

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
