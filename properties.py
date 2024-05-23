import bpy


#### ------------------------------ PROPERTIES ------------------------------ ####

class BooleanCutters(bpy.types.PropertyGroup):
    cutter: bpy.props.PointerProperty(
        type = bpy.types.Object,
    )


class OBJECT_PG_bool_tool(bpy.types.PropertyGroup):
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

    cutters: bpy.props.CollectionProperty(
        type = BooleanCutters,
    )



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    BooleanCutters,
    OBJECT_PG_bool_tool,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Object.bool_tool = bpy.props.PointerProperty(type = OBJECT_PG_bool_tool)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Object.bool_tool
