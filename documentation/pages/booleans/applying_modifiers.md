# Applying Modifiers

Multiple operators and tools in Bool Tool are applying modifiers on objects (most notably [Auto Boolean](auto_booleans.md) operators), and all of those are following the same behavior defined in add-on preferences. There are drastic differences between existing options, they dictate which modifiers are applied and in what order. This can have a significant difference on the final result, and the user might need to switch between them depending on the task.

## Apply Order
The main behavior is defined by the "Apply Modifiers" add-on preference (found in the "Shared" category), which has three options, but other preferences or tool settings can affect the behavior as well.

### (1) Apply All [_default_]
Operators will apply all modifiers present (and shape keys) to the object alongside Boolean modifiers, essentially "flattening" or "baking down" the mesh. This behavior is effectively the same as manually converting to mesh or using the "Apply Visual Geometry to Mesh" operator.

### (2) Apply Booleans & Everything Before [_recommended_]
Operators that need to apply modifiers will detect the last Boolean modifier in the stack and only apply modifiers up to that one, leaving everything that comes after the last Boolean modifier in place. This is slightly more complex than applying all, and in rare cases might be slower, but it offers the most flexibility.

The reason why it's important to apply modifiers that come before is that each modifier works on the geometry outputted by the previous one (and in the case of the first modifier in the stack, the real geometry). If the Boolean modifier, for example, sits below the Bevel one, but only Boolean is applied, the Bevel modifier will have to perform beveling on the updated real geometry left behind and drastically altered by the Boolean, which will completely change the final result. Modifiers that come after the last Boolean, in theory, do not have that problem if everything below them is applied at the same time.

This option is most useful when combined with the "Pin Boolean Modifiers" option (found for Boolean operators in add-on preferences and for Carver tools in the "Cutter" dropdown). Combining these two means that Boolean modifiers created by the add-on will always be at the top of the modifier stack (unless the user moves them down manually), and only they will be applied. This allows users to not worry about the modifier stack at all, as their effect will be the same if modifiers are present or applied.

### (3) Apply Booleans
This option will force operators to only apply Boolean modifiers, and nothing more. This option can have the most unexpected results if the applied Boolean modifiers are not first in the stack. Similar to option (2), combining this option with the "Pin Boolean Modifiers" option is most recommended.

The behavior of this option is different depending on which operator or tool is being used.
- Operators and tools that create new modifiers (Auto Boolean, Carver) will _only_ apply the modifiers they created in that instance. If the canvas object(s) already have unapplied Boolean modifiers, they won't be touched.
- Operators that apply all existing cutters on canvases will apply all Boolean modifiers present, but nothing else.
- Operators that apply selected cutter(s) to all canvases that use them will only apply modifiers that specifically reference them.
- Operators that apply the selected cutter to the selected canvas will only apply one Boolean modifier.


## Ways of Applying Modifiers
Modifiers can be applied in multiple ways with Blender's API. The add-on differentiates between two ways, one of which is experimental and disabled by default.

By default, modifiers are applied with built-in Blender operators (`bpy.ops`). Same ones that are exposed to users in various menus. Operators for applying individual modifiers, or converting to mesh (which essentially applies all of them), are being used.

The second method, which can be enabled from add-on preferences ("Add-on" category, called "Faster Destructive Booleans"), uses a lower-level API to replicate the effect of the aforementioned operators without the performance overhead that comes with them. In essence, this method constructs a new mesh from the visual result of the evaluated canvas object and replaces the old mesh with it. On average this results in 30% to 50% faster destructive operators.

However, the experimental method currently has some downsides. Most notably, some of the mesh attributes might not be correctly transferred to the new mesh, and some of the Boolean solver options might be ignored. If the user does not care about those issues and they're following Boolean modeling workflows that do not require attributes or niche solver options, it is recommended to enable this option for performance gains.
