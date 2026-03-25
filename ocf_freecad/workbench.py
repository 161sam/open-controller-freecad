import FreeCADGui as Gui

class OpenControllerWorkbench(Gui.Workbench):
    MenuText = "Open Controller"
    ToolTip = "Modular MIDI Controller Design"
    Icon = ""

    def Initialize(self):
        from ocf_freecad.commands.add_component import AddComponentCommand
        from ocf_freecad.commands.auto_layout import AutoLayoutCommand
        from ocf_freecad.commands.create_controller import CreateControllerCommand
        from ocf_freecad.commands.move_component import MoveComponentCommand
        from ocf_freecad.commands.validate_layout import ValidateLayoutCommand

        Gui.addCommand("OCF_CreateController", CreateControllerCommand())
        Gui.addCommand("OCF_AddComponent", AddComponentCommand())
        Gui.addCommand("OCF_AutoLayout", AutoLayoutCommand())
        Gui.addCommand("OCF_MoveComponent", MoveComponentCommand())
        Gui.addCommand("OCF_ValidateLayout", ValidateLayoutCommand())

        commands = [
            "OCF_CreateController",
            "OCF_AddComponent",
            "OCF_MoveComponent",
            "OCF_AutoLayout",
            "OCF_ValidateLayout",
        ]
        self.appendToolbar("OCF", commands)
        self.appendMenu("OCF", commands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass
