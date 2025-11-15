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


def destructive_op_confirmation(self, context, event, canvases: list, title="Boolean Operation"):
    """
    Creates & returns the confirmation pop-up window for destructive boolean operators.\n
    Confirmation window is triggered by canvas objects that have instanced object data or shape keys.\n
    If none of the canvas objects have them the operator is executed without any confirmation.
    """

    has_instanced_data = any(obj for obj in canvases if is_instanced_data(obj))
    has_shape_keys = any(obj for obj in canvases if obj.data.shape_keys)

    if has_instanced_data or has_shape_keys:
        # Instanced data message.
        if has_instanced_data and not has_shape_keys:
            message = ("Object(s) you're trying to cut have instanced object data.\n"
                       "In order to apply modifiers, they need to be made single-user.\n"
                       "Do you proceed?")

        # Shape keys message.
        if has_shape_keys and not has_instanced_data:
            message = ("Object(s) you're trying to cut have shape keys.\n"
                       "In order to apply modifiers shape keys need to be applied as well.\n"
                       "Do you proceed?")

        # Combined message.
        if has_instanced_data and has_shape_keys:
            message = ("Object(s) you're trying to cut have shape keys and instanced object data.\n"
                       "In order to apply modifiers shape keys need to be applied, and object data made single user.\n"
                       "Do you proceed?")

        popup = context.window_manager.invoke_confirm(self, event, title=title,
                                                      confirm_text="Yes", icon='WARNING',
                                                      message=message)

        return popup

    # Execute without confirmation window.
    else:
        return self.execute(context)
