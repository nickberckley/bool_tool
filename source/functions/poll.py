import bpy
from .list import list_canvas_cutters


#### ------------------------------ FUNCTIONS ------------------------------ ####

def basic_poll(context, check_linked=False):
    if context.mode == 'OBJECT':
        if context.active_object is not None:
            if context.active_object.type == 'MESH':
                if check_linked and is_linked(context) == True:
                    return False

                return True


def is_linked(context, obj=None):
    if not obj:
        obj = context.active_object

    if obj not in context.editable_objects:
        if obj.library:
            return True
        else:
            return False
    else:
        if obj.override_library:
            return True
        else:
            return False


def is_canvas(obj):
    if obj.booleans.canvas == False:
        return False
    else:
        cutters, __ = list_canvas_cutters([obj])
        if len(cutters) != 0:
            return True
        else:
            return False


def is_instanced_data(obj):
    """Checks if obj.data has more than one users, i.e. is instanced"""
    """Function only considers object types as users, and excludes pointers"""

    data = bpy.data.meshes.get(obj.data.name)
    users = 0

    for key, values in bpy.data.user_map(subset=[data]).items():
        for value in values:
            if value.id_type == 'OBJECT':
                users += 1

    if users > 1:
        return True
    else:
        return False


def active_modifier_poll(context):
    """Checks whether the active modifier for active object is a boolean"""

    if context.object:
        if len(context.object.modifiers) == 0:
            return False

        modifier = context.object.modifiers.active
        if modifier and modifier.type == "BOOLEAN":
            if modifier.object == None:
                return False
            else:
                return True
    else:
        return False
