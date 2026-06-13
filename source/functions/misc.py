import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def _guess_toggle_state(modifiers):
    """Guess whether cutters should be hidden or revealed."""

    enabled = 0
    disabled = 0
    for mod in modifiers:
        if mod.show_viewport:
            enabled += 1
        else:
            disabled += 1

    if enabled > disabled:
        return "On"
    else:
        return "Off"


def _get_modifier_from_list_index(obj, index: int):
    """
    Returns the modifier of an object based on Cutters list index.
    Filters out non-Boolean modifiers to leave a list that matches Cutters one in length.
    """

    modifiers = obj.modifiers
    boolean_modifiers = []

    for mod in modifiers:
        if mod.type == 'BOOLEAN' and mod.object is not None:
            boolean_modifiers.append(mod)

    if 0 <= index < len(boolean_modifiers):
        return boolean_modifiers[index]

    return None
