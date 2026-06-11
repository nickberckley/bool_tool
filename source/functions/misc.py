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
