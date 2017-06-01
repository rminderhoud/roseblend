if "bpy" in locals():
    import importlib
    importlib.reload(rose)
else:
    from . import rose

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
        zon = rose.zon.Zon()
        z.load(self.filepath)

        # Find all HIM files in same directory
        # Find all TIL files in same directory

        return {"FINISHED"}

