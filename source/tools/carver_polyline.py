import bpy
import math
import os
from mathutils import Vector
from bpy_extras import view3d_utils
from .. import __file__ as base_file

from .common.base import (
    CarverBase,
)
from .common.properties import (
    CarverPropsArray,
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


description = "Cut custom polygonal shapes into mesh objects"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_polyline(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_polyline"
    bl_label = "Polyline Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.dirname(base_file), "icons", "tool_icons", "ops.object.carver_polyline")
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

class OBJECT_OT_carve_polyline(CarverBase,
                               CarverPropsArray):
    bl_idname = "object.carve_polyline"
    bl_label = "Polyline Carve"
    bl_description = description
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}
    bl_cursor_pending = 'PICK_AREA'

    # SHAPE-properties
    shape = 'POLYLINE'
    origin = None
    aspect = None


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH') and context.area.type == 'VIEW_3D'


    def invoke(self, context, event):
        # Validate Selection
        self.objects = Selection(*self.validate_selection(context))

        if len(self.objects.selected) == 0:
            self.report({'WARNING'}, "Select mesh objects that should be carved")
            return {'CANCELLED'}

        # Initialize Core Components
        self.mouse = Mouse().from_event(event)
        self.workplane = Workplane(*self.calculate_workplane(context))
        self.cutter = Cutter(*self.create_cutter(context))
        self.effects = Effects().from_invoke(self, context)

         # cached_variables
        """Important for storing context as it was when operator was invoked (untouched by the modal)."""
        self.phase = "DRAW"
        self._distance_from_first = 0
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
        # Tool Settings Text
        snap_text = ", [MOUSEWHEEL]: Change Snapping Increment" if self.snap else ""
        shape_text = "[BACKSPACE]: Remove Last Point, [ENTER]: Confirm"
        array_text = ", [A]: Gap" if (self.rows > 1 or self.columns > 1) else ""
        context.workspace.status_text_set("[CTRL]: Snap Invert, [SPACEBAR]: Move, " + shape_text + array_text + snap_text)

        # find_the_limit_of_the_3d_viewport_region
        self.redraw_region(context)

        # Modifier Keys
        self.modifier_snap(context, event)
        self.modifier_array(context, event)
        self.modifier_move(context, event)

        if event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if self.phase != "BEVEL":
                return {'PASS_THROUGH'}


        # Mouse Move
        if event.type == 'MOUSEMOVE':
            self.mouse.current = Vector((event.mouse_region_x, event.mouse_region_y))

            # Draw
            if self.phase == "DRAW":
                # Calculate the distance from the initial mouse position.
                if self.mouse.current_3d:
                    first_vert_world = self.cutter.obj.matrix_world @ self.cutter.verts[0].co
                    first_vert_screen = view3d_utils.location_3d_to_region_2d(context.region,
                                                                              context.region_data,
                                                                              first_vert_world)
                    distance_screen = (Vector(self.mouse.current) - first_vert_screen).length
                    self._distance_from_first = max(100 - distance_screen, 0)

                # snap (find_the_closest_position_on_the_overlay_grid_and_snap_the_shape_to_it)
                if self.snap:
                    cursor_snap(self, context, event, self.mouse_path)

                self.update_cutter_shape(context)

            # Extrude
            elif self.phase == "EXTRUDE":
                self.set_extrusion_depth(context)


        # Add Points & Confirm
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self.phase == "DRAW":
                # Confirm Shape (if clicked on the first vert)
                if self._distance_from_first > 75:
                    verts = self.cutter.verts
                    if len(verts) > 3:
                        self._remove_polyline_point(context, jump_mouse=False)
                        self.extrude_cutter(context)
                        self.Cut(context)

                        # Not setting depth manually, performing a cut here.
                        if self.depth != 'MANUAL':
                            self.confirm(context)
                            return {'FINISHED'}
                        else:
                            return {'RUNNING_MODAL'}

                # Add Point
                else:
                    self._insert_polyline_point()

            # Confirm Depth
            if self.phase == "EXTRUDE":
                self.confirm(context)
                return {'FINISHED'}


        # Confirm
        elif event.type == 'RET':
            verts = self.cutter.verts
            if len(verts) > 2:
                # Confirm Shape
                if self.phase == "DRAW" and event.value == 'RELEASE':
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
            else:
                self.report({'WARNING'}, "At least three points are required to make a polygonal shape")


        # Remove Last Point
        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self._remove_polyline_point(context)


        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finalize(context, clean_up=True, abort=True)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


    # Polyline-specific features.
    def _insert_polyline_point(self):
        """Inserts a new vertex in the cutter geometry and connects it to the previous last one."""

        bm = self.cutter.bm
        verts = self.cutter.verts
        x, y = self.mouse.current_3d.x, self.mouse.current_3d.y

        # Lock the position of the last vert to cursor position at the moment of press.
        last_vert = verts[-1]
        last_vert.co = Vector((x, y, 0))

        # Find and remove edge between last vert and the first vert.
        if verts.index(last_vert) != 1:
            first_vert = verts[0]
            edge_to_remove = None
            for edge in last_vert.link_edges:
                if first_vert in edge.verts:
                    edge_to_remove = edge
                    break
            if edge_to_remove:
                self.cutter.bm.edges.remove(edge_to_remove)

        # Insert new point in bmesh and connect to last one.
        new_vert = bm.verts.new(Vector((x, y, 0)))
        bm.edges.new([last_vert, new_vert])
        verts.append(new_vert)

        # Create a new face.
        if len(verts) >= 3:
            face = self.cutter.bm.faces.new(verts)
            self.cutter.faces = [face]

        # Update bmesh.
        bm.to_mesh(self.cutter.mesh)


    def _remove_polyline_point(self, context, jump_mouse=True):
        """Removes the last vertex in cutter geometry and moves cursor to the one before that."""

        obj = self.cutter.obj
        bm = self.cutter.bm
        verts = self.cutter.verts
        faces = self.cutter.faces

        if len(verts) <= 2:
            return

        # Remove last vertex.
        last_vert = verts[-1]
        bm.verts.remove(last_vert)
        verts.pop()

        # Reconstruct the face.
        face = faces[0]
        if face is not None:
            if len(verts) >= 3:
                new_face = bm.faces.new(verts)
                faces[0] = new_face
            else:
                faces[0] = None

        # Create an edge between new last vertex and the first vertex.
        new_last = verts[-1]
        first_vert = verts[0]
        edge_exists = any(first_vert in edge.verts for edge in new_last.link_edges)
        if not edge_exists:
            bm.edges.new([new_last, first_vert])

        # Update bmesh.
        bm.to_mesh(self.cutter.mesh)

        # Jump mouse to the new last vert.
        if jump_mouse:
            vert_world = obj.matrix_world @ new_last.co
            screen_pos = view3d_utils.location_3d_to_region_2d(context.region,
                                                               context.region_data,
                                                               vert_world)
            if screen_pos:
                context.window.cursor_warp(int(screen_pos.x), int(screen_pos.y))



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
