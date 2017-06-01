bl_info = {
    "name": "ROSE Online blender plugin",
    "author": "Ralph Minderhoud",
    "blender": (2, 77, 0),
    "location": "File > Import",
    "description": "Import files from ROSE Online",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(import_map)
else:
    from .import_map import ImportMap

import bpy

def menu(self, context):
    self.layout.separator()
    self.layout.operator(ImportMap.bl_idname, text="ROSE Map (.zon)")

def register():
    bpy.utils.register_class(ImportMap)
    bpy.types.INFO_MT_file_import.append(menu)

def unregister():
    blp.utils.unregister_class(ImportMap)
    bpy.types.INFO_MT_file_import.remove(menu)


if __name__ == "__main__":
    register()
