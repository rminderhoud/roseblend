from pathlib import Path

if "bpy" in locals():
    import importlib
else:
    from .rose.zmd import *

import bpy
import mathutils as bmath
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


class ImportZMD(bpy.types.Operator, ImportHelper):
    bl_idname = "rose.import_zmd"
    bl_label = "ROSE Armature (.zmd)"
    bl_options = {"PRESET"}

    filename_ext = ".zmd"
    filter_glob = StringProperty(default="*.zmd", options={"HIDDEN"})

    find_animations = BoolProperty(
        name = "Find Animations",
        description = ( "Load any animations (ZMOs) from current "
                        "or child directories with the armature"),
        default=True,
    )

    animation_extensions = [".ZMO", ".zmo"]

    def execute(self, context):
        filepath = Path(self.filepath)
        filename = filepath.stem
        zmd = ZMD(str(filepath))

        armature = bpy.data.armatures.new(filename)
        obj = bpy.data.objects.new(filename, armature)

        scene = context.scene
        scene.objects.link(obj)
        scene.objects.active = obj

        # Armature has to exist in scene to add bones
        self.bones_from_zmd(zmd, armature)
 
        scene.update()
        return {"FINISHED"}

    def bones_from_zmd(self, zmd, armature):
        bpy.ops.object.mode_set(mode='EDIT')

        # Set all heads
        for rose_bone in zmd.bones:
            bone = armature.edit_bones.new(rose_bone.name)
            bone.use_connect = True

        for idx, rose_bone in enumerate(zmd.bones):
            bone = armature.edit_bones[idx]

            pos = bmath.Vector(rose_bone.position.as_tuple())
            rot = bmath.Quaternion(rose_bone.rotation.as_tuple(w_first=True))

            if rose_bone.parent_id >= 0:
                parent = armature.edit_bones[rose_bone.parent_id]
                parent.tail = pos
                parent.transform(rot.to_matrix())
                bone.parent = parent
            else:
                #bone.head = rose_bone.position.as_tuple()
                bone.head = pos
                # bone.tail = zmd.bones[rose_bone.parent_id].position.as_tuple()
            # Set rotation??
            # Rose bone.position = Head position?
            # How does rotation factor in?

        bpy.ops.object.mode_set(mode='OBJECT')

        return armature
