import bpy

from .list import (
    list_canvas_cutters,
    list_cutter_users,
)
from .object import (
    convert_to_mesh,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def basic_poll(cls, context, check_linked=False):
    """Basic poll for boolean operators."""

    if context.mode != 'OBJECT':
        return False
    if context.active_object is None:
        return False

    obj = context.active_object
    if obj.type != 'MESH':
        cls.poll_message_set("Boolean operators can only be used for mesh objects")
        return False

    if check_linked and is_linked(context, obj) == True:
        cls.poll_message_set("Boolean operators can not be executed on linked objects")
        return False

    return True


def is_linked(context, obj):
    """Checks whether the object is linked from an external .blend file (including library-overrides)."""

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
    """Checks whether the object is a boolean canvas (i.e. has boolean cutters)."""

    if obj.booleans.canvas == False:
        return False
    else:
        # Even if object is marked as canvas, check if it actually has any cutters
        cutters, __ = list_canvas_cutters([obj])
        if len(cutters) > 0:
            return True
        else:
            return False


def is_instanced_data(obj):
    """Checks if `obj.data` has more than one users, i.e. is instanced."""
    """Function only considers object types as users, and excludes pointers."""

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


def active_modifier_poll(obj):
    """Checks whether the active modifier for active object is a boolean."""

    # Check if active modifier exists.
    if len(obj.modifiers) == 0:
        return False
    if obj.modifiers.active is None:
        return False

    # Check if active modifier is a boolean with a valid object.
    modifier = obj.modifiers.active
    if modifier.type != "BOOLEAN":
        return False
    if modifier.object is None:
        return False

    return True


def has_evaluated_mesh(context, obj):
    """Checks if an object (non-mesh type) has an evaluated mesh created by Geometry Nodes modifiers."""

    depsgraph = context.view_layer.depsgraph
    obj_eval = depsgraph.id_eval_get(obj)
    geometry = obj_eval.evaluated_geometry()

    if geometry.mesh:
        return True
    else:
        return False


def list_candidate_objects(self, context, canvas):
    """Filter out objects from the selection that can't be used as a cutter."""

    cutters = []
    for obj in context.selected_objects:
        if obj == context.active_object:
            continue
        if is_linked(context, obj):
            self.report({'WARNING'}, f"{obj.name} is linked and can not be used as a cutter")
            continue

        if obj.type == 'MESH':
            # Exclude if object is already a cutter for canvas.
            if canvas in list_cutter_users([obj]):
                continue
            # Exclude if canvas is cutting the object (avoid dependancy loop).
            if obj in list_cutter_users([canvas]):
                self.report({'WARNING'}, f"{obj.name} can not cut its own cutter (dependancy loop)")
                continue

            cutters.append(obj)

        elif obj.type in ('CURVE', 'FONT'):
            if has_evaluated_mesh(context, obj):
                convert_to_mesh(context, obj)
                cutters.append(obj)

    return cutters
