from math import log10, atan2, cos, sin
from ase.build import hcp0001, fcc111, bcc111
import numpy as np


def hcp0001_root(symbol, root, size, a=None, c=None,
                 vacuum=None, orthogonal=False):
    """HCP(0001) surface maniupulated to have a x unit side length
    of *root* before repeating.  This also results in *root* number
    of repetitions of the cell.


    The first 20 valid roots for nonorthogonal are...
    1, 3, 4, 7, 9, 12, 13, 16, 19, 21, 25,
    27, 28, 31, 36, 37, 39, 43, 48, 49"""
    atoms = hcp0001(symbol=symbol, size=(1, 1, size[2]),
                    a=a, c=c, vacuum=vacuum, orthogonal=orthogonal)
    atoms = root_surface(atoms, root)
    atoms *= (size[0], size[1], 1)
    return atoms


def fcc111_root(symbol, root, size, a=None,
                vacuum=None, orthogonal=False):
    """FCC(111) surface maniupulated to have a x unit side length
    of *root* before repeating. This also results in *root* number
    of repetitions of the cell.

    The first 20 valid roots for nonorthogonal are...
    1, 3, 4, 7, 9, 12, 13, 16, 19, 21, 25, 27,
    28, 31, 36, 37, 39, 43, 48, 49"""
    atoms = fcc111(symbol=symbol, size=(1, 1, size[2]),
                   a=a, vacuum=vacuum, orthogonal=orthogonal)
    atoms = root_surface(atoms, root)
    atoms *= (size[0], size[1], 1)
    return atoms


def bcc111_root(symbol, root, size, a=None,
                vacuum=None, orthogonal=False):
    """BCC(111) surface maniupulated to have a x unit side length
    of *root* before repeating. This also results in *root* number
    of repetitions of the cell.


    The first 20 valid roots for nonorthogonal are...
    1, 3, 4, 7, 9, 12, 13, 16, 19, 21, 25,
    27, 28, 31, 36, 37, 39, 43, 48, 49"""
    atoms = bcc111(symbol=symbol, size=(1, 1, size[2]),
                   a=a, vacuum=vacuum, orthogonal=orthogonal)
    atoms = root_surface(atoms, root)
    atoms *= (size[0], size[1], 1)
    return atoms


def point_in_cell_2d(point, cell, eps=1e-8):
    def tri_area(t1, t2, t3):
        t1x, t1y = t1[0:2]
        t2x, t2y = t2[0:2]
        t3x, t3y = t3[0:2]
        return abs(t1x*(t2y-t3y) + t2x*(t3y-t1y) + t3x*(t1y-t2y))/2

    c0 = (0, 0)
    c1 = (cell[0][0:2])
    c2 = (cell[1][0:2])
    c3 = c1 + c2

    cA = tri_area(c0, c1, c2) + tri_area(c1, c2, c3)

    pA = tri_area(point, c0, c1) + tri_area(point, c1, c2) + tri_area(point, c2, c3) + tri_area(point, c3, c0)

    return pA <= cA + eps


def root_surface_analysis(primitive_slab, root, root_point=False, eps=1e-8):
    """A tool to analyze a slab and look for valid roots that exist, up to
       the given root. This is useful for generating all possible cells
       without prior knowledge.

       *primitive slab* is the primitive cell to analyze.

       *root* is the desired root to find, and all below.

       *root_point* returns the cell_points and the index of the root

       """

    # Setup parameters for cell searching
    logeps = int(-log10(eps))

    xscale = np.linalg.norm(primitive_slab.cell[0][0:2])
    xx, xy = primitive_slab.cell[0][0:2] / xscale
    yx, yy = primitive_slab.cell[1][0:2] / xscale
    cell_vectors = np.array([[xx, xy], [yx, yy]])

    # Allocate grid for cell search search
    points = np.indices((root+1, root+1)).T.reshape(-1, 2)

    # Find points corresponding to full cells
    cell_points = [cell_vectors[0] * x + cell_vectors[1] * y for x, y in points]

    # Find point close to the desired cell (floating point error possible)
    roots = np.around(np.linalg.norm(cell_points, axis=1)**2, logeps)

    if root_point:
        valid_roots = np.nonzero(roots == root)[0]
        if len(valid_roots) == 0:
            raise ValueError("Invalid root {} for cell {}".format(root, cell_vectors))
        return cell_points, cell_points[np.nonzero(roots == root)[0][0]]
    else:
        roots = np.array([int(this_root) for this_root in roots
                          if this_root.is_integer() and this_root <= root])
        return set(roots[1:])


def root_surface(primitive_slab, root, eps=1e-8):
    """Creates a cell from a primitive cell that repeats along the x and y
    axis in a way consisent with the primitive cell, that has been cut
    to have a side length of *root*.

    *primitive cell* should be a primitive 2d cell of your slab, repeated
    as needed in the z direction.

    *root* should be determined using an analysis tool such as the
    root_surface_analysis function, or prior knowledge. It should always
    be a whole number as it represents the number of repetitions."""

    atoms = primitive_slab.copy()

    xscale = np.linalg.norm(primitive_slab.cell[0][0:2])
    xx, xy = primitive_slab.cell[0][0:2] / xscale
    yx, yy = primitive_slab.cell[1][0:2] / xscale
    cell_vectors = np.array([[xx, xy], [yx, yy]])

    # Do root surface analysis
    cell_points, root_point = root_surface_analysis(primitive_slab, root, root_point=True, eps=eps)

    # Find new cell
    root_angle = -atan2(root_point[1], root_point[0])
    root_rotation = [[cos(root_angle), -sin(root_angle)],
                     [sin(root_angle), cos(root_angle)]]
    root_scale = np.linalg.norm(root_point)

    cell = np.array([np.dot(x, root_rotation) * root_scale for x in cell_vectors])

    # Find all cell centers within the cell
    shift = cell_vectors.sum(axis=0)/2
    cell_points = [point for point in cell_points if point_in_cell_2d(point+shift, cell, eps=eps)]

    # Setup new cell
    atoms.rotate(root_angle, v="z")
    atoms *= (root, root, 1)
    atoms.cell[0:2, 0:2] = cell * xscale
    atoms.center()

    # Remove all extra atoms
    del atoms[[atom.index for atom in atoms if not point_in_cell_2d(atom.position, atoms.cell, eps=eps)]]

    # Rotate cell back to original orientation
    standard_rotation = [[cos(-root_angle), -sin(-root_angle), 0],
                         [sin(-root_angle), cos(-root_angle),  0],
                         [0,                0,                 1]]

    new_cell = np.array([np.dot(x, standard_rotation) for x in atoms.cell])
    new_positions = np.array([np.dot(x, standard_rotation) for x in atoms.positions])

    atoms.cell = new_cell
    atoms.positions = new_positions

    return atoms
                                                                            
