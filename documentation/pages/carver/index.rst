
Carver
======

.. image:: /.images/carver_icons.png
   :alt: Carver tools

Carver tools are a set of workspace tools for interactively creating Boolean cutters and carving the object. Unlike Boolean operators, which require existing objects to be used as cutters, Carver tools allow the user to create cutters by drawing simple shapes in the 3D viewport and extruding them.

All tools are designed to closely mimic the behavior and UX of Blender's various built-in gesture and object creation tools, such as "Add Object" tools in Object & Edit modes, and "Trim" tools in Sculpt mode. But unlike those, Carver tools offer non-destructive carving by using newly created objects as Boolean modifier cutters.

There are three Carver tools available in Object and Edit modes, each offering a different form of interaction for drawing primitive shapes:

- Box
- Circle
- Polyline


Workflow
--------
Carver tools work on selected Mesh type :ref:`objects that can be cut <filtering_canvases>`. All selected objects are considered canvases as long as the created cutter object overlaps with them and actually performs a meaningful cut. With one of the tools active in the workspace and viable canvases selected, the user can start drawing shapes with :kbd:`LMB` (by pressing for some tools and click-dragging for others). Depending on the tool, holding :kbd:`Shift`, :kbd:`Ctrl`, :kbd:`Alt`, or their combinations before or after starting to draw can change the behavior of drawing.

The process of creating cutters is split into two main parts: the drawing phase, when the primitive 2D shape is drawn on the screen, and the extrusion phase, when that shape is confirmed and given depth to make a manifold Mesh object. Individual tools also have other phases for more detailed control and additional features. They will be described separately for each tool.

Carver tools, just like Boolean operators, support two workflows:

Modifier Mode
~~~~~~~~~~~~~
*Equivalent of Brush Boolean operators.*

In the non-destructive "Modifier" workflow, tools add Boolean modifier(s) to canvas object(s) and use the newly created object as the cutter, which is :doc:`configured into cutter <../booleans/configuring_cutter>` and added to the Boolean cutters collection. Keeping modifiers unapplied allows for changing the cut by repositioning the cutter or modeling it into a different shape.

.. tip::
   Keeping many Boolean modifiers unapplied, especially on objects with dense geometries, can have a performance cost. If experiencing performance issues when using tools extensively, it is recommended to apply modifiers and finalize cuts from time to time using add-ons "Apply All Cutters" operator.

Destructive Mode
~~~~~~~~~~~~~~~~~
*Equivalent of Auto Boolean operators*

In the destructive workflow, Boolean modifiers are applied on objects upon their creation, and the newly drawn object is discarded. However, with default add-on preferences *all* modifiers are applied, not just newly created ones, but the way and order modifiers are applied are configurable and can be drastically different from one another. :doc:`Read more about it here <../booleans/applying_modifiers>`.


.. Indexing:
.. toctree::
   :maxdepth: 1
   :hidden:

   Workplane <workplane.md>
   Depth <depth.md>
