import uuid


def register_object(obj):
    if obj is None:
        raise ValueError("No active object selected")

    if obj.type != "MESH":
        raise ValueError("Only mesh objects can be registered for annotation")

    settings = obj.bvt_object

    class_name = settings.class_name.strip()

    if not class_name:
        raise ValueError("Class Name cannot be empty")

    settings.class_name = class_name

    if not settings.instance_id:
        settings.instance_id = uuid.uuid4().hex

    settings.registered = True

    return settings


def iter_annotated_objects(scene):
    objects = []

    for obj in scene.objects:
        if obj.type != "MESH":
            continue

        settings = obj.bvt_object

        if not settings.registered:
            continue

        if not settings.annotation_enabled:
            continue

        objects.append(obj)

    return objects
