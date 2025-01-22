import bpy
from . import (
    carver_box,
    carver_circle,
    carver_polyline,
)
from .common import (
    ui,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    carver_box,
    # carver_circle,
    carver_polyline,
    ui,
]

main_tools = [
    carver_box.OBJECT_WT_carve_box,
    carver_box.MESH_WT_carve_box,
]
secondary_tools = [
    carver_circle.OBJECT_WT_carve_circle,
    carver_circle.MESH_WT_carve_circle,
    carver_polyline.OBJECT_WT_carve_polyline,
    carver_polyline.MESH_WT_carve_polyline,
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
