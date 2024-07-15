# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
   "name": "Bool Tool (2.0)",
   "author": "Vitor Balbio, Mikhail Rachinskiy, TynkaTopi, Meta-Androcto, Simon Appelt, Nika Kutsnishvili (v2.0)",
   "version": (2, 0, 0),
   "blender": (4, 0, 0),
   "location": "3D Viewport > Object > Boolean",
   "description": "Set of boolean tools and operators",
   "category": "Object",
}

import bpy
from .operators import register as operators_register, unregister as operators_unregister
from . import (
    preferences,
    properties,
    ui,
    versioning,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    preferences,
    properties,
    ui,
    versioning,
]

def register():
    for module in modules:
        module.register()
    
    operators_register()

def unregister():
    for module in reversed(modules):
        module.unregister()

    operators_unregister()
