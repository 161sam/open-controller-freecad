class BaseCommand:
    def GetResources(self):
        return {
            "MenuText": "Base Command",
            "ToolTip": "Base Command"
        }

    def IsActive(self):
        return True