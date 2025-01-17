import bpy, mathutils, math, os

from .common import (
    CarverModifierKeys,
    CarverBase,
    carver_ui_common,
)
from ..functions.draw import (
    carver_overlay,
)
from ..functions.select import (
    cursor_snap,
    selection_fallback,
)


#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_polyline(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_polyline"
    bl_label = "Polyline Carve"
    bl_description = ("Boolean cut custom polygonal shapes into mesh objects")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons") , "ops.object.carver_polyline")
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve_polyline", {"type": 'LEFTMOUSE', "value": 'CLICK'}, None),
        ("object.carve_polyline", {"type": 'LEFTMOUSE', "value": 'CLICK', "ctrl": True}, None),
        # select
        ("view3d.select_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, None),
        ("view3d.select_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": [("mode", 'ADD')]}),
        ("view3d.select_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": [("mode", 'SUB')]}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_polyline")
        carver_ui_common(context, layout, props)


class MESH_WT_carve_polyline(OBJECT_WT_carve_polyline):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_polyline(CarverBase, CarverModifierKeys, bpy.types.Operator):
    bl_idname = "object.carve_polyline"
    bl_label = "Polyline Carve"
    bl_description = "Cut custom polygonal shapes into mesh objects"
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}
    bl_cursor_pending = 'PICK_AREA'

    # SHAPE-properties
    closed: bpy.props.BoolProperty(
        name = "Closed Polygon",
        description = "When enabled, mouse position at the moment of execution will be registered as last point of the polygon",
        default = True,
    )

    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH')


    def __init__(self):
        self.mouse_path = [(0, 0), (0, 0)]
        self.view_vector = mathutils.Vector()
        self.verts = []
        self.cutter = None
        self.duplicates = []

        args = (self, bpy.context, 'POLYLINE')
        self._handle = bpy.types.SpaceView3D.draw_handler_add(carver_overlay, args, 'WINDOW', 'POST_PIXEL')

        # Modifier Keys
        self.snap = False
        self.move = False
        self.gap = False

        # Cache
        self.cached_mouse_position = ()

        # overlay_position
        self.position_x = 0
        self.position_y = 0
        self.initial_position = False
        self.center_origin = []
        self.distance_from_first = 0


    def modal(self, context, event):
        # Tool Settings Text
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        shape_text = "[BACKSPACE]: Remove Last Point, [ENTER]: Confirm"
        array_text = ", [A]: Gap" if (self.rows > 1 or self.columns > 1) else ""
        context.area.header_text_set("[CTRL]: Snap Invert, [SPACEBAR]: Move, " + shape_text + array_text + snap_text)

        # find_the_limit_of_the_3d_viewport_region
        self.redraw_region(context)


        # Modifier Keys
        self.modifier_snap(context, event)
        self.modifier_array(context, event)
        self.modifier_move(context, event)

        if event.type in {'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
                          'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9',
                          'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE', 'N'}:
            return {'PASS_THROUGH'}
        

        # Mouse Move
        if event.type == 'MOUSEMOVE':
            # move
            if self.move:
                self.position_x += (event.mouse_region_x - self.last_mouse_region_x)
                self.position_y += (event.mouse_region_y - self.last_mouse_region_y)
                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y

            # array
            elif self.gap:
                self.rows_gap = event.mouse_region_x * 0.1
                self.columns_gap = event.mouse_region_y * 0.1

            # Draw Shape
            else:
                if len(self.mouse_path) > 0:
                    self.mouse_path[len(self.mouse_path) - 1] = (event.mouse_region_x, event.mouse_region_y)

                    # snap (find_the_closest_position_on_the_overlay_grid_and_snap_the_shape_to_it)
                    if self.snap:
                        cursor_snap(self, context, event, self.mouse_path)

                    # get_distance_from_first_point
                    distance = math.sqrt((self.mouse_path[-1][0] - self.mouse_path[0][0]) ** 2 +
                                         (self.mouse_path[-1][1] - self.mouse_path[0][1]) ** 2)
                    min_radius = 0
                    max_radius = 30
                    self.distance_from_first = max(max_radius - distance, min_radius)


        # Add Points & Confirm
        elif (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or (event.type == 'RET' and event.value == 'PRESS'):
            # selection_fallback (expand_selection_fallback_on_every_polyline_click)
            if len(self.initial_selection) == 0:
                self.selected_objects = selection_fallback(self, context, context.view_layer.objects, polyline=True)
                for obj in self.selected_objects:
                    obj.select_set(True)


            # add_new_points
            if not (event.type == 'RET' and event.value == 'PRESS') and (self.distance_from_first < 15):
                self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))
                if self.closed == False:
                    """NOTE: Additional vert is needed for open loop."""
                    self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

            # confirm_cut
            else:
                if self.closed == False:
                    self.verts.pop() # dont_add_current_mouse_position_as_vert

                if self.distance_from_first > 15:
                    self.verts[-1] = self.verts[0]

                if len(self.verts) / 2 <= 1:
                    self.report({'INFO'}, "At least two points are required to make polygonal shape")
                    self.cancel(context)
                    return {'FINISHED'}

                if self.closed and self.mouse_path[-1] == self.mouse_path[-2]:
                    context.window.cursor_warp(event.mouse_region_x - 1, event.mouse_region_y)

                """NOTE: Polyline needs separate selection fallback, because it needs to calculate selection bounding box..."""
                """NOTE: after all points are already drawn, i.e. before execution."""
                empty = self.selection_fallback(context, polyline=True)
                if empty:
                    return {'FINISHED'}

                self.confirm(context)
                return {'FINISHED'}


        # Remove Last Point
        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if len(self.mouse_path) > 2:
                context.window.cursor_warp(int(self.mouse_path[-2][0]), int(self.mouse_path[-2][1]))
                self.mouse_path = self.mouse_path[:-1]


        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_carve_polyline,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
