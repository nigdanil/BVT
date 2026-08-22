from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def calculate_yolo_bbox(scene, camera, obj):
    world_corners = [
        obj.matrix_world @ Vector(corner)
        for corner in obj.bound_box
    ]

    projected = [
        world_to_camera_view(
            scene,
            camera,
            corner,
        )
        for corner in world_corners
    ]

    visible_points = [
        point
        for point in projected
        if point.z > 0.0
    ]

    if not visible_points:
        return None

    min_x = max(
        0.0,
        min(point.x for point in visible_points),
    )

    max_x = min(
        1.0,
        max(point.x for point in visible_points),
    )

    min_y = max(
        0.0,
        min(point.y for point in visible_points),
    )

    max_y = min(
        1.0,
        max(point.y for point in visible_points),
    )

    if max_x <= min_x:
        return None

    if max_y <= min_y:
        return None

    width = max_x - min_x
    height = max_y - min_y

    center_x = min_x + width / 2.0

    # Blender camera coordinates use bottom-left as the origin.
    # YOLO image coordinates use top-left.
    center_y = 1.0 - (
        min_y + height / 2.0
    )

    return {
        "x_center": center_x,
        "y_center": center_y,
        "width": width,
        "height": height,
    }
