import bpy, os

from ..functions.draw import(
    carver_brush,
)
from ..functions.select import(
    raycast_from_cursor,
)


from ..properties import ToolRuntimeData
tool_runtime_data = ToolRuntimeData()

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = ("Boolean cut primitive shapes into mesh objects with fixed-size brush")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons") , "ops.object.carver_circle")
    # bl_widget = 'VIEW3D_GGT_placement'
    # bl_keymap = (
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
    #     ("object.carve", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": [("shape", 'BOX')]}),
    # )
    bl_keymap = (
        ("wm.radial_control", {"type": 'F', "value": 'PRESS'}, {"properties": [("data_path_primary", 'tool_settings.unified_paint_settings.size')]}),
    )

    @staticmethod
    def draw_cursor(context, tool, xy):
        if context.active_object:
            obj = context.active_object
            brush = context.tool_settings.unified_paint_settings
            wm = context.window_manager.carver

            # Raycast
            region = context.region
            rv3d = context.region_data
            result, location, normal = raycast_from_cursor(region, rv3d, obj, xy)
            tool_runtime_data.update_raycast_status(result, obj.matrix_world, location, normal)

            if result:
                tool_runtime_data.update_brush_size(wm, brush, obj.matrix_world, location, region, rv3d)
                carver_brush('3D', context, obj_matrix=obj.matrix_world, location=location, normal=normal, radius=wm.unprojected_radius)
                return
            else:
                carver_brush('2D', context, radius=brush.size, xy=xy)
                return


class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
    bl_context_mode = 'EDIT_MESH'
