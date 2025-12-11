import bpy
import math


# Import Custom Icons
from ... import icons
svg_icons = icons.svg_icons["main"]
icon_measure = svg_icons["MEASURE"].icon_id
icon_cpu = svg_icons["CPU"].icon_id


#### ------------------------------ PROPERTIES ------------------------------ ####

class CarverPropsOperator():
    # OPERATOR-properties
    mode: bpy.props.EnumProperty(
        name = "Mode",
        items = (('DESTRUCTIVE', "Destructive",
                  "Boolean cutters are immediatelly applied and removed after the cut", 'MESH_DATA', 0),
                 ('MODIFIER', "Modifier",
                  "Cuts are stored as boolean modifiers and cutters are placed inside the collection", 'MODIFIER_DATA', 1)),
        default = 'MODIFIER',
    )
    alignment: bpy.props.EnumProperty(
        name = "Alignment",
        items = (('SURFACE', "Surface", "Align cutters to the surface normal of the mesh under the mouse", 'SNAP_NORMAL', 0),
                 ('VIEW', "View", "Align cutters to the current view", 'VIEW_CAMERA_UNSELECTED', 1),
                 ('CURSOR', "3D Cursor", "Align cutters to the 3D cursor orientation", 'ORIENTATION_CURSOR', 2),
                 ('GRID', "Grid", "Align cutters to the world grid", 'GRID', 3)),
        default = 'SURFACE',
    )
    depth: bpy.props.EnumProperty(
        name = "Depth",
        items = (('MANUAL', "Manual", "Depth can be manually set after creating a cutter shape", icon_measure, 0),
                 ('AUTO', "Auto", "Depth is set automatically to cover selected objects entirely", icon_cpu, 1),
                 ('CURSOR', "3D Cursor", "Depth is set to 3D cursors location", 'PIVOT_CURSOR', 2)),
        default = 'MANUAL',
    )

    # Grid
    use_grid: bpy.props.BoolProperty(
        name = "Snapping Grid",
        description = "Create point grid in 3D space, aligned to the workplane, that cutter vertices can snap to",
        default = False,
    )
    grid_subdivision_method: bpy.props.EnumProperty(
        name = "Subdivision Level",
        items = (('ZOOM', "Based on Zoom", "Subdivide snapping grid based on viewport zoom level when initializing"),
                 ('MANUAL', "Manual", "Subdivide snapping grid by specific increments to guarantee precise size")),
        default = 'ZOOM',
    )
    grid_increment: bpy.props.FloatProperty(
        name = "Snapping Grid Increment",
        description = "Size of the snapping grid increment in scene units (this will be rounded up or down)",
        subtype = 'DISTANCE',
        min = 0.01,
        default = 1.0,
    )


class CarverPropsShape():
    # SHAPE-properties
    orientation: bpy.props.EnumProperty(
        name = "Orientation",
        description = "Orientation method for the shape placement",
        items = (('FACE', "Face Normal", "Orient the shape along the normal of the face"),
                 ('CLOSEST_EDGE', "Closest Edge", "Orient the shape along the closest edge of the face"),
                 ('LONGEST_EDGE', "Longest Edge", "Orient the shape along the longest edge of the face")),
        default = 'CLOSEST_EDGE',
    )
    offset: bpy.props.FloatProperty(
        name = "Offset from Surface",
        description = ("Distance between the shape and the surface of the mesh.\n"
                       "Offset is important for avoiding Z-fighting issues and solver failures"),
        min = 0.0, soft_max = 0.1,
        default = 0.01,
    )
    align_to_all: bpy.props.BoolProperty(
        name = "Align to Anything",
        description = "Use all visible objects for surface alignment, not just selected objects",
        default = True,
    )
    alignment_axis: bpy.props.EnumProperty(
        name = "Alignment Axis",
        description = "Which axis of the world grid or 3D cursor should be used for workplane alignment",
        items = (('X', "X", ""),
                 ('Y', "Y", ""),
                 ('Z', "Z", "")),
        default = 'Z',
    )

    flip_direction: bpy.props.BoolProperty(
        name = "Flip Direction",
        description = "Change which way the geometry is extruded",
        options = {'SKIP_SAVE', 'HIDDEN', 'SKIP_PRESET', },
        default = False,
    )


class CarverPropsModifier():
    # MODIFIER-properties
    solver: bpy.props.EnumProperty(
        name = "Solver",
        items = [('FLOAT', "Float", ""),
                 ('EXACT', "Exact", ""),
                 ('MANIFOLD', "Manifold", "")],
        default = 'FLOAT',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifier",
        description = ("Boolean modifier will be placed first in modifier stack, above other modifier (if there are any).\n"
                       "NOTE: Order of modifiers can drastically affect the result (especially in destructive mode)"),
        default = True,
    )


class CarverPropsCutter():
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
    display: bpy.props.EnumProperty(
        name = "Cutter Display",
        items = (('WIRE', "Wire", "Display the cutter object as a wireframe"),
                 ('BOUNDS', "Bounds", "Display only the bounds of the cutter object")),
        default = 'BOUNDS'
    )
    cutter_origin: bpy.props.EnumProperty(
        name = "Cutter Origin Point",
        items = (('CENTER_OBJ', "Bounding Box", "Put the object origin at the center of the cutters bounding box"),
                 ('CENTER_MESH', "Geometry", "Put the object origin at the center of the cutters geometry (not including effects)"),
                 ('FACE_CENTER', "First Face", "Put the object origin at the center of cutters first face (i.e. shape)"),
                 ('MOUSE_INITIAL', "Mouse Click", "Put the object origin at the point where mouse was first clicked"),
                 ('CANVAS', "Same as Canvas", "Put the object origin of the cutter to the origin point of the cutter")),
        default = 'CENTER_MESH',
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


class CarverPropsArray():
    # ARRAY-properties
    rows: bpy.props.IntProperty(
        name = "Rows",
        description = "Number of times shape is duplicated horizontally",
        min = 1, soft_max = 16,
        default = 1,
    )
    columns: bpy.props.IntProperty(
        name = "Columns",
        description = "Number of times shape is duplicated vertically",
        min = 1, soft_max = 16,
        default = 1,
    )
    gap: bpy.props.FloatProperty(
        name = "Gap",
        description = "Spacing between duplicates, both in rows and columns (relative unit)",
        min = 1, soft_max = 10,
        default = 1.1,
    )


class CarverPropsBevel():
    # BEVEL-properties
    use_bevel: bpy.props.BoolProperty(
        name = "Bevel Cutter",
        description = "Bevel each side edge of the cutter",
        default = False,
    )
    bevel_segments: bpy.props.IntProperty(
        name = "Bevel Segments",
        description = "Segments for curved edge",
        min = 1, soft_max = 32,
        default = 8,
    )
    bevel_width: bpy.props.FloatProperty(
        name = "Bevel Width",
        min = 0, soft_max = 5,
        default = 0.1,
    )
    bevel_profile: bpy.props.FloatProperty(
        name = "Bevel Profile",
        description = "The bevel profile shape (0.5 = round)",
        min = 0, max = 1,
        default = 0.5,
    )
