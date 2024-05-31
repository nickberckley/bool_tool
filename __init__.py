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
    experimental,
    preferences,
    properties,
    ui,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    preferences.register()
    properties.register()
    ui.register()
    experimental.register()

    operators_register()

def unregister():
    preferences.unregister()
    properties.unregister()
    ui.unregister()
    experimental.unregister()

    operators_unregister()
