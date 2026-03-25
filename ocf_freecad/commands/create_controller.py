import FreeCAD as App
from ocf_freecad.commands.base import BaseCommand

class CreateControllerCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Create Controller",
            "ToolTip": "Create a new MIDI controller project"
        }

    def Activated(self):
        doc = App.newDocument("Controller")
        print("New controller document created:", doc.Name)