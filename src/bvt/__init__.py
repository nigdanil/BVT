from . import project
from . import ui


def register():
    project.register()
    ui.register()


def unregister():
    ui.unregister()
    project.unregister()
