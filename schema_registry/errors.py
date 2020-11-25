class SchemaRegistryError(Exception):
    pass

class ModelNotRegisteredError(SchemaRegistryError):
    def __init__(self, model):
        self.model = model