from ocf_freecad.schema.loader import load_schema

class CreateFromSchemaCommand:
    def Activated(self):
        data = load_schema("controller.hw.yaml")
        print(data)