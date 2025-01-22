import bpy, math

from ...functions.mesh import (
    create_cutter_shape,
    extrude,
    shade_smooth_by_angle,
)
from ...functions.object import (
    add_boolean_modifier,
    set_cutter_properties,
    delete_cutter,
    set_object_origin,
)
from ...functions.select import (
    selection_fallback,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def custom_modifier_event(self, context, event, key, modifier):
    """Creates custom modifier event when key is held and hides cursor until it's released"""

    if event.value == 'PRESS':
        if not self.move:
            self.cached_mouse_position = (self.mouse_path[1][0], self.mouse_path[1][1])
            context.window.cursor_set("NONE")
            setattr(self, modifier, True)

    elif event.value == 'RELEASE':
        if not self.move:
            context.window.cursor_set("MUTE")
            context.window.cursor_warp(int(self.cached_mouse_position[0]), int(self.cached_mouse_position[1]))
            setattr(self, modifier, False)



#### ------------------------------ /base/ ------------------------------ ####

class CarverModifierKeys():
    """NOTE: Order of the modifier key events is important, because key value might change after function checks for it"""
    """Functions that check last are most important because they can overwrite all modifier states"""

    def modifier_snap(self, context, event):
        """Modifier keys for snapping"""

        self.snap = context.scene.tool_settings.use_snap
        if (self.move == False) and (not hasattr(self, "rotate") or (hasattr(self, "rotate") and not self.rotate)):
    
            # change_the_snap_increment_value_using_the_wheel_mouse
            for i, area in enumerate(context.screen.areas):
                if area.type == 'VIEW_3D':
                    space = context.screen.areas[i].spaces.active

            if event.type == 'WHEELUPMOUSE':
                    space.overlay.grid_subdivisions -= 1
            elif event.type == 'WHEELDOWNMOUSE':
                    space.overlay.grid_subdivisions += 1

            # invert_snapping
            if event.ctrl:
                self.snap = not self.snap


    def modifier_aspect(self, context, event):
        """Modifier keys for changing aspect of the shape"""

        if event.shift:
            if self.initial_aspect == 'FREE':
                self.aspect = 'FIXED'
            elif self.initial_aspect == 'FIXED':
                self.aspect = 'FREE'
        else:
            self.aspect = self.initial_aspect


    def modifier_origin(self, context, event):
        """Modifier keys for changing the origin of the shape"""

        if event.alt:
            if self.initial_origin == 'EDGE':
                self.origin = 'CENTER'
            elif self.initial_origin == 'CENTER':
                self.origin = 'EDGE'
        else:
            self.origin = self.initial_origin


    def modifier_rotate(self, context, event):
        """Modifier keys for rotating the shape"""

        if event.type == 'R':
            custom_modifier_event(self, context, event, "rotate")


    def modifier_bevel(self, context, event):
        """Modifier keys for beveling the shape"""

        if self.shape == 'BOX':
            if event.type == 'B':
                custom_modifier_event(self, context, event, "bevel")

            if self.bevel:
                self.use_bevel = True

                if event.type == 'WHEELUPMOUSE':
                    self.bevel_segments += 1
                elif event.type == 'WHEELDOWNMOUSE':
                    self.bevel_segments -= 1


    def modifier_array(self, context, event):
        """Modifier keys for creating the array of the shape"""

        if event.type == 'LEFT_ARROW' and event.value == 'PRESS':
            self.rows -= 1
        if event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
            self.rows += 1
        if event.type == 'DOWN_ARROW' and event.value == 'PRESS':
            self.columns -= 1
        if event.type == 'UP_ARROW' and event.value == 'PRESS':
            self.columns += 1

        if (self.rows > 1 or self.columns > 1) and (event.type == 'A'):
            custom_modifier_event(self, context, event, event.type, "gap")


    def modifier_move(self, context, event):
        """Modifier keys for moving the shape"""

        if event.type == 'SPACE':
            if event.value == 'PRESS':
                self.move = True
            elif event.value == 'RELEASE':
                self.move = False

        if self.move:
            # reset_initial_position_before_moving_the_shape
            if self.initial_position is False:
                self.position_offset_x = 0
                self.position_offset_y = 0
                self.last_mouse_region_x = event.mouse_region_x
                self.last_mouse_region_y = event.mouse_region_y
                self.initial_position = True
        else:
            # update_the_shape_coordinates
            if self.initial_position:
                for i in range(0, len(self.mouse_path)):
                    l = list(self.mouse_path[i])
                    l[0] += self.position_offset_x
                    l[1] += self.position_offset_y
                    self.mouse_path[i] = tuple(l)

                self.position_offset_x = self.position_offset_y = 0
                self.initial_position = False


class CarverBase():

    def redraw_region(self, context):
        """Redraw region to find the limits of the 3D viewport"""

        region_types = {'WINDOW', 'UI'}
        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if not region_types or region.type in region_types:
                        region.tag_redraw()


    def validate_selection(self, context, shape='BOX'):
        """Filters out objects that are not inside the selection shape bounding box"""
        """Returns selection state (so operator can be cancelled if there are no objects inside the selection bounding box)"""

        self.selected_objects = selection_fallback(self, context, self.selected_objects, shape=shape, include_cutters=True)

        # silently_fail_if_no_objects_inside_selection_bounding_box
        if len(self.selected_objects) == 0:
            selection = False
        else:
            selection = True

        return selection


    def confirm(self, context):
        create_cutter_shape(self, context)
        extrude(self, self.cutter.data)
        set_object_origin(self.cutter)
        if self.auto_smooth:
            shade_smooth_by_angle(self.cutter, angle=math.degrees(self.sharp_angle))

        self.Cut(context)
        self.cancel(context)


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.workspace.status_text_set(None)
        context.window.cursor_set('DEFAULT' if context.mode == 'OBJECT' else 'CROSSHAIR')


    def Cut(self, context):
        # ensure_active_object
        if not context.active_object:
            context.view_layer.objects.active = self.selected_objects[0]

        # Add Modifier
        for obj in self.selected_objects:
            if self.mode == 'DESTRUCTIVE':
                add_boolean_modifier(self, context, obj, self.cutter, "DIFFERENCE", self.solver, apply=True, pin=self.pin, redo=False)
            elif self.mode == 'MODIFIER':
                add_boolean_modifier(self, context, obj, self.cutter, "DIFFERENCE", self.solver, pin=self.pin, redo=False)
                obj.booleans.canvas = True

        if self.mode == 'DESTRUCTIVE':
            # Remove Cutter
            delete_cutter(self.cutter)

        elif self.mode == 'MODIFIER':
            # Set Cutter Properties
            canvas = None
            if context.active_object and context.active_object in self.selected_objects:
                canvas = context.active_object    
            else:
                canvas = self.selected_objects[0]

            set_cutter_properties(context, canvas, self.cutter, "Difference", parent=self.parent, hide=self.hide)
