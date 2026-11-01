import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.assets import ASSET_CATEGORY_PRODUCT
from bvt.assets import asset_record
from bvt.assets import iter_registered_assets
from bvt.assets import register_asset


bvt.register()


scene = bpy.context.scene

cube = bpy.data.objects.get(
    "Cube"
)

assert cube is not None


material = bpy.data.materials.new(
    "BVT_Asset_Smoke_Material"
)

# Factory startup may contain an existing material slot.
# The smoke fixture must own its material state explicitly.
cube.data.materials.clear()

cube.data.materials.append(
    material
)


register_asset(
    cube,
    asset_id="asset_smoke_cube",
    category=ASSET_CATEGORY_PRODUCT,
    manufacturer="BVT Synthetic",
    tags=(
        "Retail",
        "Smoke",
        "Cube",
        "retail",
    ),
    license_name="BVT Synthetic Demo",
    author="BVT",
    version="0.1.0",
)


settings = cube.bvt_asset


assert settings.registered is True

assert (
    settings.asset_id
    == "asset_smoke_cube"
)

assert (
    settings.category
    == ASSET_CATEGORY_PRODUCT
)

assert (
    settings.tags
    == "retail,smoke,cube"
)


assets = iter_registered_assets(
    scene
)


assert assets == (
    cube,
)


record = asset_record(
    cube
)


assert (
    record[
        "asset_id"
    ]
    == "asset_smoke_cube"
)

assert (
    record[
        "category"
    ]
    == "PRODUCT"
)

assert (
    record[
        "tags"
    ]
    == [
        "retail",
        "smoke",
        "cube",
    ]
)

assert (
    record[
        "materials"
    ]
    == [
        "BVT_Asset_Smoke_Material"
    ]
)

assert len(
    record[
        "dimensions"
    ]
) == 3

assert all(
    float(value)
    > 0.0
    for value
    in record[
        "dimensions"
    ]
)

assert (
    record[
        "license"
    ]
    == "BVT Synthetic Demo"
)

assert (
    record[
        "author"
    ]
    == "BVT"
)

assert (
    record[
        "version"
    ]
    == "0.1.0"
)


print(
    "registered_assets=1"
)

print(
    "asset_id=asset_smoke_cube"
)

print(
    "asset_category=PRODUCT"
)

print(
    "asset_tags=retail,smoke,cube"
)

print(
    "asset_dimensions=True"
)

print(
    "asset_materials=True"
)

print(
    "BVT_ASSET_REGISTRATION_SMOKE=OK"
)

print(
    "RESULT=PASS"
)
