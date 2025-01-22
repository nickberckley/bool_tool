import bpy, math, mathutils


magic_number = 1.41

#### ------------------------------ FUNCTIONS ------------------------------ ####

def draw_circle(self, subdivision, rotation):
    """Returns the coordinates & indices of a 2d circle in screen-space"""

    def create_2d_circle(self, step, rotation):
        """Create the vertices of a 2d circle at (0, 0)"""

        modifier = 2 if self.shape == 'CIRCLE' else magic_number
        if self.origin == 'CENTER':
            modifier /= 2

        verts = []
        for i in range(step):
            angle = (360 / step) * i + rotation
            verts.append(math.cos(math.radians(angle)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / modifier))
            verts.append(math.sin(math.radians(angle)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / modifier))
            verts.append(0.0)

        verts.append(math.cos(math.radians(0.0 + rotation)) * ((self.mouse_path[1][0] - self.mouse_path[0][0]) / modifier))
        verts.append(math.sin(math.radians(0.0 + rotation)) * ((self.mouse_path[1][1] - self.mouse_path[0][1]) / modifier))
        verts.append(0.0)

        return verts

    tris_verts = []
    indices = []
    verts = create_2d_circle(self, int(subdivision), rotation)

    rotation_matrix = mathutils.Matrix.Rotation(self.rotation, 4, 'Z')
    fixed_point = mathutils.Vector((self.mouse_path[0][0], self.mouse_path[0][1], 0.0))
    current_mouse_position = mathutils.Vector((self.mouse_path[1][0], self.mouse_path[1][1], 0.0))
    shape_center = fixed_point + (current_mouse_position - fixed_point) / 2

    for idx in range((len(verts) // 3) - 1):
        x = verts[idx * 3]
        y = verts[idx * 3 + 1]
        z = verts[idx * 3 + 2]
        vert = mathutils.Vector((x, y, z))
        vert = rotation_matrix @ vert
        vert = vert + fixed_point if self.origin == 'CENTER' else shape_center - vert
        vert += mathutils.Vector((self.position_offset_x, self.position_offset_y, 0.0))
        tris_verts.append(vert)

        i1 = idx + 1
        i2 = idx + 2 if idx + 2 <= ((360 / int(subdivision)) * (idx + 1) + rotation) else 1
        indices.append((0, i1, i2))

    # BEVEL
    if self.use_bevel and self.bevel_radius > 0.01:
        tris_verts, indices = bevel_verts(self, tris_verts, (self.bevel_radius * 50), self.bevel_segments)


    # BOUNDING_BOX
    min_x, min_y, max_x, max_y = get_bounding_box(tris_verts)
    bounds = [
        mathutils.Vector((min_x, min_y, 0)),  # bottom-left
        mathutils.Vector((max_x, min_y, 0)),  # bottom-right
        mathutils.Vector((max_x, max_y, 0)),  # top-right
        mathutils.Vector((min_x, max_y, 0)),  # top-left
        mathutils.Vector((min_x, min_y, 0))   # closing_the_loop_manually
    ]

    return tris_verts, indices, bounds


def draw_polygon(self):
    """Returns polygonal 2d shape in screen-space where each cursor click is taken as a new vertice"""

    indices = []
    coords = []
    for idx, vals in enumerate(self.mouse_path):
        vert = mathutils.Vector([vals[0], vals[1], 0.0])
        vert += mathutils.Vector([self.position_offset_x, self.position_offset_y, 0.0])
        coords.append(vert)

        i1 = idx + 1
        i2 = idx + 2 if idx <= len(self.mouse_path) else 1
        indices.append((0, i1, i2))

    # circle_around_first_point
    radius = self.distance_from_first
    segments = 4

    click_point = [coords[0]]
    for i in range(segments + 1):
        angle = i * (2 * math.pi / segments)
        x = coords[0][0] + radius * math.cos(angle)
        y = coords[0][1] + radius * math.sin(angle)
        z = coords[0][2]
        vector = mathutils.Vector((x, y, z))
        click_point.append(vector)


    # ARRAY (remove_duplicate_verts)
    """NOTE: This is needed to remove extra vertices for duplicates which are not removed because `dict.fromkeys()`..."""
    """NOTE: can't be called on `coords` list, because it contains unfrozen Vectors."""
    unique_verts = []
    for vert in coords:
        if vert not in unique_verts:
            unique_verts.append(vert)

    array_coords = unique_verts if self.closed else unique_verts[:-1]

    return coords, indices, click_point, array_coords


def draw_array(self, verts):
    """Duplicates given list of vertices in rows and columns (on screen-space x and y axis)"""
    """Returns two dicts of lists of vertices for rows and columns separately"""

    # get_bounding_box_of_the_shape
    """NOTE: Calculated separately because verts needed for array differs from verts needed for shape for polyline"""
    min_x, min_y, max_x, max_y = get_bounding_box(verts)

    rows = {}
    if self.rows > 1:
        # Offset
        offset = mathutils.Vector((((max_x - min_x) + (self.rows_gap)), 0.0, 0.0))
        if self.rows_direction == 'LEFT':
            offset.x = -offset.x

        for i in range(self.rows - 1):
            accumulated_offset = offset * (i + 1)
            rows[i] = [vert.copy() + accumulated_offset for vert in verts]

    columns = {}
    if self.columns > 1:
        # Offset
        offset = mathutils.Vector((0.0, -((max_y - min_y) + (self.columns_gap)), 0.0))
        if self.columns_direction == 'UP':
            offset.y = -offset.y

        for i in range(self.columns - 1):
            accumulated_offset = offset * (i + 1)
            columns[i] = [vert.copy() + accumulated_offset for vert in verts]
            for row_idx, row in rows.items():
                columns[(i, row_idx)] = [vert.copy() + accumulated_offset for vert in row]

    return rows, columns


def bevel_verts(self, verts, radius, segments):
    """Takes in list of verts(Vectors) and bevels them, Returns a new list with new vertices"""

    def get_rounded_corner(self, angular_point, p1, p2, radius, segments):
        # get_bounding_box_of_the_shape
        min_x, min_y, max_x, max_y = get_bounding_box(verts)
        width = max_x - min_x
        height = max_y - min_y

        # clamp_radius_to_reduce_clipping
        max_radius = min(width / 2.5, height / 2.5)
        clamped_radius = min(radius, max_radius)

        if radius > clamped_radius:
            radius = clamped_radius


        # calculate_vectors (NOTE: Why it only works when reversed like this is unknown to me)
        if self.bevel_profile == 'CONVEX':
            vector1 = -(p1 - angular_point)
            vector2 = -(p2 - angular_point)
        elif self.bevel_profile == 'CONCAVE':
            vector1 = p2 - angular_point
            vector2 = p1 - angular_point

        # compute_lengths_of_vectors
        length1 = vector1.length
        length2 = vector2.length
        if length1 == 0 or length2 == 0:
            return [angular_point] * segments

        vector1.normalize()
        vector2.normalize()

        # calculate_the_angle_between_the_vectors
        dot_product = vector1.dot(vector2)
        angle = math.acos(max(-1.0, min(1.0, dot_product)))

        arc_length = radius * angle
        segment_length = arc_length / (segments - 1)
        bisector = (vector1 + vector2).normalized()

        # generate_points_along_the_arc
        rounded_corners = []
        for i in range(segments):
            fraction = i / (segments - 1)
            theta = angle * fraction
            interpolated_vector = (vector1 * math.sin(theta) + vector2 * math.cos(theta)).normalized() * radius
            if self.bevel_profile == 'CONVEX':
                point_on_arc = angular_point + interpolated_vector - bisector * (clamped_radius * magic_number)
            elif self.bevel_profile == 'CONCAVE':
                point_on_arc = angular_point + interpolated_vector - bisector / (clamped_radius)
            rounded_corners.append(point_on_arc)

        return rounded_corners

    rounded_verts = []
    indices = []
    num_verts = len(verts)

    for idx in range(num_verts):
        angular_point = verts[idx]
        prev_idx = (idx - 1) % num_verts
        next_idx = (idx + 1) % num_verts

        p1 = verts[prev_idx]
        p2 = verts[next_idx]

        corner_points = get_rounded_corner(self, angular_point, p1, p2, radius, segments)
        rounded_verts.extend(corner_points)

    for idx, vert in enumerate(reversed(rounded_verts)):
        i1 = idx + 1
        i2 = idx + 2 if idx + 2 <= len(rounded_verts) else 1
        indices.append((0, i1, i2))

    return rounded_verts, indices


def get_bounding_box(verts):
    """Calculates the bounding box coordinates from a list of vertices"""

    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)

    return min_x, min_y, max_x, max_y
