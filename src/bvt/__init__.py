from . import annotation
from . import materials
from . import project
from . import ui


def register():
    project.register()
    annotation.register()
    materials.register()
    ui.register()


def unregister():
    ui.unregister()
    materials.unregister()
    annotation.unregister()
    project.unregister()
