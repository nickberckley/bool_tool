import bpy, mathutils
from .. import __package__ as base_package

from ..functions.draw import (
    carver_overlay_rectangle,
)
from ..functions.object import (
    add_boolean_modifier,
    set_cutter_properties,
    delete_cutter,
)
from ..functions.mesh import (
    create_cut_rectangle,
    extrude,
)
from ..functions.select import (
    cursor_snap,
    selection_fallback,
)


#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = ("Boolean cut square shapes into mesh objects")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = "ops.sculpt.box_trim"
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")

        layout.prop(props, "mode")
        layout.prop(props, "depth")
        layout.prop(props, "pin")

        if props.mode == 'MODIFIER':
            row = layout.row()
            row.prop(props, "hide")


class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_box(bpy.types.Operator):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = "Boolean cut square shapes into mesh objects"
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}

    # OPERATOR-properties
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

    # CUTTER-properties
    hide: bpy.props.BoolProperty(
        name = "Hide Cutter",
        description = ("Hide cutter objects in the viewport after they're created\n"
                       "NOTE: They are hidden in render regardless of this property"),
        default = True
    )

    # ADVANCED-properties
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
        self.rectangle_coords = []
        self.cutter = None

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(carver_overlay_rectangle, args, 'WINDOW', 'POST_PIXEL')

        # Modifier Keys
        self.snap = False
        self.move = False
        self.fix = False

        # overlay_position
        self.position_x = 0
        self.position_y = 0
        self.initial_position = False


    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Carver tool can only be called from 3D viewport")
            self.cancel(context)
            return {'CANCELLED'}

        self.selected_objects = context.selected_objects.copy()
        self.mouse_path[0] = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_path[1] = (event.mouse_region_x, event.mouse_region_y)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        context.area.header_text_set("CTRL: Snap Invert, SPACEBAR: Move, SHIFT: Fixed Aspect")

        # find_the_limit_of_the_3d_viewport_region
        region_types = {'WINDOW', 'UI'}
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if not region_types or region.type in region_types:
                        region.tag_redraw()


        # SNAP
        # change_the_snap_increment_value_using_the_wheel_mouse
        if (self.move is False) and (self.fix is False):
            for i, a in enumerate(context.screen.areas):
                if a.type == 'VIEW_3D':
                    space = context.screen.areas[i].spaces.active

            if event.type == 'WHEELUPMOUSE':
                 space.overlay.grid_subdivisions += 1
            elif event.type == 'WHEELDOWNMOUSE':
                 space.overlay.grid_subdivisions -= 1

        self.snap = context.scene.tool_settings.use_snap
        if event.ctrl:
            self.snap = not self.snap


        # MOVE
        # make_spacebar_modifier_key
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


        if event.type in {
                'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9'}:
            return {'PASS_THROUGH'}


        # mouse_move
        if event.type == 'MOUSEMOVE':
            if self.move is False:
                if self.snap:
                    # find_the_closest_position_on_the_overlay_grid_and_snap_the_mouse_on_it
                    mouse_position = [[event.mouse_region_x, event.mouse_region_y]]
                    cursor_snap(self, context, event, mouse_position)
                else:
                    if len(self.mouse_path) > 0:
                        # Fixed Size
                        self.fix = event.shift
                        if self.fix:
                            side = max(abs(event.mouse_region_x - self.mouse_path[0][0]), abs(event.mouse_region_y - self.mouse_path[0][1]))
                            self.mouse_path[len(self.mouse_path) - 1] = \
                                            (self.mouse_path[0][0] + (side if event.mouse_region_x >= self.mouse_path[0][0] else -side),
                                             self.mouse_path[0][1] + (side if event.mouse_region_y >= self.mouse_path[0][1] else -side))
                        else:
                            self.mouse_path[len(self.mouse_path) - 1] = (event.mouse_region_x, event.mouse_region_y)
            else:
                self.position_x += (event.mouse_region_x - self.last_mouse_region_x)
                self.position_y += (event.mouse_region_y - self.last_mouse_region_y)

                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y


        # Confirm
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            # selection_fallback
            if len(self.selected_objects) == 0:
                self.selected_objects = selection_fallback(self, context, context.view_layer.objects)
                for obj in self.selected_objects:
                    obj.select_set(True)

                if len(self.selected_objects) == 0:
                    self.report({'INFO'}, "Only selected objects can be carved")
                    self.cancel(context)
                    return {'FINISHED'}
            else:
                # filter_out_objects_not_inside_the_mouse_path
                self.selected_objects = selection_fallback(self, context, self.selected_objects, include_cutters=True)

                # silently_fail_if_no_objects_inside_mouse_path
                if len(self.selected_objects) == 0:
                    self.cancel(context)
                    return {'FINISHED'}

            # protection_against_returning_no_rectangle_by_clicking
            delta_x = abs(event.mouse_region_x - self.mouse_path[0][0])
            delta_y = abs(event.mouse_region_y - self.mouse_path[0][1])
            min_distance = 5

            if delta_x > min_distance or delta_y > min_distance:
                create_cut_rectangle(self, context)
                extrude(self, self.cutter.data)
                self.Cut(context)

                self.cancel(context)
                return {'FINISHED'}


        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.header_text_set(None)


    def Cut(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences

        # Add Modifier
        for obj in self.selected_objects:
            if self.mode == 'DESTRUCTIVE':
                add_boolean_modifier(obj, self.cutter, "DIFFERENCE", prefs.solver, apply=True, pin=self.pin)
            elif self.mode == 'MODIFIER':
                add_boolean_modifier(obj, self.cutter, "DIFFERENCE", prefs.solver, pin=self.pin)
                obj.booleans.canvas = True

        if self.mode == 'DESTRUCTIVE':
            # Remove Cutter
            delete_cutter(context, self.cutter)

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
    OBJECT_OT_carve_box,
]

tools = [
    OBJECT_WT_carve_box,
    MESH_WT_carve_box,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for tool in tools:
        bpy.utils.register_tool(tool, separator=False, after="builtin.primitive_cube_add", group=True)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for tool in tools:
        bpy.utils.unregister_tool(tool)
