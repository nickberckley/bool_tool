import bpy, os
from .. import __file__ as base_file

from .common.ui import (
    carver_ui_common,
)


description = "Cut primitive shapes into mesh objects with brush"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.dirname(base_file), "icons", "ops.object.carver_circle")
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": [("shape", 'CIRCLE')]}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")
        carver_ui_common(context, layout, props)

class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
    bl_context_mode = 'EDIT_MESH'
