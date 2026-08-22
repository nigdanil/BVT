import random

from ..annotation.service import iter_annotated_objects
from ..core.seeding import derive_subseed


PLACEMENT_RANDOMIZER_VERSION = "placement-random-v1"


def capture_placement_baseline(scene):
    baseline = {}

    for obj in iter_annotated_objects(scene):
        settings = obj.bvt_object

        baseline[settings.instance_id] = {
            "object_name": obj.name,
            "location": obj.location.copy(),
        }

    return baseline


def apply_random_placement(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    if not project_settings.placement_randomization_enabled:
        return {
            "enabled": False,
            "version": PLACEMENT_RANDOMIZER_VERSION,
            "space": "local",
            "objects": [],
        }

    objects_result = []

    objects = list(
        iter_annotated_objects(scene)
    )

    objects.sort(
        key=lambda obj: (
            obj.bvt_object.instance_id
        )
    )

    for obj in objects:
        object_settings = obj.bvt_object

        instance_id = (
            object_settings.instance_id
        )

        base = baseline.get(
            instance_id
        )

        if base is None:
            raise ValueError(
                (
                    "Placement baseline missing for "
                    f"{obj.name}"
                )
            )

        object_seed = derive_subseed(
            frame_seed,
            "placement",
            instance_id,
        )

        rng = random.Random(
            object_seed
        )

        sampled_offset_x = rng.uniform(
            -project_settings.placement_offset_x,
            project_settings.placement_offset_x,
        )

        sampled_offset_y = rng.uniform(
            -project_settings.placement_offset_y,
            project_settings.placement_offset_y,
        )

        sampled_offset_z = rng.uniform(
            -project_settings.placement_offset_z,
            project_settings.placement_offset_z,
        )

        base_location = (
            base["location"]
        )

        obj.location.x = (
            base_location.x
            + sampled_offset_x
        )

        obj.location.y = (
            base_location.y
            + sampled_offset_y
        )

        obj.location.z = (
            base_location.z
            + sampled_offset_z
        )

        actual_location = (
            obj.location.copy()
        )

        actual_offset_x = (
            actual_location.x
            - base_location.x
        )

        actual_offset_y = (
            actual_location.y
            - base_location.y
        )

        actual_offset_z = (
            actual_location.z
            - base_location.z
        )

        objects_result.append(
            {
                "instance_id": instance_id,
                "object_name": obj.name,
                "seed": object_seed,
                "base_location": [
                    base_location.x,
                    base_location.y,
                    base_location.z,
                ],
                "offset": [
                    actual_offset_x,
                    actual_offset_y,
                    actual_offset_z,
                ],
                "location": [
                    actual_location.x,
                    actual_location.y,
                    actual_location.z,
                ],
            }
        )

    return {
        "enabled": True,
        "version": PLACEMENT_RANDOMIZER_VERSION,
        "space": "local",
        "ranges": {
            "x": project_settings.placement_offset_x,
            "y": project_settings.placement_offset_y,
            "z": project_settings.placement_offset_z,
        },
        "objects": objects_result,
    }


def restore_placement(
    scene,
    baseline,
):
    for obj in iter_annotated_objects(scene):
        instance_id = (
            obj.bvt_object.instance_id
        )

        base = baseline.get(
            instance_id
        )

        if base is None:
            continue

        obj.location = (
            base["location"]
        )
