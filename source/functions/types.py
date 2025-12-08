import bpy
import mathutils
from mathutils import Vector, Matrix


#### ------------------------------ CLASSES ------------------------------ ####

class Ray:
    """Class object for storing raycast results."""

    def __init__(self,
                 hit: bool,
                 location: Vector,
                 normal: Vector,
                 index: int,
                 obj,
                 matrix: Matrix):
        self.hit = hit
        self.location = location if location is not None else mathutils.Vector()
        self.normal = normal if normal is not None else mathutils.Vector()
        self.index = index
        self.obj = obj
        self.matrix = matrix if matrix is not None else mathutils.Matrix()
