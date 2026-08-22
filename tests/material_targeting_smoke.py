import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

TMP = (
    ROOT
    / ".tmp"
)

BLEND_PATH = (
    TMP
    / "material-targeting.blend"
)


sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.materials import get_materials_by_role
from bvt.materials import iter_scene_materials
from bvt.materials import MATERIAL_ROLE_GENERIC
from bvt.materials import MATERIAL_ROLE_GLASS
from bvt.materials import set_material_role


if TMP.exists():
    shutil.rmtree(
        TMP
    )

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene

cube = bpy.data.objects[
    "Cube"
]


generic_material = (
    bpy.data.materials.new(
        "BVT_Generic"
    )
)

glass_material = (
    bpy.data.materials.new(
        "BVT_Glass"
    )
)

unused_glass_material = (
    bpy.data.materials.new(
        "BVT_Unused_Glass"
    )
)

# Keep this intentionally unassigned material
# inside the .blend file across save/reload.
unused_glass_material.use_fake_user = True


cube.data.materials.clear()

cube.data.materials.append(
    generic_material
)

cube.data.materials.append(
    glass_material
)


set_material_role(
    generic_material,
    MATERIAL_ROLE_GENERIC,
)

set_material_role(
    glass_material,
    MATERIAL_ROLE_GLASS,
)

set_material_role(
    unused_glass_material,
    MATERIAL_ROLE_GLASS,
)


scene_material_names = tuple(
    material.name
    for material
    in iter_scene_materials(
        scene
    )
)

assert scene_material_names == (
    "BVT_Generic",
    "BVT_Glass",
)


glass_materials = (
    get_materials_by_role(
        scene,
        MATERIAL_ROLE_GLASS,
    )
)

assert tuple(
    material.name
    for material
    in glass_materials
) == (
    "BVT_Glass",
)


generic_materials = (
    get_materials_by_role(
        scene,
        MATERIAL_ROLE_GENERIC,
    )
)

assert tuple(
    material.name
    for material
    in generic_materials
) == (
    "BVT_Generic",
)


assert (
    unused_glass_material
    not in glass_materials
)


try:
    set_material_role(
        generic_material,
        "INVALID",
    )

except ValueError:
    pass

else:
    raise AssertionError(
        "Invalid material role was accepted"
    )


bpy.ops.wm.save_as_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


bpy.ops.wm.open_mainfile(
    filepath=str(
        BLEND_PATH
    )
)


scene = bpy.context.scene

reloaded_glass = (
    bpy.data.materials[
        "BVT_Glass"
    ]
)

reloaded_generic = (
    bpy.data.materials[
        "BVT_Generic"
    ]
)

reloaded_unused = (
    bpy.data.materials[
        "BVT_Unused_Glass"
    ]
)


assert (
    reloaded_glass.bvt_material.role
    == MATERIAL_ROLE_GLASS
)

assert (
    reloaded_generic.bvt_material.role
    == MATERIAL_ROLE_GENERIC
)

assert (
    reloaded_unused.bvt_material.role
    == MATERIAL_ROLE_GLASS
)


reloaded_glass_materials = (
    get_materials_by_role(
        scene,
        MATERIAL_ROLE_GLASS,
    )
)


assert tuple(
    material.name
    for material
    in reloaded_glass_materials
) == (
    "BVT_Glass",
)


assert (
    reloaded_unused
    not in reloaded_glass_materials
)


print(
    "BVT_MATERIAL_TARGETING_SMOKE=OK"
)

print(
    "scene_materials=",
    tuple(
        material.name
        for material
        in iter_scene_materials(
            scene
        )
    ),
)

print(
    "glass_materials=",
    tuple(
        material.name
        for material
        in reloaded_glass_materials
    ),
)

print(
    "glass_role=",
    reloaded_glass.bvt_material.role,
)

print(
    "generic_role=",
    reloaded_generic.bvt_material.role,
)

print(
    "unused_glass_excluded=True"
)

print(
    "persistence=OK"
)


bvt.unregister()

shutil.rmtree(
    TMP
)


print(
    "BVT_MATERIAL_TARGETING_CLEANUP=OK"
)
