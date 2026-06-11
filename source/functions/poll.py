import bpy

from ..constants import CONVERTABLE_TYPES
from .list import (
    list_canvas_cutters,
    list_cutter_users,
)
from .object import (
    convert_to_mesh,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def basic_poll(cls, context, check_active=True):
    """Basic poll for boolean operators."""

    if context.mode != 'OBJECT':
        cls.poll_message_set("Boolean operators can only be performed in Object Mode")
        return False

    if check_active:
        if context.active_object is None:
            cls.poll_message_set("No active object")
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

    # Exclude cases that return Python errors.
    if not obj:
        return False
    if bpy.app.version < (5, 2, 0) and obj.type == 'EMPTY':
        return False
    if obj.instance_type != 'NONE':
        return False

    depsgraph = context.view_layer.depsgraph
    obj_eval = depsgraph.id_eval_get(obj)

    geometry = None
    try:
        geometry = obj_eval.evaluated_geometry()
    except:
        pass

    if not geometry or not geometry.mesh:
        return False
    else:
        return True


def filter_canvases(self, context, canvases: list) -> list:
    """Filter out objects from the give list if they can't be cut."""

    usable_canvases = []
    for canvas in canvases:
        # Exclude non-Mesh types.
        if canvas.type != 'MESH':
            self.report({'WARNING'}, f"{canvas.name} is not a Mesh type. Only Meshes can be cut")
            continue
        # Exclude linked objects.
        if is_linked(context, canvas):
            self.report({'WARNING'}, f"{canvas.name} is linked and can not be used as a cutter")
            continue

        usable_canvases.append(canvas)

    return usable_canvases


def filter_cutters(self, context, cutters: list, canvases: list) -> list:
    """Filter out objects from the given list if they can't be used as a cutter."""

    usable_cutters = []
    for cutter in cutters:
        # Exclude object if it is in both lists.
        if cutter in canvases:
            continue
        # Exclude linked objects.
        if is_linked(context, cutter):
            self.report({'WARNING'}, f"{cutter.name} is linked and can not be used as a cutter")
            continue

        if cutter.type == 'MESH':
            # Exclude if object is already a cutter for canvas.
            users, __ = list_cutter_users([cutter])
            if any(canvas in users for canvas in canvases):
                continue
            # Exclude if canvas is cutting the object (avoid dependancy loop).
            users, __ = list_cutter_users(canvases)
            if cutter in users:
                self.report({'WARNING'}, f"{cutter.name} can not cut its own cutter (dependancy loop)")
                continue

            usable_cutters.append(cutter)

        elif cutter.type in CONVERTABLE_TYPES:
            if not has_evaluated_mesh(context, cutter):
                continue

            convert_to_mesh(context, cutter)
            usable_cutters.append(cutter)

    return usable_cutters


def destructive_op_confirmation(self, context, event, canvases: list, title="Boolean Operation"):
    """
    Creates & returns the confirmation pop-up window for destructive boolean operators.\n
    Confirmation window is triggered by canvas objects that have instanced object data or shape keys.\n
    If none of the canvas objects have them the operator is executed without any confirmation.
    """

    if len(canvases) == 0:
        return self.execute(context)

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
                       "In order to apply modifiers shape keys need to be applied & object data made single user.\n"
                       "Do you proceed?")

        popup = context.window_manager.invoke_confirm(self, event, title=title,
                                                      confirm_text="Yes", icon='WARNING',
                                                      message=message)

        return popup

    # Execute without confirmation window.
    else:
        return self.execute(context)


def convert_to_mesh_confirmation(self, context, event, cutters: list, title="Boolean Operation"):
    """
    Creates & returns the confirmation pop-up window when object is about to be
    converted to mesh to be used as a cutter. Only triggers during brush boolean
    operators, because object gets destroyed in the destructive one anyway.

    NOTE: This is only required because of the limitation of legacy Boolean modifier.
    Geometry nodes implementation works with any object type. When the add-on is
    updated to work with custom modifiers this will not be necesary anymore.
    """

    if len(cutters) == 0:
        return self.execute(context)

    is_convertable = any(
        obj.type in CONVERTABLE_TYPES and has_evaluated_mesh(context, obj)
        for obj in cutters
    )

    if is_convertable:
        message = ("Some of the selected objects are not of the Mesh type, but output mesh.\n"
                   "In order to use them as cutters, they need to be converted to mesh.\n"
                   "This is a destructive operator. Do you proceed?")

        popup = context.window_manager.invoke_confirm(self, event, title=title,
                                                      confirm_text="Yes", icon='WARNING',
                                                      message=message)

        self._unflippable = True
        return popup

    # Execute without confirmation window.
    else:
        return self.execute(context)
