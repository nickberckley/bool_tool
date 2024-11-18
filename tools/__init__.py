import bpy
from . import (
    carver,
    circle,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    carver,
    # circle,
]

main_tools = [
    carver.OBJECT_WT_carve_box,
    carver.MESH_WT_carve_box,
]
secondary_tools = [
    circle.OBJECT_WT_carve_circle,
    circle.MESH_WT_carve_circle,
    carver.OBJECT_WT_carve_polyline,
    carver.MESH_WT_carve_polyline,
]


def register():
    for module in modules:
        module.register()

    for tool in main_tools:
        bpy.utils.register_tool(tool, separator=False, after="builtin.primitive_cube_add", group=True)
    for tool in secondary_tools:
        bpy.utils.register_tool(tool, separator=False, after="object.carve_box", group=False)

def unregister():
    for module in reversed(modules):
        module.unregister()

    for tool in main_tools:
        bpy.utils.unregister_tool(tool)
    for tool in secondary_tools:
        bpy.utils.unregister_tool(tool)
