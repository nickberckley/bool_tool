import bpy


#### ------------------------------ PREFERENCES ------------------------------ ####

class BoolToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    BoolToolPreferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)