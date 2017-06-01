import math
from .utils import *

class Patch:
    def __init__(self):
        minimum = 0
        maximum = 0

class Him:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.grid_count = 0
        self.grid_size = 0.0

        # Two dimensional array for height data
        self.heights = []
        self.max_height = 0.0
        self.min_height = 0.0
        
        self.patches = []
        self.quad_patches = []

    def load(self, path):
        with open(path, 'rb') as f:
            self.width = read_i32(f)
            self.height = read_i32(f)
            self.grid_count = read_i32(f)
            self.grid_size = read_f32(f)

            for x in range(self.width):
                row = []
                for y in range(self.height):
                    h = read_f32(f)

                    if h > self.max_height: self.max_height = h
                    if h < self.min_height: self.min_height = h
                    
                    row.append(h)

                self.heights.append(row)
            
            name = read_bstr(f)
            patch_count = read_i32(f)
            patch_sqrt = int(math.sqrt(patch_count))

            for h in range(patch_sqrt):
                row = []
                for w in range(patch_sqrt):
                    p = Patch()
                    p.maximum = read_f32(f)
                    p.minimum = read_f32(f)

                    row.append(p)

                self.patches.append(row)
            
            quad_count = read_i32(f)
            for i in range(quad_count):
                p = Patch()
                p.maximum = read_f32(f)
                p.minimum = read_f32(f)

                self.quad_patches.append(p)
