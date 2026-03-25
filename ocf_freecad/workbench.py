import FreeCADGui as Gui

class OpenControllerWorkbench(Gui.Workbench):
    MenuText = "Open Controller"
    ToolTip = "Modular MIDI Controller Design"
    Icon = ""

    def Initialize(self):
        from ocf_freecad.commands.create_controller import CreateControllerCommand

        Gui.addCommand("OCF_CreateController", CreateControllerCommand())

        self.appendToolbar("OCF", ["OCF_CreateController"])
        self.appendMenu("OCF", ["OCF_CreateController"])

    def Activated(self):
        pass

    def Deactivated(self):
        pass