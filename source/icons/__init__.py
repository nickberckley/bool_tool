import bpy
import os


#### ------------------------------ REGISTRATION ------------------------------ ####

svg_icons = {}
icons = bpy.utils.previews.new()
dir = os.path.join(os.path.dirname(__file__))

icons.load("MEASURE", os.path.join(dir, "measure.svg"), 'IMAGE')
icons.load("CPU", os.path.join(dir, "cpu.svg"), 'IMAGE')
svg_icons["main"] = icons


def register():
    ...

def unregister():
    # ICONS
    for pcoll in svg_icons.values():
        bpy.utils.previews.remove(pcoll)
    svg_icons.clear()
