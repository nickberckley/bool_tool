# Auto Boolean Operators

"Auto Boolean" operators mostly work the same way "[Brush Boolean](brush_booleans.md)" ones do, so it is advised to read the documentation about them first. This page will often reference their inner workings and mention differences between the two. There is little difference in behavior for any of the operator modes but Auto Boolean operators additionally apply the modifiers they create and finalize the cut. This makes Auto Boolean operators destructive.

Auto Boolean operators, similarly can be called from any of the add-ons menus or with keymaps (which are same as for Brush Boolean operators, except with additional <kbd>Shift</kbd> key):

1. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Numpad +</kbd> Destructive version of _Union_
2. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Numpad -</kbd> Destructive version of _Difference_
3. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Numpad *</kbd> Destructive version of _Intersect_
4. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Numpad /</kbd> Destructive version of _Slice_

:::{note}
Add-on keymaps are configurable. The documentation lists default keymaps
:::

## Anatomy of the Operator
Since operators behave mostly similarly to [Brush Boolean](brush_booleans.md) ones, most of the steps are the same. This section will only describe differences and additions or omissions that Auto Boolean operators have.

### (1) Filtering Phase
Auto Boolean operators also perform [filtering](filtering_objects.md) to exclude objects that are not _viable_ cutters and canvases, but there are differences in how they're handled and what is communicated to user.

- Because of the destructive nature of Auto Boolean operators, all cutters objects are deleted from the scene after the operator finishes, and the operator does not notify users that non-Mesh type objects will be converted, since it is not important for objects that will be consumed entirely.

- Because of limitations in Blender, modifiers cannot be applied to objects that have shape keys or are using instanced data (mesh). In order for the operator to succeed shape keys also need to be applied, and object data made unique. The operator will show pop-up to the user and will not perform this task until the user confirms it in the pop-up.

![Destructive Boolean confirmation pop-up](/.images/popup_convert_canvas.png)

### (2) Execution Phase
- Since cutter object(s) will be deleted after the operator anyway, they're not configured, put into collection, parented, marked, or otherwise modified. However, their every face is selected before the modifier is applied, so that newly Boolean modifier selects newly created faces on canvas object(s) as well.

- If deleted cutter objects had any children they're transferred to canvas object(s). This ensures that they won't change the position in the viewport, and won't be left orphaned.

- Modifiers added to canvas object(s) and their slices are applied immediatelly. However, with default add-on preferences _all_ modifiers are applied, not just newly created ones, but the way and order modifiers are applied are configurable and can be drastically different from one another. [Read more about it here](applying_modifiers.md).

### (3) Adjustment Phase
The same as for Brush Boolean operators.
