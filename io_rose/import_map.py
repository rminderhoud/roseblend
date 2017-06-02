if "bpy" in locals():
    import importlib
    # importlib.reload(rose)
else:
    from .rose.him import *
    from .rose.zon import *

import glob
import os

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper


class ImportMap(bpy.types.Operator, ImportHelper):
    bl_idname = "import_map.zon"
    bl_label = "Import ROSE map (.zon)"
    bl_options = {"PRESET"}
    
    filename_ext = ".zon"
    filter_glob = StringProperty(default="*.zon", options={"HIDDEN"})

    def execute(self, context):
        zon = Zon()
        zon.load(self.filepath)

        zon_dir = os.path.dirname(self.filepath)
        
        him_tiles = []
        him_min_x = 999
        him_min_y = 999
        him_max_x = -1
        him_max_y = -1
        
        him_coords = []
        
        i=0
        for file in os.listdir(zon_dir):
            for him_ext in [".him", ".HIM"]:
                if file.endswith(him_ext):
                    # Extract coordinate of HIM tile from filename
                    x,y = map(int, file.split(".")[0].split("_"))
                    
                    # Get lowest x,y pair from filenames
                    him_min_x = min(x, him_min_x)
                    him_min_y = min(y, him_min_y)
                    him_max_x = max(x, him_max_x)
                    him_max_y = max(y, him_max_y)
                    
                    him_file = os.path.join(zon_dir, file)
                    him_coords.append((him_file, x, y))

        him_x_count = him_max_x - him_min_x + 1
        him_y_count = him_max_y - him_min_y + 1
    
        # Allocate space for our lists
        him_tiles = list_2d(him_x_count, him_y_count)
        
        # Sort our him files into 2d array
        for file, x, y in him_coords:
            # Calculate relative offset for this tile
            normalized_x = x - him_min_x
            normalized_y = y - him_min_y
            
            him = Him()
            him.load(file)
            
            him_tiles[normalized_y][normalized_x] = him
        
        # Create our object and mesh
        bpy.ops.object.add(type='MESH')
        terrain_obj = bpy.context.object
        terrain_mesh = terrain_obj.data
        
        vertices = []
        offset_x, offset_y = 0, 0

        # Generate our vertices taking into account offsets
        for y in range(him_y_count):
            cur_length = 0
            for x in range(him_x_count):
                him = him_tiles[y][x]

                for vy in range(him.length):
                    for vx in range(him.width):
                        vz = him.heights[vy][vx] / him.patch_scale
                        vertices.append((vx+offset_x,vy+offset_y,vz))
                
                offset_x += him.width
                cur_length = him.length

            offset_x = 0
            offset_y += him.length

        terrain_mesh.from_pydata(vertices, [], [])
        terrain_mesh.update()

        return {"FINISHED"}

