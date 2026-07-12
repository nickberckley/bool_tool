# Configuring Cutter
Boolean operators configure objects used by Boolean modifiers that they have created into "cutters". Essentially, that configuration consists of excluding the cutter object entirely from all purposes. Cutters will not be rendered or otherwise taken into account during rendering.

This page lists all changes that happen to objects when they become cutters:

1. Cutters are hidden from render (`hide_render` property).

2. Viewport display type of cutter is set to "Bounds" or "Wire", depending on add-on preference. This essentially makes cutters invisible, therefore allowing users to see the effect of modifiers that use them, but still selectable, so that they can be transformed for non-destructive, real-time updates.

3. Cutters are excluded from Line Art usage so that Grease Pencil modifiers that create scene-wide or collection-wide line arts do not draw upon cutters.

4. All ray visibility settings are turned off for cutters. This makes cutters invisible to cameras, raycasts, light, compositors, light probes, etc.

5. Cutters are placed inside the special "boolean_cutters" collection that the add-on itself creates (if it does not already exist). This collection is fully managed by an add-on and will be removed if there are no cutters remaining in the scene.

:::{note}
The fifth step can be avoided. Cutters' collection management can be entirely disabled in add-on preferences. The name of the collection can also be configured there.
:::
