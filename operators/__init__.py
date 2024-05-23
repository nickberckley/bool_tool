import bpy

from . import (
    boolean,
    canvas,
    cutter,
    select,
)



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    boolean.register()
    canvas.register()
    cutter.register()
    select.register()

def unregister():
    boolean.unregister()
    canvas.unregister()
    cutter.unregister()
    select.unregister()