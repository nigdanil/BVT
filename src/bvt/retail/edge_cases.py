import math

import bpy

from ..assets import ASSET_CATEGORY_PRODUCT
from ..assets import iter_registered_assets
from ..core.seeding import SUBSEED_STRATEGY
from ..core.seeding import derive_subseed


RETAIL_EDGE_CASES_VERSION = (
    "retail-edge-cases-v0.1"
)

WRONG_ANGLE_NAMESPACE = (
    "retail-edge-case/wrong-angle"
)

WRONG_POSITION_NAMESPACE = (
    "retail-edge-case/wrong-position"
)

EMPTY_SLOT_NAMESPACE = (
    "retail-edge-case/empty-slot"
)

OCCLUSION_NAMESPACE = (
    "retail-edge-case/occlusion"
)


def iter_retail_products(
    scene,
):
    products = []

    for obj in iter_registered_assets(
        scene
    ):
        if (
            obj.bvt_asset.category
            != ASSET_CATEGORY_PRODUCT
        ):
            continue

        if not obj.bvt_object.registered:
            continue

        instance_id = (
            obj.bvt_object.instance_id
            .strip()
        )

        if not instance_id:
            continue

        products.append(
            obj
        )

    products.sort(
        key=lambda obj: (
            obj.bvt_object.instance_id
        )
    )

    return tuple(
        products
    )


def remove_retail_edge_case_occluders(
    scene,
):
    removed = []

    for obj in list(
        scene.objects
    ):
        if not bool(
            obj.get(
                "bvt_retail_edge_case_occluder",
                False,
            )
        ):
            continue

        name = obj.name

        mesh = getattr(
            obj,
            "data",
            None,
        )

        bpy.data.objects.remove(
            obj,
            do_unlink=True,
        )

        if (
            mesh is not None
            and getattr(
                mesh,
                "users",
                1,
            )
            == 0
        ):
            bpy.data.meshes.remove(
                mesh
            )

        removed.append(
            name
        )

    return tuple(
        removed
    )


def capture_retail_edge_case_baseline(
    scene,
):
    baseline = {}

    for obj in iter_retail_products(
        scene
    ):
        instance_id = (
            obj.bvt_object.instance_id
        )

        baseline[
            instance_id
        ] = {
            "object_name": (
                obj.name
            ),
            "location": (
                obj.location.copy()
            ),
            "rotation_euler": (
                obj.rotation_euler.copy()
            ),
            "hide_render": bool(
                obj.hide_render
            ),
            "annotation_enabled": bool(
                obj.bvt_object.annotation_enabled
            ),
        }

    return baseline


def restore_retail_edge_cases(
    scene,
    baseline,
):
    remove_retail_edge_case_occluders(
        scene
    )

    for obj in iter_retail_products(
        scene
    ):
        instance_id = (
            obj.bvt_object.instance_id
        )

        base = baseline.get(
            instance_id
        )

        if base is None:
            continue

        obj.location = (
            base[
                "location"
            ]
        )

        obj.rotation_euler = (
            base[
                "rotation_euler"
            ]
        )

        obj.hide_render = bool(
            base[
                "hide_render"
            ]
        )

        obj.bvt_object.annotation_enabled = bool(
            base[
                "annotation_enabled"
            ]
        )


def select_wrong_angle_target(
    scene,
    frame_seed,
):
    candidates = list(
        iter_retail_products(
            scene
        )
    )

    if not candidates:
        return None

    scored = []

    for obj in candidates:
        instance_id = (
            obj.bvt_object.instance_id
        )

        selection_seed = (
            derive_subseed(
                frame_seed,
                (
                    WRONG_ANGLE_NAMESPACE
                    + "/target"
                ),
                instance_id,
            )
        )

        scored.append(
            (
                selection_seed,
                instance_id,
                obj,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    selection_seed, _, obj = (
        scored[0]
    )

    return (
        obj,
        selection_seed,
    )


def derive_wrong_angle_delta(
    frame_seed,
    instance_id,
    minimum_degrees,
    maximum_degrees,
):
    minimum_degrees = float(
        minimum_degrees
    )

    maximum_degrees = float(
        maximum_degrees
    )

    if minimum_degrees < 0.0:
        raise ValueError(
            "Wrong Angle minimum must be >= 0"
        )

    if maximum_degrees < minimum_degrees:
        raise ValueError(
            (
                "Wrong Angle maximum must be "
                ">= minimum"
            )
        )

    magnitude_seed = (
        derive_subseed(
            frame_seed,
            (
                WRONG_ANGLE_NAMESPACE
                + "/magnitude"
            ),
            instance_id,
        )
    )

    sign_seed = (
        derive_subseed(
            frame_seed,
            (
                WRONG_ANGLE_NAMESPACE
                + "/sign"
            ),
            instance_id,
        )
    )

    maximum_seed = float(
        0x7FFFFFFF
    )

    fraction = (
        float(
            magnitude_seed
        )
        / maximum_seed
    )

    magnitude = (
        minimum_degrees
        + (
            maximum_degrees
            - minimum_degrees
        )
        * fraction
    )

    sign = (
        -1.0
        if (
            sign_seed
            % 2
        )
        else 1.0
    )

    return {
        "delta_degrees": (
            sign
            * magnitude
        ),
        "magnitude_seed": (
            magnitude_seed
        ),
        "sign_seed": (
            sign_seed
        ),
    }


def apply_wrong_angle(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    target_result = (
        select_wrong_angle_target(
            scene,
            frame_seed,
        )
    )

    if target_result is None:
        return None

    obj, selection_seed = (
        target_result
    )

    instance_id = (
        obj.bvt_object.instance_id
    )

    base = baseline.get(
        instance_id
    )

    if base is None:
        raise ValueError(
            (
                "Retail edge-case baseline "
                "missing for "
                f"{instance_id}"
            )
        )

    angle = (
        derive_wrong_angle_delta(
            frame_seed,
            instance_id,
            (
                project_settings
                .retail_wrong_angle_min_degrees
            ),
            (
                project_settings
                .retail_wrong_angle_max_degrees
            ),
        )
    )

    event_seed = derive_subseed(
        frame_seed,
        WRONG_ANGLE_NAMESPACE,
        instance_id,
    )

    before_rotation_z = float(
        base[
            "rotation_euler"
        ].z
    )

    delta_radians = math.radians(
        angle[
            "delta_degrees"
        ]
    )

    after_rotation_z = (
        before_rotation_z
        + delta_radians
    )

    obj.rotation_euler.z = (
        after_rotation_z
    )

    return {
        "edge_case": "wrong_angle",
        "applied": True,
        "seed": event_seed,
        "selection_seed": (
            selection_seed
        ),
        "magnitude_seed": (
            angle[
                "magnitude_seed"
            ]
        ),
        "sign_seed": (
            angle[
                "sign_seed"
            ]
        ),
        "instance_id": (
            instance_id
        ),
        "object_name": obj.name,
        "axis": "Z",
        "delta_degrees": (
            angle[
                "delta_degrees"
            ]
        ),
        "before": {
            "rotation_z_degrees": (
                math.degrees(
                    before_rotation_z
                )
            ),
        },
        "after": {
            "rotation_z_degrees": (
                math.degrees(
                    after_rotation_z
                )
            ),
        },
    }


def select_wrong_position_target(
    scene,
    frame_seed,
):
    candidates = list(
        iter_retail_products(
            scene
        )
    )

    if not candidates:
        return None

    scored = []

    for obj in candidates:
        instance_id = (
            obj.bvt_object.instance_id
        )

        selection_seed = (
            derive_subseed(
                frame_seed,
                (
                    WRONG_POSITION_NAMESPACE
                    + "/target"
                ),
                instance_id,
            )
        )

        scored.append(
            (
                selection_seed,
                instance_id,
                obj,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    selection_seed, _, obj = (
        scored[0]
    )

    return (
        obj,
        selection_seed,
    )


def derive_wrong_position_offset(
    frame_seed,
    instance_id,
    maximum_x,
    maximum_y,
):
    maximum_x = float(
        maximum_x
    )

    maximum_y = float(
        maximum_y
    )

    if maximum_x < 0.0:
        raise ValueError(
            (
                "Wrong Position X range "
                "must be >= 0"
            )
        )

    if maximum_y < 0.0:
        raise ValueError(
            (
                "Wrong Position Y range "
                "must be >= 0"
            )
        )

    x_seed = derive_subseed(
        frame_seed,
        (
            WRONG_POSITION_NAMESPACE
            + "/x"
        ),
        instance_id,
    )

    y_seed = derive_subseed(
        frame_seed,
        (
            WRONG_POSITION_NAMESPACE
            + "/y"
        ),
        instance_id,
    )

    maximum_seed = float(
        0x7FFFFFFF
    )

    x_fraction = (
        (
            float(
                x_seed
            )
            / maximum_seed
        )
        * 2.0
        - 1.0
    )

    y_fraction = (
        (
            float(
                y_seed
            )
            / maximum_seed
        )
        * 2.0
        - 1.0
    )

    return {
        "x": (
            x_fraction
            * maximum_x
        ),
        "y": (
            y_fraction
            * maximum_y
        ),
        "z": 0.0,
        "x_seed": x_seed,
        "y_seed": y_seed,
    }


def apply_wrong_position(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    target_result = (
        select_wrong_position_target(
            scene,
            frame_seed,
        )
    )

    if target_result is None:
        return None

    obj, selection_seed = (
        target_result
    )

    instance_id = (
        obj.bvt_object.instance_id
    )

    if (
        instance_id
        not in baseline
    ):
        raise ValueError(
            (
                "Retail edge-case baseline "
                "missing for "
                f"{instance_id}"
            )
        )

    # This is intentionally captured AFTER the
    # placement layer. Wrong Position therefore
    # composes with deterministic placement.
    before_location = (
        obj.location.copy()
    )

    offset = (
        derive_wrong_position_offset(
            frame_seed,
            instance_id,
            (
                project_settings
                .retail_wrong_position_offset_x
            ),
            (
                project_settings
                .retail_wrong_position_offset_y
            ),
        )
    )

    obj.location.x = (
        before_location.x
        + offset[
            "x"
        ]
    )

    obj.location.y = (
        before_location.y
        + offset[
            "y"
        ]
    )

    # Wrong Position v0.1 never lifts or lowers
    # the product from the current shelf Z.
    obj.location.z = (
        before_location.z
    )

    after_location = (
        obj.location.copy()
    )

    event_seed = derive_subseed(
        frame_seed,
        WRONG_POSITION_NAMESPACE,
        instance_id,
    )

    return {
        "edge_case": "wrong_position",
        "applied": True,
        "seed": event_seed,
        "selection_seed": (
            selection_seed
        ),
        "x_seed": (
            offset[
                "x_seed"
            ]
        ),
        "y_seed": (
            offset[
                "y_seed"
            ]
        ),
        "instance_id": (
            instance_id
        ),
        "object_name": obj.name,
        "shelf_id": obj.get(
            "bvt_shelf_id",
            "",
        ),
        "slot_id": obj.get(
            "bvt_slot_id",
            "",
        ),
        "offset_m": [
            offset[
                "x"
            ],
            offset[
                "y"
            ],
            0.0,
        ],
        "before": {
            "location_m": [
                float(
                    before_location.x
                ),
                float(
                    before_location.y
                ),
                float(
                    before_location.z
                ),
            ],
        },
        "after": {
            "location_m": [
                float(
                    after_location.x
                ),
                float(
                    after_location.y
                ),
                float(
                    after_location.z
                ),
            ],
        },
    }


def select_empty_slot_target(
    scene,
    frame_seed,
):
    candidates = list(
        iter_retail_products(
            scene
        )
    )

    if not candidates:
        return None

    scored = []

    for obj in candidates:
        slot_id = str(
            obj.get(
                "bvt_slot_id",
                "",
            )
        ).strip()

        if not slot_id:
            raise ValueError(
                (
                    "Retail product has no "
                    "bvt_slot_id: "
                    f"{obj.name}"
                )
            )

        selection_seed = derive_subseed(
            frame_seed,
            (
                EMPTY_SLOT_NAMESPACE
                + "/target"
            ),
            slot_id,
        )

        scored.append(
            (
                selection_seed,
                slot_id,
                obj,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    selection_seed, _, obj = (
        scored[0]
    )

    return (
        obj,
        selection_seed,
    )


def apply_empty_slot(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    target_result = (
        select_empty_slot_target(
            scene,
            frame_seed,
        )
    )

    if target_result is None:
        return None

    obj, selection_seed = (
        target_result
    )

    instance_id = (
        obj.bvt_object.instance_id
    )

    base = baseline.get(
        instance_id
    )

    if base is None:
        raise ValueError(
            (
                "Retail edge-case baseline "
                "missing for "
                f"{instance_id}"
            )
        )

    slot_id = str(
        obj.get(
            "bvt_slot_id",
            "",
        )
    ).strip()

    shelf_id = str(
        obj.get(
            "bvt_shelf_id",
            "",
        )
    ).strip()

    sku_id = str(
        obj.get(
            "bvt_sku_id",
            "",
        )
    ).strip()

    if not slot_id:
        raise ValueError(
            "Empty Slot target has no slot_id"
        )

    before_hide_render = bool(
        obj.hide_render
    )

    before_annotation = bool(
        obj.bvt_object.annotation_enabled
    )

    obj.hide_render = True

    obj.bvt_object.annotation_enabled = False

    event_seed = derive_subseed(
        frame_seed,
        EMPTY_SLOT_NAMESPACE,
        slot_id,
    )

    return {
        "edge_case": "empty_slot",
        "applied": True,
        "seed": event_seed,
        "selection_seed": (
            selection_seed
        ),
        "instance_id": (
            instance_id
        ),
        "object_name": obj.name,
        "sku_id": sku_id,
        "shelf_id": shelf_id,
        "slot_id": slot_id,
        "before": {
            "hide_render": (
                before_hide_render
            ),
            "annotation_enabled": (
                before_annotation
            ),
        },
        "after": {
            "hide_render": True,
            "annotation_enabled": False,
        },
    }


def select_occlusion_target(
    scene,
    frame_seed,
):
    candidates = [
        obj
        for obj
        in iter_retail_products(
            scene
        )
        if (
            not obj.hide_render
            and obj.bvt_object.annotation_enabled
        )
    ]

    if not candidates:
        return None

    scored = []

    for obj in candidates:
        instance_id = (
            obj.bvt_object.instance_id
        )

        selection_seed = derive_subseed(
            frame_seed,
            (
                OCCLUSION_NAMESPACE
                + "/target"
            ),
            instance_id,
        )

        scored.append(
            (
                selection_seed,
                instance_id,
                obj,
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    selection_seed, _, obj = (
        scored[0]
    )

    return (
        obj,
        selection_seed,
    )


def get_occluder_material():
    name = (
        "BVT_Retail_EdgeCase_Occluder"
    )

    material = bpy.data.materials.get(
        name
    )

    if material is None:
        material = bpy.data.materials.new(
            name=name
        )

        material.diffuse_color = (
            0.025,
            0.025,
            0.030,
            1.0,
        )

    return material


def create_box_mesh(
    name,
    width,
    depth,
    height,
):
    half_width = (
        width
        / 2.0
    )

    half_depth = (
        depth
        / 2.0
    )

    half_height = (
        height
        / 2.0
    )

    vertices = [
        (
            -half_width,
            -half_depth,
            -half_height,
        ),
        (
            half_width,
            -half_depth,
            -half_height,
        ),
        (
            half_width,
            half_depth,
            -half_height,
        ),
        (
            -half_width,
            half_depth,
            -half_height,
        ),
        (
            -half_width,
            -half_depth,
            half_height,
        ),
        (
            half_width,
            -half_depth,
            half_height,
        ),
        (
            half_width,
            half_depth,
            half_height,
        ),
        (
            -half_width,
            half_depth,
            half_height,
        ),
    ]

    faces = [
        (
            0,
            1,
            2,
            3,
        ),
        (
            4,
            7,
            6,
            5,
        ),
        (
            0,
            4,
            5,
            1,
        ),
        (
            1,
            5,
            6,
            2,
        ),
        (
            2,
            6,
            7,
            3,
        ),
        (
            4,
            0,
            3,
            7,
        ),
    ]

    mesh = bpy.data.meshes.new(
        name=name
        + "_Mesh"
    )

    mesh.from_pydata(
        vertices,
        [],
        faces,
    )

    mesh.update()

    return mesh


def apply_occlusion(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    target_result = (
        select_occlusion_target(
            scene,
            frame_seed,
        )
    )

    if target_result is None:
        return None

    obj, selection_seed = (
        target_result
    )

    instance_id = (
        obj.bvt_object.instance_id
    )

    if (
        instance_id
        not in baseline
    ):
        raise ValueError(
            (
                "Retail edge-case baseline "
                "missing for "
                f"{instance_id}"
            )
        )

    width_factor = float(
        project_settings
        .retail_occlusion_width_factor
    )

    height_factor = float(
        project_settings
        .retail_occlusion_height_factor
    )

    if not (
        0.0
        < width_factor
        < 1.0
    ):
        raise ValueError(
            (
                "Occlusion width factor must "
                "be between 0 and 1"
            )
        )

    if not (
        0.0
        < height_factor
        < 1.0
    ):
        raise ValueError(
            (
                "Occlusion height factor must "
                "be between 0 and 1"
            )
        )

    dimensions = (
        obj.dimensions.copy()
    )

    occluder_width = max(
        0.01,
        float(
            dimensions.x
        )
        * width_factor,
    )

    occluder_depth = 0.012

    occluder_height = max(
        0.02,
        float(
            dimensions.z
        )
        * height_factor,
    )

    event_seed = derive_subseed(
        frame_seed,
        OCCLUSION_NAMESPACE,
        instance_id,
    )

    object_name = (
        "BVT_Occluder_"
        + str(
            event_seed
        )
    )

    mesh = create_box_mesh(
        object_name,
        occluder_width,
        occluder_depth,
        occluder_height,
    )

    occluder = bpy.data.objects.new(
        object_name,
        mesh,
    )

    scene.collection.objects.link(
        occluder
    )

    material = (
        get_occluder_material()
    )

    occluder.data.materials.append(
        material
    )

    # Camera is on negative Y in the canonical
    # Beverage Fridge scene. Place the occluder
    # slightly in front of the selected package,
    # but still behind the fridge glass.
    occluder.location.x = (
        float(
            obj.location.x
        )
    )

    occluder.location.y = (
        float(
            obj.location.y
        )
        - (
            float(
                dimensions.y
            )
            / 2.0
        )
        - (
            occluder_depth
            / 2.0
        )
        - 0.006
    )

    occluder.location.z = (
        float(
            obj.location.z
        )
        + (
            float(
                dimensions.z
            )
            / 2.0
        )
    )

    occluder[
        "bvt_retail_edge_case_occluder"
    ] = True

    occluder[
        "bvt_edge_case"
    ] = "occlusion"

    occluder[
        "bvt_target_instance_id"
    ] = instance_id

    bpy.context.view_layer.update()

    slot_id = str(
        obj.get(
            "bvt_slot_id",
            "",
        )
    ).strip()

    shelf_id = str(
        obj.get(
            "bvt_shelf_id",
            "",
        )
    ).strip()

    return {
        "edge_case": "occlusion",
        "applied": True,
        "seed": event_seed,
        "selection_seed": (
            selection_seed
        ),
        "instance_id": (
            instance_id
        ),
        "object_name": obj.name,
        "slot_id": slot_id,
        "shelf_id": shelf_id,
        "occluder": {
            "object_name": (
                occluder.name
            ),
            "annotation_target": False,
            "asset_registered": False,
            "dimensions_m": [
                float(
                    occluder_width
                ),
                float(
                    occluder_depth
                ),
                float(
                    occluder_height
                ),
            ],
            "location_m": [
                float(
                    occluder.location.x
                ),
                float(
                    occluder.location.y
                ),
                float(
                    occluder.location.z
                ),
            ],
        },
        "before": {
            "occluder_present": False,
            "annotation_enabled": bool(
                obj.bvt_object.annotation_enabled
            ),
        },
        "after": {
            "occluder_present": True,
            "annotation_enabled": bool(
                obj.bvt_object.annotation_enabled
            ),
        },
    }


def apply_retail_edge_cases(
    scene,
    project_settings,
    frame_seed,
    baseline,
):
    if (
        not project_settings
        .retail_edge_cases_enabled
    ):
        return {
            "enabled": False,
            "version": (
                RETAIL_EDGE_CASES_VERSION
            ),
            "seed_strategy": (
                SUBSEED_STRATEGY
            ),
            "events": [],
        }

    events = []

    if (
        project_settings
        .retail_wrong_angle_enabled
    ):
        event = apply_wrong_angle(
            scene=scene,
            project_settings=(
                project_settings
            ),
            frame_seed=frame_seed,
            baseline=baseline,
        )

        if event is not None:
            events.append(
                event
            )

    if (
        project_settings
        .retail_wrong_position_enabled
    ):
        event = apply_wrong_position(
            scene=scene,
            project_settings=(
                project_settings
            ),
            frame_seed=frame_seed,
            baseline=baseline,
        )

        if event is not None:
            events.append(
                event
            )

    if (
        project_settings
        .retail_empty_slot_enabled
    ):
        event = apply_empty_slot(
            scene=scene,
            project_settings=(
                project_settings
            ),
            frame_seed=frame_seed,
            baseline=baseline,
        )

        if event is not None:
            events.append(
                event
            )

    if (
        project_settings
        .retail_occlusion_enabled
    ):
        event = apply_occlusion(
            scene=scene,
            project_settings=(
                project_settings
            ),
            frame_seed=frame_seed,
            baseline=baseline,
        )

        if event is not None:
            events.append(
                event
            )

    return {
        "enabled": True,
        "version": (
            RETAIL_EDGE_CASES_VERSION
        ),
        "seed_strategy": (
            SUBSEED_STRATEGY
        ),
        "events": events,
    }
