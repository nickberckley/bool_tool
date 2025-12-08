import bpy
import os
from mathutils import Vector
from .. import __file__ as base_file

from .common.base import (
    CarverBase,
)
from .common.properties import (
    CarverPropsArray,
    CarverPropsBevel,
)
from .common.types import (
    Selection,
    Mouse,
    Workplane,
    Cutter,
    Effects,
)
from .common.ui import (
    carver_ui_common,
)

from ..functions.select import (
    cursor_snap,
)


description = "Cut primitive shapes into mesh objects by box drawing"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.dirname(base_file), "icons", "tool_icons", "ops.object.carver_box")
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": None}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")
        carver_ui_common(context, layout, props)


class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_box(CarverBase,
                          CarverPropsArray,
                          CarverPropsBevel):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}
    bl_cursor_pending = 'PICK_AREA'

    # SHAPE-properties
    shape = 'BOX'

    aspect: bpy.props.EnumProperty(
        name = "Aspect",
        description = "The initial aspect",
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


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH') and context.area.type == 'VIEW_3D'


    def invoke(self, context, event):
        # Validate Selection
        self.objects = Selection(*self.validate_selection(context))

        if len(self.objects.selected) == 0:
            self.report({'WARNING'}, "Select mesh objects that should be carved")
            bpy.ops.view3d.select_box('INVOKE_DEFAULT')
            return {'CANCELLED'}

        # Initialize Core Components
        self.mouse = Mouse().from_event(event)
        self.workplane = Workplane(*self.calculate_workplane(context))
        self.cutter = Cutter(*self.create_cutter(context))
        self.effects = Effects().from_invoke(self, context)

         # cached_variables
        """Important for storing context as it was when operator was invoked (untouched by the modal)."""
        self.phase = "DRAW"
        self.initial_origin = self.origin  # Initial shape origin.
        self.initial_aspect = self.aspect  # Initial shape aspect.
        self._stored_phase = "DRAW"

        # modifier_keys
        self.snap = False

        # Add Draw Handler
        self._handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_shaders,
                                                               (context,),
                                                               'WINDOW', 'POST_VIEW')
        context.window.cursor_set("MUTE")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        # Status Bar Text
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        shape_text = "[SHIFT]: Aspect, [ALT]: Origin, [R]: Rotate, [ARROWS]: Array, [F]: Flip"
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
        self.modifier_flip(context, event)
        self.modifier_move(context, event)

        if event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if self.phase != "BEVEL":
                return {'PASS_THROUGH'}


        # Mouse Move
        if event.type == 'MOUSEMOVE':
            self.mouse.current = Vector((event.mouse_region_x, event.mouse_region_y))

            # Array
            if self.phase == "ARRAY":
                self.rows_gap = event.mouse_region_x * 0.002
                self.columns_gap = event.mouse_region_y * 0.002

            # Draw
            elif self.phase == "DRAW":
                # snap (find_the_closest_position_on_the_overlay_grid_and_snap_the_shape_to_it)
                if self.snap:
                    cursor_snap(self, context, event, self.mouse)

                self.update_cutter_shape(context)

            # Extrude
            elif self.phase == "EXTRUDE":
                self.set_extrusion_depth(context)


        # Confirm
        elif event.type == 'LEFTMOUSE':
            # Confirm Shape
            if self.phase == "DRAW" and event.value == 'RELEASE':
                """
                Protection against creating a very small rectangle (or even with 0 dimensions)
                by clicking and releasing very quickly, in a very small distance.
                """
                delta_x = abs(event.mouse_region_x - self.mouse.initial[0])
                delta_y = abs(event.mouse_region_y - self.mouse.initial[1])
                min_distance = 5

                if delta_x < min_distance or delta_y < min_distance:
                    self.finalize(context, clean_up=True, abort=True)
                    return {'FINISHED'}

                self.extrude_cutter(context)
                self.Cut(context)

                # Not setting depth manually, performing a cut here.
                if self.depth != 'MANUAL':
                    self.confirm(context)
                    return {'FINISHED'}
                else:
                    return {'RUNNING_MODAL'}

            # Confirm Depth
            if self.phase == "EXTRUDE" and event.value == 'PRESS':
                self.confirm(context)
                return {'FINISHED'}


        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finalize(context, clean_up=True, abort=True)
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
