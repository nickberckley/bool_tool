import bpy, math


#### ------------------------------ PROPERTIES ------------------------------ ####

class CarverOperatorProperties():
    # OPERATOR-properties
    mode: bpy.props.EnumProperty(
        name = "Mode",
        items = (('DESTRUCTIVE', "Destructive", "Boolean cutters are immediatelly applied and removed after the cut", 'MESH_DATA', 0),
                 ('MODIFIER', "Modifier", "Cuts are stored as boolean modifiers and cutters are placed inside the collection", 'MODIFIER_DATA', 1)),
        default = 'DESTRUCTIVE',
    )
    depth: bpy.props.EnumProperty(
        name = "Depth",
        items = (('VIEW', "View", "Depth is automatically calculated from view orientation", 'VIEW_CAMERA_UNSELECTED', 0),
                 ('CURSOR', "Cursor", "Depth is derived from 3D cursors location", 'PIVOT_CURSOR', 1)),
        default = 'VIEW',
    )


class CarverModifierProperties():
    # MODIFIER-properties
    solver: bpy.props.EnumProperty(
        name = "Solver",
        items = [('FAST', "Fast", ""),
                 ('EXACT', "Exact", ""),
                 ('MANIFOLD', "Manifold", "")],
        default = 'FAST',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifier",
        description = ("Boolean modifier will be placed first in modifier stack, above other modifier (if there are any).\n"
                       "NOTE: Order of modifiers can drastically affect the result (especially in destructive mode)"),
        default = True,
    )


class CarverCutterProperties():
    # CUTTER-properties
    hide: bpy.props.BoolProperty(
        name = "Hide Cutter",
        description = ("Hide cutter objects in the viewport after they're created."),
        default = True,
    )
    parent: bpy.props.BoolProperty(
        name = "Parent to Canvas",
        description = ("Cutters will be parented to active object being cut, even if cutting multiple objects.\n"
                       "If there is no active object in selection cutters parent might be chosen seemingly randomly"),
        default = True,
    )

    auto_smooth: bpy.props.BoolProperty(
        name = "Shade Auto Smooth",
        description = ("Cutter object will be shaded smooth with sharp edges (above specified degrees) marked as sharp\n"
                        "NOTE: This is a one time operator. 'Smooth by Angle' modifier will not be added on cutter"),
        default = True,
    )
    sharp_angle: bpy.props.FloatProperty(
        name = "Angle",
        description = "Maximum face angle for sharp edges",
        subtype = "ANGLE",
        min = 0, max = math.pi,
        default = 0.523599,
    )


class CarverArrayProperties():
    # ARRAY-properties
    rows: bpy.props.IntProperty(
        name = "Rows",
        description = "Number of times shape is duplicated horizontally",
        min = 1, soft_max = 16,
        default = 1,
    )
    rows_gap: bpy.props.FloatProperty(
        name = "Gap between rows (relative unit)",
        min = 0, soft_max = 250,
        default = 50,
    )
    rows_direction: bpy.props.EnumProperty(
        name = "Direction of Rows",
        items = (('LEFT', "Left", ""),
                 ('RIGHT', "Right", "")),
        default = 'RIGHT',
    )

    columns: bpy.props.IntProperty(
        name = "Columns",
        description = "Number of times shape is duplicated vertically",
        min = 1, soft_max = 16,
        default = 1,
    )
    columns_direction: bpy.props.EnumProperty(
        name = "Direction of Rows",
        items = (('UP', "Up", ""),
                 ('DOWN', "Down", "")),
        default = 'DOWN',
    )
    columns_gap: bpy.props.FloatProperty(
        name = "Gap between columns (relative unit)",
        min = 0, soft_max = 250,
        default = 50,
    )


class CarverBevelProperties():
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
