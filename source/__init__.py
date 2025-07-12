if "bpy" in locals():
    import importlib
    for mod in [operators,
                tools,
                manual,
                preferences,
                properties,
                ui,
                versioning,
                ]:
        importlib.reload(mod)
    print("Add-on Reloaded: Bool Tool")
else:
    import bpy
    from . import (
        operators,
        tools,
        manual,
        preferences,
        properties,
        ui,
        versioning,
    )


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    operators,
    tools,
    manual,
    preferences,
    properties,
    ui,
    versioning,
]

def register():
    for module in modules:
        module.register()

    preferences.update_sidebar_category(bpy.context.preferences.addons[__package__].preferences, bpy.context)


def unregister():
    for module in reversed(modules):
        module.unregister()
