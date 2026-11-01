from . import annotation
from . import assets
from . import materials
from . import project
from . import ui


def register():
    project.register()
    annotation.register()
    assets.register()
    materials.register()
    ui.register()


def unregister():
    ui.unregister()
    materials.unregister()
    assets.unregister()
    annotation.unregister()
    project.unregister()
