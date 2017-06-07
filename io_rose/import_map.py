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

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

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

        zon = Zon(self.filepath)
        zon_dir = os.path.dirname(self.filepath)
        
        # Ew nasty
        data_dir = Path(self.filepath)
        for i in range(5):
            data_dir = data_dir.parent
        
        textures = []
        for tpath in zon.textures[:-1]:
            name = tpath.split("\\")[-1].split(".")[0].upper()
            p = os.path.join(str(data_dir), from_rose_path(tpath))
            img = bpy.data.images.load(p)
            tex = bpy.data.textures.new(name, type="IMAGE")
            tex.image = img
            textures.append(tex)

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
                til = chunks.tils[y][x]

                c_offset = Vector2() 
                c_offset.x = chunks.offsets[y][x].x
                c_offset.y = chunks.offsets[y][x].y

                # Make patches
                p_count = Vector2()
                p_count.x = int((him.width - 1) / him.grid_count)
                p_count.y = int((him.length - 1 ) / him.grid_count)

                p_size = Vector2()
                p_size.x = int((him.width - 1) / p_count.x)
                p_size.y = int((him.length - 1) / p_count.y)
                
                
                # Generate mesh data for each patch in chunk
                for py in range(0, him.length - p_size.y, p_size.y):
                    for px in range(0, him.width - p_size.x, p_size.x):
                        p_verts = []
                        p_edges = []
                        p_faces = []
                        p_uv = []

                        # Vertices/edges/faces
                        for viy in range(p_size.y + 1):
                            for vix in range(p_size.x + 1):
                                vx = vix + px
                                vy = viy + py
                                vz = him.heights[py+viy][px+vix] / him.size
                                p_verts.append((vix, viy, vz))
                                
                                uv = Vector2(vix * (1 / p_size.x), viy * (1 / p_size.y))
                                # TODO: UV rotation (multiply by rotation matrix)
                                p_uv.append(uv)

                                vi = len(p_verts) - 1
                                if vix < p_size.x and viy < p_size.y:
                                    v1 = vi
                                    v2 = vi + 1
                                    v3 = vi + 1 + p_size.x + 1
                                    v4 = vi + p_size.x + 1
                                    p_edges += ((v1,v2),(v2,v3))
                                    p_edges += ((v3,v4),(v4,v1))
                                    p_faces.append((v1,v2,v3,v4))
                        
                        p_offset = Vector2(px+c_offset.x, py+c_offset.y)
                        norm_px = int(px * (1 / p_size.x))
                        norm_py = int(py * (1 / p_size.y))
                        p_tile = til.tiles[norm_py][norm_px]
                        p_zon_tile = zon.tiles[p_tile.tile]

                        p_mesh_name = "tmesh_{}_{}_{}_{}".format(x, y, px, py)
                        p_uv_name = "tuv_{}_{}_{}_{}".format(x, y, px, py)
                        p_mat_name = "tmat_{}_{}_{}_{}".format(x, y, px, py)
                        p_obj_name = "terr_{}_{}_{}_{}".format(x, y, px, py)
                        
                        # -- Mesh
                        p_mesh = bpy.data.meshes.new(p_mesh_name)
                        p_mesh.from_pydata(p_verts, p_edges, p_faces)
                        p_mesh.validate()

                        # -- UV
                        p_mesh.uv_textures.new(p_uv_name)
                        
                        uv_orient = Vector2(1,1)
                        if p_zon_tile.rotation == 1:
                            uv_orient = Vector2(1,1)
                        elif p_zon_tile.rotation == 2:
                            uv_orient = Vector2(-1,1)
                        elif p_zon_tile.rotation == 3:
                            uv_orient = Vector2(1,-1)
                        elif p_zon_tile.rotation == 4:
                            uv_orient = Vector2(-1,-1)

                        uv = []
                        for loop in p_mesh.loops:
                            u,v = p_uv[loop.vertex_index].values()
                            
                            if p_zon_tile.rotation == 0:
                                uv += [u,v]
                            elif p_zon_tile.rotation == 1:
                                uv += [1 - u, v]
                            elif p_zon_tile.rotation == 2:
                                uv += [u, 1 - v]
                            elif p_zon_tile.rotation == 3:
                                uv += [v, u]
                            elif p_zon_tile.rotation == 4:
                                uv += [v, 1 - u]


                        p_mesh.uv_layers[0].data.foreach_set("uv", uv)
                        
                        # -- Material
                        # TODO: Create material, attach to mesh, set 3 textures
                        p_mat = bpy.data.materials.new(p_mat_name)

                        tile_id = p_tile.tile
                        zon_tile = zon.tiles[tile_id]

                        top_tex = p_mat.texture_slots.add()
                        top_tex.texture = textures[zon_tile.layer1 + zon_tile.offset1]
                        top_tex.texture_coords = "UV"

                        bot_tex = p_mat.texture_slots.add()
                        bot_tex.texture = textures[zon_tile.layer2 + zon_tile.offset2]
                        bot_tex.texture_coords = "UV"

                        light_tex = p_mat.texture_slots.add()
                        light_tex.texture_coords = "UV"

                        p_mesh.materials.append(p_mat)

                        # -- Object
                        p_object = bpy.data.objects.new(p_obj_name, p_mesh)
                        p_object.hide_select = True
                        p_object.location = (p_offset.x, p_offset.y, 0.0)
                        p_object.parent = terrain_obj

                        bpy.context.scene.objects.link(p_object)

        # Create our material
        # terrain_mat = bpy.data.materials.data.new("terrain")

        return {"FINISHED"}

