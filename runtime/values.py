class RuntimeVal:
    def __init__(self, type: str):
        self.type = type

class NilVal(RuntimeVal):
    def __init__(self):
        super().__init__("nil")
        self.value = "nil"

    def __repr__(self):
        return str({"type": "nil", "value": self.value})

class NumberVal(RuntimeVal):
    def __init__(self, value: int):
        super().__init__("number")
        self.value = value

    def __repr__(self):
        return str({"type": "number", "value": self.value})
    
class StringVal(RuntimeVal):
    def __init__(self, value: str):
        super().__init__("string")
        self.value = value

    def __repr__(self):
        return str({"type": "string", "value": self.value})

class BoolVal(RuntimeVal):
    def __init__(self, value: bool):
        super().__init__("boolean")
        self.value = str(value).lower()

    def __repr__(self):
        return str({"type": "boolean", "value": self.value})
    
class VarargVal(RuntimeVal):
    def __init__(self, values: list):
        super().__init__("tuple")
        self.values = values

    def __repr__(self):
        return str({"type": "tuple", "values": self.values})

class ObjectVal(RuntimeVal):
    def __init__(self, properties: list[str, RuntimeVal], isfrozen: bool = False):
        super().__init__("table")
        self.properties = properties
        self.isfrozen = isfrozen

    def __repr__(self):
        return str({"type": "table", "properties": self.properties, "isfrozen": self.isfrozen})
    
    def get(self, index):
        for i in self.properties:
            if i.value == index:
                return self.properties[i]
        return NilVal()

class NativeFnValue(RuntimeVal):
    def __init__(self, call):
        super().__init__("nativefn")
        self.call = call

    def __repr__(self):
        return str({"type": "nativefn", "call": self.call})

class FunctionValue(RuntimeVal):
    def __init__(self, name: str, parameters: list[str], declarationEnv: list, body: list, range: list):
        super().__init__("function")
        self.name = name
        self.parameters = parameters
        self.declarationEnv = declarationEnv
        self.body = body
        self.range = range

    def __repr__(self):
        return str({"type": "function", "name": self.name, "parameters": self.parameters, "declarationEnv": self.declarationEnv, "body": self.body, "range": self.range})