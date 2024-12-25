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

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = ("Boolean cut primitive shapes into mesh objects by drawing rectangles with cursor")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons") , "ops.object.carver_box")
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, None),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, None),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")
        carver_ui_common(context, layout, props)


class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'


# class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool, CarverUserInterface):
#     bl_idname = "object.carve_circle"
#     bl_label = "Circle Carve"
#     bl_description = ("Boolean cut circlular shapes into mesh objects")

#     bl_space_type = 'VIEW_3D'
#     bl_context_mode = 'OBJECT'

#     bl_icon = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons") , "ops.object.carver_circle")
#     # bl_widget = 'VIEW3D_GGT_placement'
#     bl_keymap = (
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
#         ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
#     )

# class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
#     bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_box(CarverBase, CarverModifierKeys, bpy.types.Operator):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = "Boolean cut square shapes into mesh objects"
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

    # BEVEL-properties
    use_bevel: bpy.props.BoolProperty(
        name = "Bevel Cutter",
        description = "Bevel each side edge of the cutter",
        default = False,
    )
    bevel_profile: bpy.props.EnumProperty(
        name = "Bevel Profile",
        items = (('CONVEX', "Convex", "Outside bevel (rounded corners)"),
                 ('CONCAVE', "Concave", "Inside bevel")),
        default = 'CONVEX',
    )
    bevel_segments: bpy.props.IntProperty(
        name = "Bevel Segments",
        description = "Segments for curved edge",
        min = 2, soft_max = 32,
        default = 8,
    )
    bevel_radius: bpy.props.FloatProperty(
        name = "Bevel Radius",
        description = "Amout of the bevel (in screen-space units)",
        min = 0.01, soft_max = 5,
        default = 1,
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

        args = (self, bpy.context, 'BOX')
        self._handle = bpy.types.SpaceView3D.draw_handler_add(carver_overlay, args, 'WINDOW', 'POST_PIXEL')

        # Modifier Keys
        self.snap = False
        self.move = False
        self.rotate = False
        self.gap = False
        self.bevel = False

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


    def modal(self, context, event):
        # Tool Settings Text
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        shape_text = "[SHIFT]: Aspect, [ALT]: Origin, [R]: Rotate, [ARROWS]: Array"
        array_text = ", [A]: Gap" if (self.rows > 1 or self.columns > 1) else ""
        bevel_text = ", [B]: Bevel"
        context.area.header_text_set("[CTRL]: Snap Invert, [SPACEBAR]: Move, " + shape_text + bevel_text + array_text + snap_text)

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
            # rotate
            if self.rotate:
                self.rotation = event.mouse_region_x * 0.01

            # move
            elif self.move:
                self.position_x += (event.mouse_region_x - self.last_mouse_region_x)
                self.position_y += (event.mouse_region_y - self.last_mouse_region_y)
                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y

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
    for cls in classes:
        bpy.utils.unregister_class(cls)
