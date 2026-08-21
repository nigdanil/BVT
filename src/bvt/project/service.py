import uuid

from ..core.constants import PROJECT_SCHEMA_VERSION


def initialize_project(scene):
    settings = scene.bvt_project

    project_name = settings.project_name.strip()

    if not project_name:
        raise ValueError("Project Name cannot be empty")

    output_directory = settings.output_directory.strip()

    if not output_directory:
        raise ValueError("Output Directory cannot be empty")

    settings.project_name = project_name
    settings.output_directory = output_directory
    settings.schema_version = PROJECT_SCHEMA_VERSION

    if not settings.project_id:
        settings.project_id = uuid.uuid4().hex

    settings.initialized = True

    return settings
