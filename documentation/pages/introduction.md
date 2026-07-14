# Introduction to Bool Tool

Bool Tool is an extension for Blender that aims to simplify hard-surface modeling operations specifically related to Booleans. Bool Tool doesn't offer any alternatives to existing Boolean solvers in Blender (therefore, it doesn't offer faster Booleans), nor does it invent any new systems. Bool Tool simply offers tools for quickly adding, managing, and applying Boolean modifiers (and cutters that they use).

While Bool Tool also offers numerous smaller tools and enhancements, like a manageable list of Boolean cutters, collection management, and others, the main content that Bool Tool adds to Blender can be split into three categories:
- [Boolean operators](booleans/brush_booleans.md) (for quickly adding modifiers & setting up cutter objects)
- Utility operators (for managing existing cutters and canvases: toggling, removing, selecting, etc.)
- [Carving tools](carver/index.rst) (for drawing cutters interactively and using them for Boolean operations)


(terminology)=
## Add-on Terminology
- ___Canvas___ - the object that is being cut by Boolean modifiers.
- ___Cutter___ - the object that is used by Boolean modifier to cut other object(s). Usually hidden from render and displayed as wires or bounds.
- ___Slice___ - the object that was cut off from canvas by "Slice" Boolean operators. Slices are duplicates of canvases in every way except geometry.
- ___Brush Boolean___ (sometimes referred to as Modifier mode) - Operators that add Boolean modifiers on active object (canvas) that use selected objects, which are "transformed" into cutters. Maintaining modifiers allows for non-destructive modeling.
- ___Auto Boolean___ (sometimes referred to as Destructive mode) - Operators that add Boolean modifiers on active object (canvas) that use selected objects as cutters. Operators apply modifiers immediately, and optionally delete cutter objects, allowing for quick destructive modeling.
