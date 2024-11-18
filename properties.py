import bpy, mathutils
from .functions.select import(
    calc_projected_radius,
    calc_unprojected_radius,
)


#### ------------------------------ PROPERTIES ------------------------------ ####

class ToolRuntimeData:
    """Runtime Data for Circle Carve Tool"""

    def __init__(self):
        self.raycast = False
        self.world_location = mathutils.Vector()
        self.world_normal = mathutils.Vector()

        self.rad_3d = 0.0
        self.brush_size = 0.0

        # self.pack_source_circle = False

    def update_raycast_status(self, raycast, obj_matrix, location, normal):
        self.raycast = raycast

        if raycast:
            self.world_location = obj_matrix @ location
            self.world_normal = obj_matrix.to_quaternion() @ normal
        else:
            self.world_location.zero()
            self.world_normal.zero()

    def update_brush_size(self, wm, brush, obj_matrix, location, region, rv3d):
        if not wm.scale_size or brush.size != self.brush_size:
            self.rad_3d, wm.unprojected_radius = calc_unprojected_radius(obj_matrix, location, region, rv3d, brush.size)
            if brush.size != self.brush_size:
                self.brush_size = brush.size
        else:
            brush.size = self.brush_size = calc_projected_radius(obj_matrix, self.loc_world, region, rv3d, wm.unprojected_radius)


class OBJECT_PG_booleans(bpy.types.PropertyGroup):
    # OBJECT-level Properties

    canvas: bpy.props.BoolProperty(
        name = "Boolean Canvas",
        default = False,
    )
    cutter: bpy.props.StringProperty(
        name = "Boolean Cutter",
    )
    slice: bpy.props.BoolProperty(
        name = "Boolean Slice",
        default = False,
    )

    slice_of: bpy.props.PointerProperty(
        name = "Slice of...",
        type = bpy.types.Object,
    )
    carver: bpy.props.BoolProperty(
        name = "Is Carver Cutter",
        default = False,
    )

    cutters_active_index: bpy.props.IntProperty(
        name = "Active Cutter Index",
        default = -1,
    )


class TOOL_PG_carver(bpy.types.PropertyGroup):
    # TOOL-level Properties

    scale_size: bpy.props.BoolProperty(
        name = "Brush Scale",
        description = "Toggle between 2D space and 3D space where the brush is in when zooming",
        default = False,
    )
    unprojected_radius: bpy.props.FloatProperty(
        name = "Unprojected Radius",
        subtype = 'DISTANCE',
        min = 0.001, soft_max = 1, step = 1, precision = -1,
    )



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_PG_booleans,
    TOOL_PG_carver,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Object.booleans = bpy.props.PointerProperty(type=OBJECT_PG_booleans, name="Booleans")
    bpy.types.WindowManager.carver = bpy.props.PointerProperty(type=TOOL_PG_carver, name="Carver")



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Object.booleans
    del bpy.types.WindowManager.carver
