import bpy
from .functions.misc import (
    _get_modifier_from_list_index,
)
from .functions.poll import is_canvas


#### ------------------------------ /ui/ ------------------------------ ####

def carve_menu(self, context):
    layout = self.layout
    layout.operator("object.carve_box", text="Box Carve")
    layout.operator("object.carve_circle", text="Circle Carve")
    layout.operator("object.carve_polyline", text="Polyline Carve")


def boolean_operators_menu_simple(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    col.operator("object.boolean_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_auto_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')

    col.separator()
    col.label(text="Brush Boolean")
    col.operator("object.boolean_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_brush_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')


def boolean_operators_menu_expanded(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    row = col.row(align=False)
    row.operator("object.boolean_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
    row.operator("object.boolean_auto_difference", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_auto_union", text="Union", icon='SELECT_EXTEND')
    row.operator("object.boolean_auto_union", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
    row.operator("object.boolean_auto_intersect", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')
    row.operator("object.boolean_auto_slice", text="", icon='UV_SYNC_SELECT').flip=True

    col.separator()
    col.label(text="Brush Boolean")
    row = col.row(align=False)
    row.operator("object.boolean_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
    row.operator("object.boolean_brush_difference", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_brush_union", text="Union", icon='SELECT_EXTEND')
    row.operator("object.boolean_brush_union", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
    row.operator("object.boolean_brush_intersect", text="", icon='UV_SYNC_SELECT').flip=True
    row = col.row(align=False)
    row.operator("object.boolean_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')
    row.operator("object.boolean_brush_slice", text="", icon='UV_SYNC_SELECT').flip=True


def boolean_extras_menu(self, context, cutter_only=False):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    col = layout.column(align=True)

    if context.active_object:
        # Canvas operators
        active_object = context.active_object
        if is_canvas(active_object) and not cutter_only:
            col.separator()
            col.operator("object.boolean_toggle_all", text="Toggle All Cuters")
            col.operator("object.boolean_apply_all", text="Apply All Cutters")
            col.operator("object.boolean_remove_all", text="Remove All Cutters")

        # Cutter operators
        if active_object.booleans.cutter:
            col.separator()
            col.operator("object.boolean_toggle_cutter", text="Toggle Cutter").method='ALL'
            col.operator("object.boolean_apply_cutter", text="Apply Cutter").method='ALL'
            col.operator("object.boolean_remove_cutter", text="Remove Cutter").method='ALL'



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
        prefs = context.preferences.addons[__package__].preferences
        return prefs.show_in_sidebar

    def draw(self, context):
        boolean_operators_menu_expanded(self, context)


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
        prefs = context.preferences.addons[__package__].preferences
        if prefs.show_in_sidebar:
            if context.active_object:
                if is_canvas(context.active_object):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def draw(self, context):
        layout = self.layout
        canvas = context.active_object

        # Cutters List
        row = layout.row()
        col = row.column()
        col.template_list(
            "VIEW3D_UL_boolean_cutters",
            "",
            canvas, "modifiers",
            canvas.booleans, "modifiers_list_index",
            rows=5,
        )

        # Filtr & Operators
        col = row.column(align=True)
        cutters_list_index = canvas.booleans.modifiers_list_index
        mod = _get_modifier_from_list_index(canvas, cutters_list_index)

        # Apply Cutter
        op_apply = col.operator("object.boolean_apply_cutter", text="", icon='CHECKMARK')
        op_apply.method = 'SPECIFIED'
        op_apply.specified_cutter = mod.object.name
        op_apply.specified_canvas = canvas.name

        # Remove Cutter
        op_remove = col.operator("object.boolean_remove_cutter", text="", icon='X')
        op_remove.method = 'SPECIFIED'
        op_remove.specified_cutter = mod.object.name
        op_remove.specified_canvas = canvas.name
        op_remove.specified_modifier = mod.name

        col.separator()
        col.menu("VIEW3D_MT_boolean_specials", icon='DOWNARROW_HLT', text="")


# Helpers Panel
class VIEW3D_PT_boolean_helpers(bpy.types.Panel):
    bl_label = "Helpers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[__package__].preferences
        if not prefs.show_in_sidebar:
            return False
        if not context.active_object:
            return False
        if context.active_object.booleans.cutter:
            return True

        return False

    def draw(self, context):
        boolean_extras_menu(self, context, cutter_only=True)


#### ------------------------------ /ui_list/ ------------------------------ ####

class VIEW3D_UL_boolean_cutters(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        canvas = context.active_object
        mod = item

        # Pick Icon
        if mod.operation == 'DIFFERENCE':
            icon = 'SELECT_SUBTRACT'
        elif mod.operation == 'UNION':
            icon = 'SELECT_EXTEND'
        elif mod.operation == 'INTERSECT':
            icon = 'SELECT_INTERSECT'

        row = layout.row(align=True)
        row.prop(mod.object, "name", text="", icon=icon, emboss=False)

        # Select Cutter
        op_select = row.operator("object.boolean_select_cutter", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op_select.cutter = mod.object.name

        # Toggle Cutter
        icon = 'HIDE_OFF' if mod.show_viewport else 'HIDE_ON'
        op_toggle = row.operator("object.boolean_toggle_cutter", text="", icon=icon, emboss=False)
        op_toggle.method = 'SPECIFIED'
        op_toggle.specified_cutter = mod.object.name
        op_toggle.specified_canvas = canvas.name
        op_toggle.specified_modifier = mod.name


    def filter_items(self, context, data, propname):
        flags = []
        indices = []

        modifiers = getattr(data, propname)
        for mod in modifiers:
            if mod.type == 'BOOLEAN' and mod.object is not None:
                flags.append(self.bitflag_filter_item)
            else:
                flags.append(0)

        # Search Filter
        if self.filter_name:
            filter_name = self.filter_name.lower()
            for i, mod in enumerate(modifiers):
                if flags[i] != self.bitflag_filter_item:
                    continue
                if filter_name not in mod.object.name.lower():
                    flags[i] = 0

        # Invert
        if self.use_filter_invert:
            for i, mod in enumerate(modifiers):
                if mod.type != 'BOOLEAN' or mod.object is None:
                    continue  # don't unhide non-booleans on invert
                flags[i] ^= self.bitflag_filter_item

        # Sort by Name
        indices = list(range(len(modifiers)))
        if self.use_filter_sort_alpha:
            sorted_indices = sorted(range(len(modifiers)),
                                    key=lambda i: modifiers[i].object.name if modifiers[i].object else "")
            indices = [0] * len(modifiers)
            for rank, original_i in enumerate(sorted_indices):
                indices[original_i] = rank

        return flags, indices



#### ------------------------------ MENUS ------------------------------ ####

# Carve Menu
class VIEW3D_MT_carve(bpy.types.Menu):
    bl_label = "Carve"
    bl_idname = "VIEW3D_MT_carve"

    def draw(self, context):
        carve_menu(self, context)


# 3D Viewport (Object Mode) -> Object
class VIEW3D_MT_boolean(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_carve")
        layout.separator()
        boolean_operators_menu_simple(self, context)
        boolean_extras_menu(self, context)


# Shift-Ctrl-B Menu
class VIEW3D_MT_boolean_popup(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean_popup"

    def draw(self, context):
        boolean_operators_menu_simple(self, context)
        boolean_extras_menu(self, context)


# Specials
class VIEW3D_MT_boolean_specials(bpy.types.Menu):
    bl_label = "Boolean Operators"
    bl_idname = "VIEW3D_MT_boolean_specials"

    def draw(self, context):
        boolean_extras_menu(self, context)


def object_mode_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_boolean")


def edit_mode_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_carve")


def boolean_select_menu(self, context):
    layout = self.layout
    active_obj = context.active_object
    if active_obj:
        if active_obj.booleans.canvas == True or active_obj.booleans.cutter:
            layout.separator()

        if active_obj.booleans.canvas == True:
            layout.operator("object.boolean_select_all", text="Boolean Cutters")
        if active_obj.booleans.cutter:
            layout.operator("object.select_cutter_canvas", text="Boolean Canvases")



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    VIEW3D_MT_carve,
    VIEW3D_MT_boolean,
    VIEW3D_MT_boolean_popup,
    VIEW3D_MT_boolean_specials,
    VIEW3D_PT_boolean,
    VIEW3D_PT_boolean_cutters,
    VIEW3D_PT_boolean_helpers,
    VIEW3D_UL_boolean_cutters,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.append(object_mode_menu)
    bpy.types.VIEW3D_MT_select_object.append(boolean_select_menu)
    bpy.types.VIEW3D_MT_edit_mesh.append(edit_mode_menu)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("wm.call_menu", 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = "VIEW3D_MT_boolean_popup"
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.remove(object_mode_menu)
    bpy.types.VIEW3D_MT_select_object.remove(boolean_select_menu)
    bpy.types.VIEW3D_MT_edit_mesh.remove(edit_mode_menu)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
