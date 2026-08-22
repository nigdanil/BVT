from . import annotation
from . import project
from . import ui


def register():
    project.register()
    annotation.register()
    ui.register()


def unregister():
    ui.unregister()
    annotation.unregister()
    project.unregister()
