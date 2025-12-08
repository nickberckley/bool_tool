import bpy
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def cursor_snap(self, context, event, mouse_pos):
    """Find the closest position on the overlay grid and snap the mouse on it"""

    region = context.region
    rv3d = context.region_data

    for i, a in enumerate(context.screen.areas):
        if a.type == 'VIEW_3D':
            space = context.screen.areas[i].spaces.active

    # get_the_grid_overlay
    grid_scale = space.overlay.grid_scale
    grid_subdivisions = space.overlay.grid_subdivisions

    # use_grid_scale_and_subdivision_to_get_the_increment
    increment = (grid_scale / grid_subdivisions)
    half_increment = increment / 2

    # convert_2d_location_of_the_mouse_in_3d
    for index, loc in enumerate(reversed(mouse_pos)):
        mouse_loc_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc, (0, 0, 0))

        # get_the_remainder_from_the_mouse_location_and_the_ratio (test_if_the_remainder_>_to_the_half_of_the_increment)
        for i in range(3):
            modulo = mouse_loc_3d[i] % increment
            if modulo < half_increment:
                modulo = -modulo
            else:
                modulo = increment - modulo

            # add_the_remainder_to_get_the_closest_location_on_the_grid
            mouse_loc_3d[i] = mouse_loc_3d[i] + modulo

        snap_loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, mouse_loc_3d)

        # replace_the_last_mouse_location_by_the_snapped_location
        if len(self.mouse_path) > 0:
            self.mouse_path[len(self.mouse_path) - (index + 1) ] = tuple(snap_loc_2d)
