if "bpy" in locals():
    import importlib
    # importlib.reload(rose)
else:
    from .rose.him import *
    from .rose.til import *
    from .rose.zon import *

import glob
import os
from pathlib import Path
from types import SimpleNamespace 

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

class ImportMap(bpy.types.Operator, ImportHelper):
    bl_idname = "import_map.zon"
    bl_label = "Import ROSE map (.zon)"
    bl_options = {"PRESET"}
    
    filename_ext = ".zon"
    filter_glob = StringProperty(default="*.zon", options={"HIDDEN"})

    def execute(self, context):
        him_ext = ".HIM"
        til_ext = ".TIL"
        ifo_ext = ".IFO"

        # Incase user is on case-sensitive platform and is using lowercase ext
        if self.filepath.endswith(".zon"):
            him_ext = ".him"
            til_ext = ".til"
            ifo_ext = ".ifo"    

        zon = Zon(self.filepath)
        zon_dir = os.path.dirname(self.filepath)
        
        chunks = SimpleNamespace()
        chunks.min_pos = Vector2(999, 999)
        chunks.max_pos = Vector2(-1, -1)
        chunks.area = Vector2(0, 0)
        chunks.coords = []

        for file in os.listdir(zon_dir):
            # Use HIM files to build chunks data
            if file.endswith(him_ext):
                # Extract coordinate of chunks system from file name
                x,y = map(int, file.split(".")[0].split("_"))
                
                # Get min/max pos of tile system
                chunks.min_pos.x = min(x, chunks.min_pos.x)
                chunks.min_pos.y = min(y, chunks.min_pos.y)
                chunks.max_pos.x = max(x, chunks.max_pos.x)
                chunks.max_pos.y = max(y, chunks.max_pos.y)
                
                chunks.coords.append((x, y))
        
        chunks.area.x = chunks.max_pos.x - chunks.min_pos.x + 1
        chunks.area.y = chunks.max_pos.y - chunks.min_pos.y + 1
        
        chunks.vertices = list_2d(chunks.area.x, chunks.area.y)
        chunks.indices = list_2d(chunks.area.x, chunks.area.y)
        chunks.offsets = list_2d(chunks.area.x, chunks.area.y)
        chunks.hims = list_2d(chunks.area.x, chunks.area.y)
        chunks.tils = list_2d(chunks.area.x, chunks.area.y)
        chunks.ifos = list_2d(chunks.area.x, chunks.area.y)

        for x, y in chunks.coords:
            tile_name = "{}_{}".format(x,y)
            him_file = os.path.join(zon_dir, tile_name + him_ext)
            til_file = os.path.join(zon_dir, tile_name + til_ext)
            ifo_file = os.path.join(zon_dir, tile_name + ifo_ext)
            
            him = Him(him_file)
            til = Til(til_file)
            # ifo = Ifo(ifo_file)

            # Calculate relative offset for this tile
            norm_x = x - chunks.min_pos.x
            norm_y = y - chunks.min_pos.y
            
            chunks.vertices[norm_y][norm_x] = list_2d(him.width, him.length)
            chunks.indices[norm_y][norm_x] = list_2d(him.width, him.length)
            chunks.hims[norm_y][norm_x] = him
            chunks.tils[norm_y][norm_x] = til
            # chunks.ifos[norm_y][norm_x] = ifo

        # Calculate tile offsets
        length, cur_length = 0, 0
        for y in range(chunks.area.y):
            width = 0
            for x in range(chunks.area.x):
                him = chunks.hims[y][x]

                offset = Vector2(width, length)
                chunks.offsets[y][x] = offset

                width += him.width -1
                cur_length = him.length - 1

            length += cur_length
        
        terrain_obj = bpy.data.objects.new("terrain", None)
        terrain_obj.hide_select = True
        bpy.context.scene.objects.link(terrain_obj)
           
        # Generate mesh data (vertices/edges/faces) for each chunk
        for y in range(chunks.area.y):
            for x in range(chunks.area.x):
                him = chunks.hims[y][x]

                # Make patches
                p_count = Vector2()
                p_count.x = int((him.width - 1) / him.grid_count)
                p_count.y = int((him.length - 1 ) / him.grid_count)

                p_size = Vector2()
                p_size.x = int((him.width - 1) / p_count.x)
                p_size.y = int((him.length - 1) / p_count.y)
                
                p_offset = Vector2() 
                p_offset.x = chunks.offsets[y][x].x
                p_offset.y = chunks.offsets[y][x].y
                
                # Generate mesh data for each patch in chunk
                for py in range(0, him.length - p_size.y, p_size.y):
                    for px in range(0, him.width - p_size.x, p_size.x):
                        p_verts = []
                        p_edges = []
                        p_faces = []
                        
                        for viy in range(p_size.y + 1):
                            for vix in range(p_size.x + 1):
                                vx = vix + px
                                vy = viy + py
                                vz = him.heights[py+viy][px+vix] / him.size
                                p_verts.append((vix, viy, vz))

                                vi = len(p_verts) - 1
                                if vix < p_size.x and viy < p_size.y:
                                    v1 = vi
                                    v2 = vi + 1
                                    v3 = vi + 1 + p_size.x + 1
                                    v4 = vi + p_size.x + 1
                                    p_edges += ((v1,v2),(v2,v3))
                                    p_edges += ((v3,v4),(v4,v1))
                                    p_faces.append((v1,v2,v3,v4))
                        
                        p_mesh_name = "tmesh_{}_{}".format(px, py)
                        p_obj_name = "terr_{}_{}".format(px,py)

                        p_mesh = bpy.data.meshes.new(p_mesh_name)
                        p_mesh.from_pydata(p_verts, p_edges, p_faces)

                        p_object = bpy.data.objects.new(p_obj_name, p_mesh)
                        p_object.hide_select = True
                        p_object.location = (px+p_offset.x, py+p_offset.y, 0.0)
                        p_object.parent = terrain_obj

                        bpy.context.scene.objects.link(p_object)

        # Create our material
        # terrain_mat = bpy.data.materials.data.new("terrain")

        return {"FINISHED"}

