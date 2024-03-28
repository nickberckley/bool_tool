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
from . import (
    bool_tool,
    utilities,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    bool_tool.register()
    utilities.register()

def unregister():
    bool_tool.unregister()
    utilities.unregister()