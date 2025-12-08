import bpy
import bmesh
from contextlib import contextmanager
from .. import __package__ as base_package

from .object import (
    convert_to_mesh,
)
from .poll import (
    is_instanced_data,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def add_boolean_modifier(self, context, obj, cutter, mode, solver, pin=False, redo=True):
    "Adds boolean modifier with specified cutter and properties to a single object"

    if bpy.app.version < (5, 0, 0) and solver == 'FLOAT':
        solver = 'FAST'

    prefs = context.preferences.addons[base_package].preferences

    modifier = obj.modifiers.new("boolean_" + cutter.name.replace("boolean_", ""), 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver

    # Set solver options (inherited from operator properties).
    if redo:
        modifier.material_mode = self.material_mode
        modifier.use_self = self.use_self
        modifier.use_hole_tolerant = self.use_hole_tolerant
        modifier.double_threshold = self.double_threshold

    if prefs.show_in_editmode:
        modifier.show_in_editmode = True

    # Move modifier to the index 0 (make it first in the stack).
    if pin:
        index = obj.modifiers.find(modifier.name)
        obj.modifiers.move(index, 0)

    return modifier


def apply_modifiers(context, obj, modifiers: list, force_clean=False):
    """
    Apply modifiers on object.
    Instead of using `bpy.ops.object.modifier_apply`, this function uses
    `bpy.data.meshes.new_from_object` built-in function to create a temporary
    mesh from the evaluated object (basically with visible modifiers applied).
    Temporary mesh is then transferred to objects mesh with `bmesh`.

    This method is up to 2x faster, although it's considered experimental
    and may fail in some cases, so a fallback to `bpy.ops.object.modifier_apply` is kept.
    """

    prefs = context.preferences.addons[base_package].preferences

    # Make object data unique if it's instanced.
    if is_instanced_data(obj):
        context.active_object.data = context.active_object.data.copy()

    try:
        # Don't use this method if it's not enabled by user in preferences, unless caller forces it.
        if not prefs.fast_modifier_apply:
            if not force_clean:
                raise Exception()

        with hide_modifiers(obj, excluding=modifiers):
            # Create a temporary mesh from evaluated object.
            evaluated_obj = obj.evaluated_get(context.evaluated_depsgraph_get())
            temp_data = bpy.data.meshes.new_from_object(evaluated_obj)

            # Create `bmesh` from temporary mesh and update edit mesh.
            if context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                bm.clear()
                bm.from_mesh(temp_data)
                bmesh.update_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(temp_data)
                bm.to_mesh(obj.data)
            bm.free()
            evaluated_obj.to_mesh_clear()

            # Remove modifiers and purge temporary mesh.
            bpy.data.meshes.remove(temp_data)
            for mod in modifiers:
                obj.modifiers.remove(mod)

            # Remove shape keys if there are any.
            # (after above operations none of the shape keys have any effect).
            if obj.data.shape_keys:
                obj.shape_key_clear()

    # Use `bpy.ops` operator to apply modifiers if above fails.
    except Exception as e:
        # print("Error applying modifiers with `bmesh` method:", e, "falling back to `bpy.ops` method")

        context_override = {"active_object": obj, "mode": 'OBJECT'}
        with context.temp_override(**context_override):
            # Apply shape keys if there are any.
            if obj.data.shape_keys:
                bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

            # If all modifiers need to be applied convert to Mesh.
            if modifiers == obj.modifiers.values():
                print("Applying all modifiers by converting to Mesh")
                convert_to_mesh(context, obj)
                return

            for mod in modifiers:
                bpy.ops.object.modifier_apply(modifier=mod.name)


@contextmanager
def hide_modifiers(obj, excluding: list):
    """Hides all modifiers of a given object in viewport except those in excluding list"""

    visible_modifiers = []
    for mod in obj.modifiers:
        if mod in excluding:
            continue
        if mod.show_viewport == True:
            visible_modifiers.append(mod)
            mod.show_viewport = False

    try:
        yield
    finally:
        for mod in visible_modifiers:
            mod.show_viewport = True


def add_modifier_asset(obj, path: str, asset: str):
    """Loads the node group asset and adds a Geometry Nodes modifier using it."""

    try:
        # Load the node group.
        if bpy.app.version >= (5, 0, 0):
            with bpy.data.libraries.load(path, link=True, pack=True) as (data_from, data_to):
                if asset in data_from.node_groups:
                    data_to.node_groups = [asset]

        else:
            with bpy.data.libraries.load(path) as (data_from, data_to):
                if asset in data_from.node_groups:
                    data_to.node_groups = [asset]

        node_group = bpy.data.node_groups[asset]

        # Add modifier on the object.
        mod = obj.modifiers.new(asset, type='NODES')
        mod.node_group = node_group
        mod.show_group_selector = False
        mod.show_manage_panel = False

        return mod

    except Exception as e:
        print("Modifier node group could not be loaded:", e)
        return None
