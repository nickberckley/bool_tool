import bpy, math
from .. import __package__ as base_package

from ..functions.mesh import (
    create_cutter_shape,
    extrude,
    shade_smooth_by_angle,
)
from ..functions.object import (
    add_boolean_modifier,
    set_cutter_properties,
    delete_cutter,
    set_object_origin,
)
from ..functions.select import (
    selection_fallback,
)


#### ------------------------------ OPERATORS ------------------------------ ####

class CarverModifierKeys():
    # Snap
    def modifier_snap(self, context, event):
        self.snap = context.scene.tool_settings.use_snap
        if (self.move == False) and (not hasattr(self, "rotate") or (hasattr(self, "rotate") and not self.rotate)):
            # change_the_snap_increment_value_using_the_wheel_mouse
            for i, a in enumerate(context.screen.areas):
                if a.type == 'VIEW_3D':
                    space = context.screen.areas[i].spaces.active

            if event.type == 'WHEELUPMOUSE':
                    space.overlay.grid_subdivisions -= 1
            elif event.type == 'WHEELDOWNMOUSE':
                    space.overlay.grid_subdivisions += 1

            # invert_snapping
            if event.ctrl:
                self.snap = not self.snap

    # Aspect
    def modifier_aspect(self, context, event):
        if event.shift:
            if self.initial_aspect == 'FREE':
                self.aspect = 'FIXED'
            elif self.initial_aspect == 'FIXED':
                self.aspect = 'FREE'
        else:
            self.aspect = self.initial_aspect

    # Origin
    def modifier_origin(self, context, event):
        if event.alt:
            if self.initial_origin == 'EDGE':
                self.origin = 'CENTER'
            elif self.initial_origin == 'CENTER':
                self.origin = 'EDGE'
        else:
            self.origin = self.initial_origin

    # Rotate
    def modifier_rotate(self, context, event):
        if event.type == 'R':
            if event.value == 'PRESS':
                self.cached_mouse_position = (self.mouse_path[1][0], self.mouse_path[1][1])
                context.window.cursor_set("NONE")
                self.rotate = True
            elif event.value == 'RELEASE':
                context.window.cursor_set("MUTE")
                context.window.cursor_warp(int(self.cached_mouse_position[0]), int(self.cached_mouse_position[1]))
                self.rotate = False

    # Bevel
    def modifier_bevel(self, context, event):
        if event.type == 'B':
            if event.value == 'PRESS':
                self.use_bevel = True
                self.cached_mouse_position = (self.mouse_path[1][0], self.mouse_path[1][1])
                context.window.cursor_set("NONE")
                self.bevel = True
            elif event.value == 'RELEASE':
                context.window.cursor_set("MUTE")
                context.window.cursor_warp(int(self.cached_mouse_position[0]), int(self.cached_mouse_position[1]))
                self.bevel = False

        if self.bevel:
            if event.type == 'WHEELUPMOUSE':
                self.bevel_segments += 1
            elif event.type == 'WHEELDOWNMOUSE':
                self.bevel_segments -= 1

    # Array
    def modifier_array(self, context, event):
        if event.type == 'LEFT_ARROW' and event.value == 'PRESS':
            self.rows -= 1
        if event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
            self.rows += 1
        if event.type == 'DOWN_ARROW' and event.value == 'PRESS':
            self.columns -= 1
        if event.type == 'UP_ARROW' and event.value == 'PRESS':
            self.columns += 1

        if (self.rows > 1 or self.columns > 1) and (event.type == 'A'):
            if event.value == 'PRESS':
                self.cached_mouse_position = (self.mouse_path[1][0], self.mouse_path[1][1])
                context.window.cursor_set("NONE")
                self.gap = True
            elif event.value == 'RELEASE':
                context.window.cursor_set("MUTE")
                context.window.cursor_warp(self.cached_mouse_position[0], self.cached_mouse_position[1])
                self.gap = False

    # Move
    def modifier_move(self, context, event):
        if event.type == 'SPACE':
            if event.value == 'PRESS':
                self.move = True
            elif event.value == 'RELEASE':
                self.move = False

        if self.move:
            # initial_position_variable_before_moving_the_brush
            if self.initial_position is False:
                self.position_x = 0
                self.position_y = 0
                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y
                self.initial_position = True
            self.move = True

        # update_the_coordinates
        if self.initial_position and self.move is False:
            for i in range(0, len(self.mouse_path)):
                l = list(self.mouse_path[i])
                l[0] += self.position_x
                l[1] += self.position_y
                self.mouse_path[i] = tuple(l)

            self.position_x = self.position_y = 0
            self.initial_position = False


class CarverBase():
    # OPERATOR-properties
    mode: bpy.props.EnumProperty(
        name = "Mode",
        items = (('DESTRUCTIVE', "Destructive", "Boolean cutters are immediatelly applied and removed after the cut", 'MESH_DATA', 0),
                 ('MODIFIER', "Modifier", "Cuts are stored as boolean modifiers and cutters placed inside the collection", 'MODIFIER_DATA', 1)),
        default = 'DESTRUCTIVE',
    )
    # orientation: bpy.props.EnumProperty(
    #     name = "Orientation",
    #     items = (('SURFACE', "Surface", "Surface normal of the mesh under the cursor"),
    #              ('VIEW', "View", "View-aligned orientation")),
    #     default = 'SURFACE',
    # )
    depth: bpy.props.EnumProperty(
        name = "Depth",
        items = (('VIEW', "View", "Depth is automatically calculated from view orientation", 'VIEW_CAMERA_UNSELECTED', 0),
                 ('CURSOR', "Cursor", "Depth is automatically set at 3D cursor location", 'PIVOT_CURSOR', 1)),
        default = 'VIEW',
    )

    # CUTTER-properties
    hide: bpy.props.BoolProperty(
        name = "Hide Cutter",
        description = ("Hide cutter objects in the viewport after they're created.\n"
                       "NOTE: They are hidden in render regardless of this property"),
        default = True,
    )
    parent: bpy.props.BoolProperty(
        name = "Parent to Canvas",
        description = ("Cutters will be parented to active object being cut, even if cutting multiple objects.\n"
                       "If there is no active object in selection cutters parent might be chosen seemingly randomly"),
        default = True,
    )
    auto_smooth: bpy.props.BoolProperty(
        name = "Shade Auto Smooth",
        description = ("Cutter object will be shaded smooth with sharp edges (above 30 degrees) marked as sharp\n"
                        "NOTE: This is one time operator. 'Smooth by Angle' modifier will not be added on object"),
        default = True,
    )
    sharp_angle: bpy.props.FloatProperty(
        name = "Angle",
        description = "Maximum face angle for sharp edges",
        subtype = "ANGLE",
        min = 0, max = math.pi,
        default = 0.523599,
    )

    # MODIFIER-properties
    solver: bpy.props.EnumProperty(
        name = "Solver",
        items = [('FAST', "Fast", ""),
                 ('EXACT', "Exact", "")],
        default = 'FAST',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifier",
        description = ("When enabled boolean modifier will be moved above every other modifier on the object (if there are any).\n"
                       "Order of modifiers can drastically affect the result (especially in destructive mode)"),
        default = True,
    )


    # ARRAY-properties
    rows: bpy.props.IntProperty(
        name = "Rows",
        description = "Number of times shape is duplicated on X axis",
        min = 1, soft_max = 16,
        default = 1,
    )
    rows_gap: bpy.props.FloatProperty(
        name = "Gap between Rows",
        min = 0, soft_max = 250,
        default = 50,
    )
    rows_direction: bpy.props.EnumProperty(
        name = "Direction of Rows",
        items = (('LEFT', "Left", ""),
                 ('RIGHT', "Right", "")),
        default = 'RIGHT',
    )

    columns: bpy.props.IntProperty(
        name = "Columns",
        description = "Number of times shape is duplicated on Y axis",
        min = 1, soft_max = 16,
        default = 1,
    )
    columns_direction: bpy.props.EnumProperty(
        name = "Direction of Rows",
        items = (('UP', "Up", ""),
                 ('DOWN', "Down", "")),
        default = 'DOWN',
    )
    columns_gap: bpy.props.FloatProperty(
        name = "Gap between Columns",
        min = 0, soft_max = 250,
        default = 50,
    )


    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Carver tool can only be called from 3D viewport")
            self.cancel(context)
            return {'CANCELLED'}

        self.selected_objects = context.selected_objects
        self.initial_selection = context.selected_objects
        self.mouse_path[0] = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_path[1] = (event.mouse_region_x, event.mouse_region_y)

        context.window.cursor_set("MUTE")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def redraw_region(self, context):
        """Redraw region to find the limits of the 3D viewport"""

        region_types = {'WINDOW', 'UI'}
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if not region_types or region.type in region_types:
                        region.tag_redraw()


    def selection_fallback(self, context, polyline=False):
        # filter_out_objects_not_inside_the_selection_bounding_box
        self.selected_objects = selection_fallback(self, context, self.selected_objects, polyline=polyline, include_cutters=True)

        # silently_fail_if_no_objects_inside_selection_bounding_box
        empty = False
        if len(self.selected_objects) == 0:
            self.cancel(context)
            empty = True

        return empty


    def confirm(self, context):
        create_cutter_shape(self, context)
        extrude(self, self.cutter.data)
        set_object_origin(self.cutter)
        if self.auto_smooth:
            shade_smooth_by_angle(self.cutter, angle=math.degrees(self.sharp_angle))

        self.Cut(context)
        self.cancel(context)


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.header_text_set(None)
        context.window.cursor_set('DEFAULT' if context.object.mode == 'OBJECT' else 'CROSSHAIR')


    def Cut(self, context):
        # ensure_active_object
        if not context.active_object:
            context.view_layer.objects.active = self.selected_objects[0]

        # Add Modifier
        for obj in self.selected_objects:
            if self.mode == 'DESTRUCTIVE':
                add_boolean_modifier(self, obj, self.cutter, "DIFFERENCE", self.solver, apply=True, pin=self.pin, redo=False)
            elif self.mode == 'MODIFIER':
                add_boolean_modifier(self, obj, self.cutter, "DIFFERENCE", self.solver, pin=self.pin, redo=False)
                obj.booleans.canvas = True

        if self.mode == 'DESTRUCTIVE':
            # Remove Cutter
            delete_cutter(self.cutter)

        elif self.mode == 'MODIFIER':
            # Set Cutter Properties
            canvas = None
            if context.active_object and context.active_object in self.selected_objects:
                canvas = context.active_object    
            else:
                canvas = self.selected_objects[0]

            set_cutter_properties(context, canvas, self.cutter, "Difference", parent=self.parent, hide=self.hide)



#### ------------------------------ PANELS ------------------------------ ####

def carver_ui_common(context, layout, props):
    """Tool properties common for all Carver operators"""

    layout.prop(props, "mode", text="")
    layout.prop(props, "depth", text="")
    row = layout.row()
    row.prop(props, "solver", expand=True)

    if context.object:
        layout.popover("TOPBAR_PT_carver_shape", text="Shape")
        layout.popover("TOPBAR_PT_carver_array", text="Array")
        layout.popover("TOPBAR_PT_carver_cutter", text="Cutter")


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
        mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
        tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)

        # Box Properties
        if tool.idname == "object.carve_box":
            props = tool.operator_properties("object.carve_box")

            if tool.idname == "object.carve_circle":
                layout.prop(props, "subdivision", text="Vertices")
            layout.prop(props, "rotation")
            layout.prop(props, "aspect", expand=True)
            layout.prop(props, "origin", expand=True)

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

        # Polyline Properties
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

        mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
        tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)
        if tool.idname == "object.carve_box":
            props = tool.operator_properties("object.carve_box")
        elif tool.idname == "object.carve_polyline":
            props = tool.operator_properties("object.carve_polyline")

        col = layout.column(align=True)
        col.prop(props, "rows")
        row = col.row(align=True)
        row.prop(props, "rows_direction", text="Direction", expand=True)
        col.prop(props, "rows_gap", text="Gap")

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

        mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
        tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)
        if tool.idname == "object.carve_box":
            props = tool.operator_properties("object.carve_box")
        elif tool.idname == "object.carve_polyline":
            props = tool.operator_properties("object.carve_polyline")

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
