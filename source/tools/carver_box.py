import bpy, mathutils, os
from .. import __file__ as base_file

from .common.base import (
    CarverModifierKeys,
    CarverBase,
)
from .common.properties import (
    CarverOperatorProperties,
    CarverModifierProperties,
    CarverCutterProperties,
    CarverArrayProperties,
    CarverBevelProperties,
)
from .common.ui import (
    carver_ui_common,
)

from ..functions.draw import (
    carver_shape_box,
)
from ..functions.select import (
    cursor_snap,
    selection_fallback,
)


description = "Cut primitive shapes into mesh objects by box drawing"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.dirname(base_file), "icons", "ops.object.carver_box")
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")
        carver_ui_common(context, layout, props)


class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_box(CarverBase, CarverModifierKeys, bpy.types.Operator,
                          CarverOperatorProperties, CarverModifierProperties, CarverCutterProperties,
                          CarverArrayProperties, CarverBevelProperties):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}
    bl_cursor_pending = 'PICK_AREA'

    shape: bpy.props.EnumProperty(
        name = "Shape",
        items = (('BOX', "Box", ""),
                 ('CIRCLE', "Circle", ""),
                 ('POLYLINE', "Polyline", "")),
        default = 'BOX',
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


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH') and context.area.type == 'VIEW_3D'


    def invoke(self, context, event):
        self.selected_objects = context.selected_objects
        self.mouse_path = [(event.mouse_region_x, event.mouse_region_y),
                           (event.mouse_region_x, event.mouse_region_y)]

        # initialize_empty_values
        self.verts = []
        self.duplicates = []
        self.cutter = None
        self.view_depth = mathutils.Vector()
        self.cached_mouse_position = () # needed_for_custom_modifier_keys

         # cached_variables
        """Important for storing context as it was when operator was invoked (untouched by the modal)"""
        self.initial_origin = self.origin
        self.initial_aspect = self.aspect

        # modifier_keys
        self.snap = False
        self.move = False
        self.rotate = False
        self.gap = False
        self.bevel = False

        # overlay_position (needed_for_moving_the_shape)
        self.position_offset_x = 0
        self.position_offset_y = 0
        self.initial_position = False

        # Add Draw Handler
        self._handle = bpy.types.SpaceView3D.draw_handler_add(carver_shape_box, (self, context, self.shape), 'WINDOW', 'POST_PIXEL')
        context.window.cursor_set("MUTE")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        # Status Bar Text
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        shape_text = "[SHIFT]: Aspect, [ALT]: Origin, [R]: Rotate, [ARROWS]: Array"
        array_text = ", [A]: Gap" if (self.rows > 1 or self.columns > 1) else ""
        bevel_text = ", [B]: Bevel" if self.shape == 'BOX' else ""
        context.workspace.status_text_set("[CTRL]: Snap Invert, [SPACEBAR]: Move, " + shape_text + bevel_text + array_text + snap_text)

        # find_the_limit_of_the_3d_viewport_region
        self.redraw_region(context)


        # Modifier Keys
        self.modifier_snap(context, event)
        self.modifier_aspect(context, event)
        self.modifier_origin(context, event)
        self.modifier_rotate(context, event)
        self.modifier_bevel(context, event)
        self.modifier_array(context, event)
        self.modifier_move(context, event)

        if event.type in {'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
                          'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9',
                          'MIDDLEMOUSE', 'N'}:
            return {'PASS_THROUGH'}

        if self.bevel == False and event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}


        # Mouse Move
        if event.type == 'MOUSEMOVE':
            # move
            if self.move:
                self.position_offset_x += (event.mouse_region_x - self.last_mouse_region_x)
                self.position_offset_y += (event.mouse_region_y - self.last_mouse_region_y)
                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y

            # rotate
            elif self.rotate:
                self.rotation = event.mouse_region_x * 0.01

            # array
            elif self.gap:
                self.rows_gap = event.mouse_region_x * 0.1
                self.columns_gap = event.mouse_region_y * 0.1

            # bevel
            elif self.bevel:
                self.bevel_radius = event.mouse_region_x * 0.002

            # Draw Shape
            else:
                if len(self.mouse_path) > 0:
                    # aspect
                    if self.aspect == 'FIXED':
                        side = max(abs(event.mouse_region_x - self.mouse_path[0][0]),
                                   abs(event.mouse_region_y - self.mouse_path[0][1]))
                        self.mouse_path[len(self.mouse_path) - 1] = \
                                        (self.mouse_path[0][0] + (side if event.mouse_region_x >= self.mouse_path[0][0] else -side),
                                         self.mouse_path[0][1] + (side if event.mouse_region_y >= self.mouse_path[0][1] else -side))

                    elif self.aspect == 'FREE':
                        self.mouse_path[len(self.mouse_path) - 1] = (event.mouse_region_x, event.mouse_region_y)

                    # snap (find_the_closest_position_on_the_overlay_grid_and_snap_the_shape_to_it)
                    if self.snap:
                        cursor_snap(self, context, event, self.mouse_path)


        # Confirm
        elif (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or (event.type == 'RET' and event.value == 'PRESS'):
            # selection_fallback
            if len(self.selected_objects) == 0:
                self.selected_objects = selection_fallback(self, context, context.view_layer.objects, shape='BOX')
                for obj in self.selected_objects:
                    obj.select_set(True)

                if len(self.selected_objects) == 0:
                    self.cancel(context)
                    return {'FINISHED'}
            else:
                selection = self.validate_selection(context, shape='BOX')
                if not selection:
                    self.cancel(context)
                    return {'FINISHED'}

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



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_carve_box,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
