from pathlib import Path

if "bpy" in locals():
    import importlib
else:
    from .rose.zms import *

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


class ImportZMS(bpy.types.Operator, ImportHelper):
    bl_idname = "rose.import_zms"
    bl_label = "ROSE Mesh (.zms)"
    bl_options = {"PRESET"}

    filename_ext = ".zms"
    filter_glob = StringProperty(default="*.zms", options={"HIDDEN"})
    load_texture = BoolProperty(
        name = "Load texture",
        description = ( "Automatically detect and load a texture if "
                        "one can be found (uses file name)"),
        default=True,
    )

    def execute(self, context):
        filepath = Path(self.filepath)
        name = filepath.stem
        zms = ZMS(self.filepath) 

        mesh = self.mesh_from_zms(zms, name)

        obj = bpy.data.objects.new(name, mesh)
        
        scene = context.scene
        scene.objects.link(obj)
        scene.update()

        return {"FINISHED"}

    def mesh_from_zms(self, zms, name):
        mesh = bpy.data.meshes.new(name)
        
        verts = []
        for v in zms.vertices:
            verts.append((v.position.x, v.position.y, v.position.z))
        
        faces = []
        for i in zms.indices:
            faces.append((i.x, i.y, i.z))
        
        mesh.from_pydata(verts, [], faces)
        
        uvs = []
        if zms.uv1_enabled():
            mesh.uv_textures.new(name="uv1")
            uvs.append("uv1")
        if zms.uv2_enabled():
            mesh.uv_textures.new(name="uv2")
            uvs.append("uv2")
        if zms.uv3_enabled():
            mesh.uv_textures.new(name="uv3")
            uvs.append("uv3")
        if zms.uv4_enabled():
            mesh.uv_textures.new(name="uv4")
            uvs.append("uv4")

        # DO THE NEEDFUL
        for uv in uvs:
            pass

        mesh.update(calc_edges=True)
        return mesh
