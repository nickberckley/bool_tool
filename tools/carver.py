import bpy, mathutils, math
from .. import __package__ as base_package

from ..functions.draw import (
    carver_overlay,
)
from ..functions.object import (
    add_boolean_modifier,
    set_cutter_properties,
    delete_cutter,
)
from ..functions.mesh import (
    create_cutter_shape,
    extrude,
)
from ..functions.select import (
    cursor_snap,
    selection_fallback,
)


#### ------------------------------ /toolshelf_draw/ ------------------------------ ####

class CarverToolshelf():
    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve")
        if context.object:
            mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
            active_tool = context.workspace.tools.from_space_view3d_mode(mode, create=False).idname

        layout.prop(props, "mode", text="")
        layout.prop(props, "depth", text="")
        layout.prop(props, "solver", expand=True)
        layout.prop(props, "pin")

        if context.object:
            if props.mode == 'MODIFIER':
                row = layout.row()
                row.prop(props, "hide")

            if active_tool != "object.carve_polyline":
                layout.popover("TOPBAR_PT_carver_shape", text="Shape")
                layout.popover("TOPBAR_PT_carver_array", text="Array")
            else:
                layout.prop(props, "closed")

class TOPBAR_PT_carver_shape(bpy.types.Panel):
    bl_label = "Carver Shape"
    bl_idname = "TOPBAR_PT_carver_shape"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
        tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)
        op = tool.operator_properties("object.carve")

        if tool.idname == "object.carve_circle":
            layout.prop(op, "subdivision", text="Vertices")
        layout.prop(op, "rotation")
        layout.prop(op, "aspect", expand=True)
        layout.prop(op, "origin", expand=True)

class TOPBAR_PT_carver_array(bpy.types.Panel):
    bl_label = "Carver Array"
    bl_idname = "TOPBAR_PT_carver_array"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        mode = "OBJECT" if context.object.mode == 'OBJECT' else "EDIT_MESH"
        tool = context.workspace.tools.from_space_view3d_mode(mode, create=False)
        op = tool.operator_properties("object.carve")

        layout.prop(op, "rows")
        layout.prop(op, "rows_direction", text="Direction", expand=True)
        layout.prop(op, "rows_gap", text="Gap")

        layout.separator()
        layout.prop(op, "columns")
        layout.prop(op, "columns_direction", text="Direction", expand=True)
        layout.prop(op, "columns_gap", text="Gap")



#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool, CarverToolshelf):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = ("Boolean cut rectangular shapes into mesh objects")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = "ops.sculpt.box_trim"
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("shape", 'BOX')]}),
    )

class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'


class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool, CarverToolshelf):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = ("Boolean cut circlular shapes into mesh objects")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = "ops.sculpt.lasso_trim"
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("shape", 'CIRCLE')]}),
    )

class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
    bl_context_mode = 'EDIT_MESH'


class OBJECT_WT_carve_polyline(bpy.types.WorkSpaceTool, CarverToolshelf):
    bl_idname = "object.carve_polyline"
    bl_label = "Polyline Carve"
    bl_description = ("Boolean cut custom polygonal shapes into mesh objects")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = "ops.sculpt.polyline_trim"
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK'}, {"properties": [("shape", 'POLYLINE')]}),
    )

class MESH_WT_carve_polyline(OBJECT_WT_carve_polyline):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve(bpy.types.Operator):
    bl_idname = "object.carve"
    bl_label = "Carve"
    bl_description = "Boolean cut square shapes into mesh objects"
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}

    # OPERATOR-properties
    shape: bpy.props.EnumProperty(
        name = "Shape",
        items = (('BOX', "Box", ""),
                 ('CIRCLE', "Circle", ""),
                 ('POLYLINE', "Polyline", "")),
        default = 'BOX',
    )
    mode: bpy.props.EnumProperty(
        name = "Mode",
        items = (('DESTRUCTIVE', "Destructive", "Boolean cutters are immediatelly applied and removed after the cut"),
                 ('MODIFIER', "Modifier", "Cuts are stored as boolean modifiers and cutters placed inside the collection")),
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
        items = (('VIEW', "View", "Depth is automatically calculated from view orientation"),
                 ('CURSOR', "Cursor", "Depth is automatically set at 3D cursor location")),
        default = 'VIEW',
    )

    # SHAPE-properties
    aspect: bpy.props.EnumProperty(
        name = "Aspect",
        items = (('FREE', "Free", "Use an unconstrained aspect"),
                ('FIXED', "Fixed", "Use a fixed 1:1 aspect")),
        default = 'FREE',
    )
    origin: bpy.props.EnumProperty(
        name = "Origin",
        description = "The initial position for placement",
        items = (('EDGE', "Edge", ""),
                ('CENTER', "Center", "")),
        default = 'EDGE',
    )
    rotation: bpy.props.FloatProperty(
        name = "Rotation",
        subtype = "ANGLE",
        soft_min = -360, soft_max = 360,
        default = 0,
    )
    subdivision: bpy.props.IntProperty(
        name = "Circle Subdivisions",
        description = "Number of vertices that will make up the circular shape that will be extruded into a cylinder",
        min = 3, soft_max = 128,
        default = 16,
    )
    closed: bpy.props.BoolProperty(
        name = "Closed Polygon",
        description = "When enabled, mouse position at the moment of execution will be registered as last point of the polygon",
        default = True,
    )

    # CUTTER-properties
    hide: bpy.props.BoolProperty(
        name = "Hide Cutter",
        description = ("Hide cutter objects in the viewport after they're created\n"
                       "NOTE: They are hidden in render regardless of this property"),
        default = True
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
        items = (('RIGHT', "Right", ""),
                 ('LEFT', "Left", "")),
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

    # ADVANCED-properties
    solver: bpy.props.EnumProperty(
        name = "Solver",
        items = [('FAST', "Fast", ""),
                 ('EXACT', "Exact", "")],
        default = 'FAST',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifier",
        description = ("When enabled boolean modifier will be moved above every other modifier on the object (if there are any)\n"
                       "Order of modifiers can drastically affect the result (especially in destructive mode)"),
        default = True,
    )


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH')


    def __init__(self):
        context = bpy.context

        self.mouse_path = [(0, 0), (0, 0)]
        self.view_vector = mathutils.Vector()
        self.verts = []
        self.cutter = None
        self.duplicates = []

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(carver_overlay, args, 'WINDOW', 'POST_PIXEL')

        # Modifier Keys
        self.snap = False
        self.move = False
        self.rotate = False
        self.gap = False

        # Cache
        self.initial_origin = self.origin
        self.initial_aspect = self.aspect
        self.cached_mouse_position = ()

        # overlay_position
        self.position_x = 0
        self.position_y = 0
        self.initial_position = False
        self.center_origin = []
        self.distance_from_first = 0


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


    def modal(self, context, event):
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        if self.shape == 'POLYLINE':
            shape_text = "[BACKSPACE]: Remove Last Point, [ENTER]: Confirm"
        else:
            shape_text = "[SHIFT]: Aspect, [ALT]: Origin, [R]: Rotate, [ARROWS]: Array"
        array_text = ", [A]: Gap" if (self.rows > 1 or self.columns > 1) else ""
        context.area.header_text_set("[CTRL]: Snap Invert, [SPACEBAR]: Move, " + shape_text + array_text + snap_text)

        # find_the_limit_of_the_3d_viewport_region
        region_types = {'WINDOW', 'UI'}
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if not region_types or region.type in region_types:
                        region.tag_redraw()


        # SNAP
        # change_the_snap_increment_value_using_the_wheel_mouse
        if (self.move is False) and (self.rotate is False):
            for i, a in enumerate(context.screen.areas):
                if a.type == 'VIEW_3D':
                    space = context.screen.areas[i].spaces.active

            if event.type == 'WHEELUPMOUSE':
                 space.overlay.grid_subdivisions -= 1
            elif event.type == 'WHEELDOWNMOUSE':
                 space.overlay.grid_subdivisions += 1

        self.snap = context.scene.tool_settings.use_snap
        if event.ctrl and (self.move is False) and (self.rotate is False):
            self.snap = not self.snap


        # ASPECT
        if event.shift and (self.shape != 'POLYLINE'):
            if self.initial_aspect == 'FREE':
                self.aspect = 'FIXED'
            elif self.initial_aspect == 'FIXED':
                self.aspect = 'FREE'
        else:
            self.aspect = self.initial_aspect


        # ORIGIN
        if event.alt and (self.shape != 'POLYLINE'):
            if self.initial_origin == 'EDGE':
                self.origin = 'CENTER'
            elif self.initial_origin == 'CENTER':
                self.origin = 'EDGE'
        else:
            self.origin = self.initial_origin


        # ROTATE
        if event.type == 'R' and (self.shape != 'POLYLINE'):
            if event.value == 'PRESS':
                self.cached_mouse_position = (self.mouse_path[1][0], self.mouse_path[1][1])
                context.window.cursor_set("NONE")
                self.rotate = True
            elif event.value == 'RELEASE':
                context.window.cursor_set("MUTE")
                context.window.cursor_warp(self.cached_mouse_position[0], self.cached_mouse_position[1])
                self.rotate = False


        # ARRAY
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


        # MOVE
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


        # Remove Point (Polyline)
        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if len(self.mouse_path) > 2:
                context.window.cursor_warp(self.mouse_path[-2][0], self.mouse_path[-2][1])
                self.mouse_path = self.mouse_path[:-2]


        if event.type in {
                'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9'}:
            return {'PASS_THROUGH'}


        # mouse_move
        if event.type == 'MOUSEMOVE':
            if self.rotate:
                self.rotation = event.mouse_region_x * 0.01

            elif self.move:
                # MOVE
                self.position_x += (event.mouse_region_x - self.last_mouse_region_x)
                self.position_y += (event.mouse_region_y - self.last_mouse_region_y)

                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y

            elif self.gap:
                self.rows_gap = event.mouse_region_x * 0.1
                self.columns_gap = event.mouse_region_y * 0.1

            else:
                if len(self.mouse_path) > 0:
                    # ASPECT
                    if self.aspect == 'FIXED':
                        side = max(abs(event.mouse_region_x - self.mouse_path[0][0]),
                                    abs(event.mouse_region_y - self.mouse_path[0][1]))
                        self.mouse_path[len(self.mouse_path) - 1] = \
                                        (self.mouse_path[0][0] + (side if event.mouse_region_x >= self.mouse_path[0][0] else -side),
                                            self.mouse_path[0][1] + (side if event.mouse_region_y >= self.mouse_path[0][1] else -side))

                    elif self.aspect == 'FREE':
                        self.mouse_path[len(self.mouse_path) - 1] = (event.mouse_region_x, event.mouse_region_y)

                    # SNAP (find_the_closest_position_on_the_overlay_grid_and_snap_the_shape_to_it)
                    if self.snap:
                        cursor_snap(self, context, event, self.mouse_path)

                    if self.shape == 'POLYLINE':
                        # get_distance_from_first_point
                        distance = math.sqrt((self.mouse_path[-1][0] - self.mouse_path[0][0]) ** 2 + 
                                                (self.mouse_path[-1][1] - self.mouse_path[0][1]) ** 2)
                        min_radius = 0
                        max_radius = 30
                        self.distance_from_first = max(max_radius - distance, min_radius)


        # Confirm
        elif (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or (event.type == 'RET' and event.value == 'PRESS'):
            # selection_fallback
            if self.shape != 'POLYLINE':
                if len(self.selected_objects) == 0:
                    self.selected_objects = selection_fallback(self, context, context.view_layer.objects)
                    for obj in self.selected_objects:
                        obj.select_set(True)

                    if len(self.selected_objects) == 0:
                        self.report({'INFO'}, "Only selected objects can be carved")
                        self.cancel(context)
                        return {'FINISHED'}
                else:
                    empty = self.selection_fallback(context)
                    if empty:
                        return {'FINISHED'}
            else:
                if len(self.initial_selection) == 0:
                    # expand_selection_fallback_on_every_polyline_click
                    self.selected_objects = selection_fallback(self, context, context.view_layer.objects)
                    for obj in self.selected_objects:
                        obj.select_set(True)

            # Polyline
            if self.shape == 'POLYLINE':
                if not (event.type == 'RET' and event.value == 'PRESS') and (self.distance_from_first < 15):
                    self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))
                else:
                    # Confirm Cut (Polyline)
                    if self.closed == False:
                        self.mouse_path.pop() # dont_add_current_mouse_position_as_vert

                    if (len(self.mouse_path) / 2) < 2 or (len(self.mouse_path) / 2) == 2 and self.mouse_path[-1] == self.mouse_path[-2]:
                        self.report({'INFO'}, "At least two points are required to make polygonal shape")
                        self.cancel(context)
                        return {'FINISHED'}

                    if self.closed and self.mouse_path[-1] == self.mouse_path[-2]:
                        context.window.cursor_warp(event.mouse_region_x - 1, event.mouse_region_y)

                    # NOTE: Polyline needs separate selection fallback, because it needs to calculate selection bounding box...
                    # NOTE: after all points are already drawn, i.e. before execution.
                    empty = self.selection_fallback(context)
                    if empty:
                        return {'FINISHED'}

                    self.confirm(context)
                    return {'FINISHED'}

            # Confirm Cut (Box, Circle)
            else:
                # protection_against_returning_no_rectangle_by_clicking
                delta_x = abs(event.mouse_region_x - self.mouse_path[0][0])
                delta_y = abs(event.mouse_region_y - self.mouse_path[0][1])
                min_distance = 5

                if delta_x > min_distance or delta_y > min_distance:
                    self.confirm(context)
                    return {'FINISHED'}


        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


    def confirm(self, context):
        create_cutter_shape(self, context)
        extrude(self, self.cutter.data)
        self.Cut(context)
        self.cancel(context)


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")


    def selection_fallback(self, context):
        # filter_out_objects_not_inside_the_selection_bounding_box
        self.selected_objects = selection_fallback(self, context, self.selected_objects, include_cutters=True)

        # silently_fail_if_no_objects_inside_selection_bounding_box
        empty = False
        if len(self.selected_objects) == 0:
            self.cancel(context)
            empty = True

        return empty


    def Cut(self, context):
        # ensure_active_object
        if not context.active_object:
            context.view_layer.objects.active = self.selected_objects[0]

        # Add Modifier
        for obj in self.selected_objects:
            if self.mode == 'DESTRUCTIVE':
                add_boolean_modifier(self, obj, self.cutter, "DIFFERENCE", self.solver, apply=True, pin=self.pin)
            elif self.mode == 'MODIFIER':
                add_boolean_modifier(self, obj, self.cutter, "DIFFERENCE", self.solver, pin=self.pin)
                obj.booleans.canvas = True

        if self.mode == 'DESTRUCTIVE':
            # Remove Cutter
            delete_cutter(self.cutter)

        elif self.mode == 'MODIFIER':
            # Set Cutter Properties
            parent = None
            if context.active_object and context.active_object in self.selected_objects:
                parent = context.active_object    
            else:
                parent = self.selected_objects[0]

            set_cutter_properties(context, parent, self.cutter, "Difference", hide=self.hide)



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_carve,
    TOPBAR_PT_carver_shape,
    TOPBAR_PT_carver_array,
]

main_tools = [
    OBJECT_WT_carve_box,
    MESH_WT_carve_box,
]
secondary_tools = [
    OBJECT_WT_carve_circle,
    OBJECT_WT_carve_polyline,
    MESH_WT_carve_circle,
    MESH_WT_carve_polyline,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for tool in main_tools:
        bpy.utils.register_tool(tool, separator=False, after="builtin.primitive_cube_add", group=True)
    for tool in secondary_tools:
        bpy.utils.register_tool(tool, separator=False, after="object.carve_box", group=False)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for tool in main_tools:
        bpy.utils.unregister_tool(tool)
    for tool in secondary_tools:
        bpy.utils.unregister_tool(tool)
