import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
TMP = ROOT / ".tmp"

BLEND_PATH = TMP / "yolo-annotation.blend"

sys.path.insert(
    0,
    str(SOURCE),
)


import bpy
import bvt

from bvt.annotation.service import register_object
from bvt.project.service import initialize_project
from bvt.render.service import generate_minimal_dataset


if TMP.exists():
    shutil.rmtree(TMP)

TMP.mkdir(
    parents=True,
    exist_ok=True,
)


bvt.register()

scene = bpy.context.scene


bpy.ops.wm.save_as_mainfile(
    filepath=str(BLEND_PATH),
)


project = scene.bvt_project

project.project_name = (
    "YOLO Annotation Smoke"
)

project.output_directory = (
    "//bvt_output/"
)

project.seed = 12345

initialize_project(
    scene,
)


cube = bpy.data.objects.get(
    "Cube",
)

assert cube is not None


cube_settings = cube.bvt_object

cube_settings.class_id = 0
cube_settings.class_name = "cube"

register_object(
    cube,
)


assert cube_settings.registered is True
assert cube_settings.instance_id
assert cube_settings.class_id == 0
assert cube_settings.class_name == "cube"


result = generate_minimal_dataset(
    scene,
)


image_path = result["image_path"]
label_path = result["label_path"]
classes_path = result["classes_path"]
manifest_path = result["manifest_path"]


assert image_path.exists()
assert label_path.exists()
assert classes_path.exists()
assert manifest_path.exists()


label = label_path.read_text(
    encoding="utf-8",
).strip()


parts = label.split()

assert len(parts) == 5
assert parts[0] == "0"


x_center = float(parts[1])
y_center = float(parts[2])
width = float(parts[3])
height = float(parts[4])


assert 0.0 <= x_center <= 1.0
assert 0.0 <= y_center <= 1.0

assert 0.0 < width <= 1.0
assert 0.0 < height <= 1.0


classes = classes_path.read_text(
    encoding="utf-8",
).strip()

assert classes == "cube"


manifest = json.loads(
    manifest_path.read_text(
        encoding="utf-8",
    )
)


assert (
    manifest["annotations"]["format"]
    == "yolo"
)

assert (
    manifest["annotations"]["classes_file"]
    == "classes.txt"
)

assert (
    manifest["annotations"]["classes"][0]["id"]
    == 0
)

assert (
    manifest["annotations"]["classes"][0]["name"]
    == "cube"
)


frame = manifest["frames"][0]

assert frame["label"] == "labels/000001.txt"
assert len(frame["objects"]) == 1


obj = frame["objects"][0]

assert obj["instance_id"] == cube_settings.instance_id
assert obj["object_name"] == "Cube"
assert obj["class_id"] == 0
assert obj["class_name"] == "cube"

assert len(obj["bbox_yolo"]) == 4


print("BVT_YOLO_ANNOTATION_SMOKE=OK")

print(
    "label=",
    label,
)

print(
    "classes=",
    classes,
)

print(
    "instance_id=",
    cube_settings.instance_id,
)

print(
    "manifest=",
    manifest_path,
)


bvt.unregister()

shutil.rmtree(
    TMP,
)

print(
    "BVT_YOLO_ANNOTATION_CLEANUP=OK"
)
