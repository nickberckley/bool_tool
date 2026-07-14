# Filtering Objects
All of the Bool Tool operators are filtering selected objects to determine if they're viable for Boolean operators. There are different requirements for being a cutter and being a canvas that the object must meet.


(filtering_cutters)=
## Requirements for Cutters
1. A linked or library-overridden object cannot be used as a cutter.

2. Objects that are already cutting the selected canvas will be excluded. Using one object for multiple Boolean modifiers has no practical effects and will introduce corrupted geometry and performance issues. Bool Tool protects against this.

3. If the object is being cut by the selected canvas it will not be allowed to become a cutter of said canvas. This avoids corrupted geometry and dependency cycle, where two objects are cutting each other simultaneously.

4. The evaluated object must be outputting Mesh to be used as a cutter.
Essentially, what this means is that the object must have actual Mesh geometry that the Boolean solver can use. Even though objects that are Mesh type by default have a geometry, they're not always viable, and they're not the only object type that can have geometry either. Bool Tool uses final, evaluated geometry, meaning it takes the result of modifiers (and shape keys) into account. If a Mesh type object does not have a geometry (because it was deleted in the Edit Mode, or Geometry Nodes modifiers don't output Mesh) it is not viable.

Some other object types can also be used as cutters. <kbd>Curve</kbd>, <kbd>(Hair) Curves</kbd>, <kbd>Text</kbd>, and <kbd>Empty</kbd> type objects can be used as cutters if they have Geometry Nodes modifiers that output Mesh.

:::{important}
In order to use those types as cutters they need to be converted to Mesh type first. This is a destructive operation that will apply modifiers. Bool Tool operators will not perform this task until the user confirms it in the pop-up.
:::

Object types that cannot have geometry by design (Camera, Light, Armature, etc.) are automatically excluded. There are also certain object types that can output geometry through Geometry Nodes modifiers but are not able to convert to Mesh.


(filtering_canvases)=
## Requirements for Canvases
1. A linked or library-overridden object cannot be used as a canvas. Technically, library-overridden objects are allowed to have modifiers in Blender, but there have not been legitimate use cases for supporting them yet, and the add-on excludes them to avoid performance and other issues.

2. Only Mesh type object can be a canvas.

:::{note}
This limitation exists because the built-in Boolean modifier can only be added to Mesh type objects in Blender. However, Geometry Nodes implementation is type-agnostic and can be used on any type of object if it outputs Mesh. If/when the add-on switches to using Geometry Nodes instead of legacy modifiers, this limitation will be lifted.
:::

3. _Specifically for Destructive mode of Carver tools, object with shape keys or instanced object data cannot be used as canvases, since modifiers cannot be applied to them due to Blender's limitations._
