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
        for file, x, y in him_coords:
            # Calculate relative offset for this tile
            normalized_x = x - him_min_x
            normalized_y = y - him_min_y
            
            him = Him()
            him.load(file)
            
            # Stores vertex indices
            him.indices = list_2d(him.width, him.length)

            him_tiles[normalized_y][normalized_x] = him
        
        # Store our tile offsets
        him_offsets = list_2d(him_x_count, him_y_count)
        length, cur_length = 0, 0
        for y in range(him_y_count):
            width = 0
            for x in range(him_x_count):
                him = him_tiles[y][x]

                offset = Vector2()
                offset.x = width
                offset.y = length
                him_offsets[y][x] = offset

                width += him.width
                cur_length = him.length

            length += cur_length
        
        # Create our object and mesh
        bpy.ops.object.add(type='MESH')
        terrain_obj = bpy.context.object
        terrain_mesh = terrain_obj.data
        
        vertices = []
        edges = []
        faces = []
        
        # Generate mesh data (vertices/edges/faces) for each HIM tile (counter-clockwise)
        for y in range(him_y_count):
            for x in range(him_x_count):
                him = him_tiles[y][x]

                offset_x = him_offsets[y][x].x
                offset_y = him_offsets[y][x].y
                
                for vy in range(him.length):
                    for vx in range(him.width):
                        # Create vertices
                        vz = him.heights[vy][vx] / him.patch_scale
                        vertices.append((vx+offset_x,vy+offset_y,vz))
                        
                        vi = len(vertices) - 1
                        him.indices[vy][vx] = vi

                        if vx < him.width -1 and vy < him.length - 1:
                            v1 = vi
                            v2 = vi + 1
                            v3 = vi + 1 + him.width
                            v4 = vi + him.width
                            edges += ((v1,v2), (v2,v3), (v3,v4), (v4,v1))
                            faces.append((v1,v2,v3,v4))
        
        # Generate edges/faces inbetween each HIM tile (counter-clockwise)
        for y in range(him_y_count):
            for x in range(him_x_count):
                him = him_tiles[y][x]
                
                is_x_edge = (x == him_x_count - 1)
                is_y_edge = (y == him_y_count - 1)

                for vy in range(him.length):
                    for vx in range(him.width):
                        is_x_edge_vertex = (vx == him.width - 1) and (vy < him.length - 1)
                        is_y_edge_vertex = (vx < him.width - 1) and (vy == him.length - 1)
                        is_corner_vertex = (vx == him.width - 1) and (vy == him.length - 1)

                        if not is_x_edge:
                            if is_x_edge_vertex:
                                next_him = him_tiles[y][x+1]
                                v1 = him.indices[vy][vx]
                                v2 = him.indices[vy+1][vx]
                                v3 = next_him.indices[vy+1][0]
                                v4 = next_him.indices[vy][0]
                                edges += ((v1,v2), (v2,v3), (v3,v4), (v4,v1))
                                faces.append((v1,v2,v3,v4))
                        
                        if not is_y_edge:
                            if is_y_edge_vertex:
                                next_him = him_tiles[y+1][x]
                                v1 = him.indices[vy][vx]
                                v2 = him.indices[vy][vx+1]
                                v3 = next_him.indices[0][vx+1]
                                v4 = next_him.indices[0][vx]
                                edges += ((v1,v2), (v2,v3), (v3,v4), (v4,v1))
                                faces.append((v1,v2,v3,v4))

                        if not is_x_edge and not is_y_edge:
                            if is_corner_vertex:
                                right_him = him_tiles[y][x+1]
                                diag_him = him_tiles[y+1][x+1]
                                down_him = him_tiles[y+1][x]

                                v1 = him.indices[vy][vx]
                                v2 = down_him.indices[0][down_him.width-1]
                                v3 = diag_him.indices[0][0]
                                v4 = right_him.indices[diag_him.length-1][0]
                                edges += ((v1,v2), (v2,v3), (v3,v4), (v4,v1))
                                faces.append((v1,v2,v3,v4))
                            
        
        terrain_mesh.from_pydata(vertices, edges, faces)
        terrain_mesh.update()

        return {"FINISHED"}

