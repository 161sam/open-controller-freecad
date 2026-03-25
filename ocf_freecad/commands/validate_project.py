from ocf_freecad.schema.validator import validate_schema

class ValidateProjectCommand:
    def Activated(self):
        validate_schema({})
        print("Validation complete")