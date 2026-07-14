# Carver Workplane (Alignment)

The main purpose of Carver tools is to allow creating cutters by drawing simple 2D shapes in the 3D viewport and extruding them, but drawing a 2D shape in the 3D space is not always straightforward. The main question is what the drawing is aligned to, and there are multiple options for that.

Carver tools, based on the "Alignment" tool property and the context they were called in, initialize a drawing plane: an invisible flat plane positioned and rotated in the 3D viewport on which the actual drawing happens. This is called the _Workplane_. The workplane decides both the orientation of the drawing and its actual position in the 3D world.

:::{hint}
If you're familiar with Grease Pencil, the concept of Workplane is the same as Canvas in Grease Pencil draw mode, although options for placement and alignment are different between tools because of their unique needs. If you want to better understand how Workplane functions, you can enable Canvas overlay visualization for the Grease Pencil object and play with "Drawing Plane" and "Stroke Placement" settings in the 3D viewport header.
:::

```{figure} /.images/carver_alignment.png
:alt: Carver Alignment Methods

This figure shows the result of all four alignment methods for the same gesture (same initial mouse-click position and same size).
```

## Surface Alignment
Chosen for all tools by default, the "Surface" alignment method creates a workplane that is aligned to the face of the canvas object that the user clicked on when starting to draw (or, in other words, the workplane is aligned to the face of the mesh under the mouse cursor). If the user started drawing on an empty space and there is no geometry under the mouse, tools fall back to "View" alignment.

For ray casting, i.e., detecting the face directly under the mouse cursor, tools use evaluated objects, meaning that the geometry is sampled with the effect of modifiers (most importantly existing Boolean modifiers) taken into account.

"Surface" method has additional settings for fine-tuning the alignment (all found in the "Shape" dropdown menu):

### Orientation
The face of the geometry that is sampled decides where the workplane should be placed - on top of the face. But the orientation (a.k.a. X-Y rotation) of the workplane is not final. It can be rotated in several ways (manually as well, once the drawing starts), but the initial orientation is chosen from three options:

- "__Face Normal__" method simply uses the normal of the face for the orientation, without any modifications. This is the simplest to calculate, but the most unpredictable, as the face normal can be pointing out seemingly randomly. Still, this method has the potential to give users the most control, since normals of faces can be manually transformed.

- "__Closest Edge__" method (_default_) orients the workplane to be aligned to the closest edge to the mouse. This is the most predictable and controllable method. Users can not only see exactly how the drawing will be rotated by looking at the closest edge, but they can also pick different edges of the face and start drawing near them to get the desired orientation.

The images below show how the orientation of the shape can change depending on which edge was closest to the cursor (highlighted in lime green) when it was first clicked on the face. If the face is a perfect square and a quad, the orientation will be the same regardless of which edge is closest.

| #1 | #2 | #3 |
| --- | --- | --- |
| ![Closest Edge #1](/.images/carver_orientation_closest_edge_1.png) | ![Closest Edge #2](/.images/carver_orientation_closest_edge_2.png) | ![Closest Edge #3](/.images/carver_orientation_closest_edge_3.png) |

- "__Longest Edge__" method also orients the workplane to be aligned to the edge of the face, but instead of picking the one based on starting position it always favors the longest edge. In the same situation that is shown in the images above, the "Longest Edge" method would always align the workplane as shown in image #3, regardless of where the drawing started.

:::{note}
Orientation is not relevant for the Polyline tool, since it does not have a pre-defined shape and instead allows users to construct it from ground up, orienting it as they wish in the process.
:::

### Offset
The "Offset from Surface" setting (set to 0.1 by default) pushes the workplane away from the face of the geometry by a given amount. This is necessary to avoid Z-fighting and corrupted geometry, which happens when the faces of canvas and cutter objects are in the exact same place.

### Align to Anything
By default, the workplane can be aligned to any object in the scene that has geometry, even if it's not selected and won't be carved by the tool, to offer more flexibility. When the "Align to Anything" setting is disabled, only selected objects will be aligned to.

Non-selected objects will be completely excluded from depth-picking when ray casting, which makes it possible to draw on selected objects even if they're occluded by non-selected ones. This can be most useful in heavily populated scenes.


## View Alignment
The "View" method creates a workplane that is perfectly aligned to the screen. However, the screen can only dictate the orientation, and not the placement, since it does not exist as a point in the 3D world.

For the position of the workplane, tools calculate the collective bounding box of all selected objects, then calculate the point on that box that is closest to the viewport camera, and place the workplane there (with some offset to avoid Z-fighting). This ensures that the drawing happens exactly where the cutter is needed, and it does not produce overly elongated shapes.

Aligning to view is most useful when working in orthographic side views. The "Surface" alignment method still performs a ray cast even in side views, it allows the workplane to be aligned to faces that are not perfectly aligned to sides. The "View" method, on the other hand, essentially aligns the workplane to the grid, resulting in perfectly rotated cutters.


## 3D Cursor Alignment
The "3D Cursor" alignment method offers the most flexibility and is designed for complex workflows. "Surface" and "View" methods are dynamic; they are dependent on positions of the viewport camera and mouse; they're designed to be quick and iterative and allow for positioning cutters differently each time. "3D Cursor" method, on the other hand, is more rigid. It uses the same workplane for all cuts. This is most useful when the user wants to position the workplane with perfect accuracy and "freeze" it.

By default, this method will act similarly to the "Grid" alignment method, but that only happens if the 3D Cursor is at the world origin. Changing the position and orientation of the 3D Cursor with keymaps or dedicated tools will essentially reposition and reorient the workplane with it.

The exact axis of the 3D Cursor on which to align can be picked in the "Shape" dropdown menu (option called "Align to").


## Grid Alignment
The simplest method of alignment, the "Grid" method, always aligns to the grid in the 3D world. It cannot be changed or modified in any way. In "user" views, the workplane is placed on the visible floor of the 3D viewport. In side views, the workplane is placed with the same logic as in the "View" method.
