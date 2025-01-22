import bpy
from ... import __package__ as base_package


#### ------------------------------ /toolbar/ ------------------------------ ####

def carver_ui_common(context, layout, props):
    """Common tool properties for all Carver tools"""

    layout.prop(props, "mode", text="")
    layout.prop(props, "depth", text="")
    layout.prop(props, "solver", expand=True)

    # Popovers
    layout.popover("TOPBAR_PT_carver_shape", text="Shape")
    layout.popover("TOPBAR_PT_carver_array", text="Array")
    layout.popover("TOPBAR_PT_carver_cutter", text="Cutter")



#### ------------------------------ /popovers/ ------------------------------ ####

class TOPBAR_PT_carver_shape(bpy.types.Panel):
    bl_label = "Carver Shape"
    bl_idname = "TOPBAR_PT_carver_shape"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        prefs = context.preferences.addons[base_package].preferences
        tool = context.workspace.tools.from_space_view3d_mode('OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH')

        # Box
        if tool.idname == "object.carve_box" or tool.idname == "object.carve_circle":
            props = tool.operator_properties("object.carve_box")

            if tool.idname == "object.carve_circle":
                layout.prop(props, "subdivision", text="Vertices")
            layout.prop(props, "rotation")
            layout.prop(props, "aspect", expand=True)
            layout.prop(props, "origin", expand=True)

            # bevel
            if tool.idname == 'object.carve_box':
                layout.separator()
                layout.prop(props, "use_bevel", text="Bevel")
                col = layout.column(align=True)
                row = col.row(align=True)
                if prefs.experimental:
                    row.prop(props, "bevel_profile", text="Profile", expand=True)
                col.prop(props, "bevel_segments", text="Segments")
                col.prop(props, "bevel_radius", text="Radius")

                if props.use_bevel == False:
                    col.enabled = False

        # Polyline
        elif tool.idname == "object.carve_polyline":
            props = tool.operator_properties("object.carve_polyline")
            layout.prop(props, "closed")


class TOPBAR_PT_carver_array(bpy.types.Panel):
    bl_label = "Carver Array"
    bl_idname = "TOPBAR_PT_carver_array"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        tool = context.workspace.tools.from_space_view3d_mode('OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH')
        if tool.idname == "object.carve_box" or tool.idname == "object.carve_circle":
            props = tool.operator_properties("object.carve_box")
        elif tool.idname == "object.carve_polyline":
            props = tool.operator_properties("object.carve_polyline")

        # Rows
        col = layout.column(align=True)
        col.prop(props, "rows")
        row = col.row(align=True)
        row.prop(props, "rows_direction", text="Direction", expand=True)
        col.prop(props, "rows_gap", text="Gap")

        # Columns
        layout.separator()
        col = layout.column(align=True)
        col.prop(props, "columns")
        row = col.row(align=True)
        row.prop(props, "columns_direction", text="Direction", expand=True)
        col.prop(props, "columns_gap", text="Gap")


class TOPBAR_PT_carver_cutter(bpy.types.Panel):
    bl_label = "Carver Cutter"
    bl_idname = "TOPBAR_PT_carver_cutter"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        tool = context.workspace.tools.from_space_view3d_mode('OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH')
        if tool.idname == "object.carve_box" or tool.idname == "object.carve_circle":
            props = tool.operator_properties("object.carve_box")
        elif tool.idname == "object.carve_polyline":
            props = tool.operator_properties("object.carve_polyline")

        # modifier_&_cutter
        col = layout.column()
        col.prop(props, "pin", text="Pin Modifier")
        if props.mode == 'MODIFIER':
            col.prop(props, "parent")
            col.prop(props, "hide")

        # auto_smooth
        layout.separator()
        col = layout.column(align=True)
        col.prop(props, "auto_smooth", text="Auto Smooth")
        col.prop(props, "sharp_angle")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    TOPBAR_PT_carver_shape,
    TOPBAR_PT_carver_array,
    TOPBAR_PT_carver_cutter,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
