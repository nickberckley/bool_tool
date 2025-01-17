import bpy, mathutils, math, os

from .common import (
    CarverBase,
    carver_ui_common,
)
from ..functions.draw import(
    carver_brush,
)
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
from ..functions.select import(
    raycast_from_cursor,
)


from ..properties import CarverRuntimeData
tool_runtime_data = CarverRuntimeData()

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = ("Boolean cut primitive shapes into mesh objects with fixed-size brush")

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons") , "ops.object.carver_circle")
    # bl_widget = 'VIEW3D_GGT_placement'
    bl_keymap = (
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": None}),
        ("wm.radial_control", {"type": 'F', "value": 'PRESS'}, {"properties": [("data_path_primary", 'tool_settings.unified_paint_settings.size')]}),
    )

    @staticmethod
    def draw_cursor(context, tool, xy):
        if context.active_object:
            obj = context.active_object
            brush = context.tool_settings.unified_paint_settings
            wm = context.window_manager.carver
            global tool_runtime_data

            # Raycast
            region = context.region
            rv3d = context.region_data
            result, location, normal = raycast_from_cursor(region, rv3d, obj, xy)
            tool_runtime_data.update_raycast_status(result, obj.matrix_world, location, normal)

            if result:
                tool_runtime_data.update_brush_size(wm, brush, obj.matrix_world, location, region, rv3d)
                rectangle, indices = carver_brush('3D', context, obj_matrix=obj.matrix_world, location=location, normal=normal, radius=wm.unprojected_radius)
                tool_runtime_data.update_verts(wm, rectangle, indices)
            else:
                carver_brush('2D', context, xy=xy, radius=brush.size)


class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_circle(CarverBase, bpy.types.Operator):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = "Cut shapes into mesh objects with brush"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH')


    def __init__(self):
        self.mouse_path = [(0, 0), (0, 0)]
        self.view_vector = mathutils.Vector()
        self.verts = []
        self.cutter = None
        self.duplicates = []


    def invoke(self, context, event):
        global tool_runtime_data
        self.verts = tool_runtime_data.verts

        self.selected_objects = context.selected_objects

        return self.execute(context)


    def execute(self, context):
        if self.verts:
            print(str(self.verts))

            create_cutter_shape(self, context)
            # extrude(self, self.cutter.data)
            # set_object_origin(self.cutter)
            # if self.auto_smooth:
            #     shade_smooth_by_angle(self.cutter, angle=math.degrees(self.sharp_angle))

            # self.Cut(context)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_carve_circle,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
