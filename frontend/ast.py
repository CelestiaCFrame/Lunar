class Stmt:
    def __init__(self, kind: str):
        self.kind = kind
    
class Expr(Stmt):
    pass

class Program(Stmt):
    def __init__(self, body: list[Stmt], comments: list[Stmt], range: list):
        super().__init__("Program")
        self.body = body
        self.comments = comments
        self.range = range

    def __repr__(self):
        return str({"kind": "Program", "body": self.body, "comments": self.comments, "range": self.range})

class VarDeclaration(Stmt):
    def __init__(self, Identifier: str, value: Stmt = None, constant: bool = False, range: list = []):
        super().__init__("VarDeclaration")
        self.Identifier = Identifier
        self.value = value
        self.constant = constant
        self.range = range

    def __repr__(self):
        return str({"kind": "VarDeclaration", "identifier": self.Identifier, "value": self.value, "constant": self.constant, "range": self.range})
    
class Comment(Stmt):
    def __init__(self, value: str, range: list):
        super().__init__("Comment")
        self.value = value
        self.raw = "//" + value
        self.range = range

    def __repr__(self):
        return str({"kind": "Comment", "value": self.value, "raw": self.raw, "range": self.range})
    
class IfStatement(Stmt):
    def __init__(self, clauses: Stmt, range: list):
        super().__init__("IfStatement")
        self.clauses = clauses
        self.range = range

    def __repr__(self):
        return str({"kind": "IfStatement", "clauses": self.clauses, "range": self.range})
    
class IfClause(Stmt):
    def __init__(self, condition: Stmt, body: list[Stmt], range: list):
        super().__init__("IfClause")
        self.condition = condition
        self.body = body
        self.range = range

    def __repr__(self):
        return str({"kind": "IfClause", "condition": self.condition, "body": self.body, "range": self.range})
    
class ForStatement(Stmt):
    def __init__(self, variable: Stmt, condition: Stmt, increment: Stmt, body: list[Stmt], range: list):
        super().__init__("ForStatement")
        self.variable = variable
        self.condition = condition
        self.increment = increment
        self.body = body
        self.range = range

    def __repr__(self):
        return str({"kind": "ForStatement", "variable": self.variable, "condition": self.condition, "increment": self.increment, "body": self.body, "range": self.range})
    
class ReturnStatement(Stmt):
    def __init__(self, arguments: list[Stmt], range: list):
        super().__init__("ReturnStatement")
        self.arguments = arguments
        self.range = range

    def __repr__(self):
        return str({"kind": "ReturnStatement", "arguments": self.arguments, "range": self.range})
    
class BreakStatement(Stmt):
    def __init__(self, range: list):
        super().__init__("BreakStatement")
        self.range = range

    def __repr__(self):
        return str({"kind": "BreakStatement", "range": self.range})
    
class ContinueStatement(Stmt):
    def __init__(self, range: list):
        super().__init__("ContinueStatement")
        self.range = range

    def __repr__(self):
        return str({"kind": "ContinueStatement", "range": self.range})

class FunctionDeclaration(Stmt):
    def __init__(self, parameters: list[str], name: str, body: list[Stmt], range: list):
        super().__init__("FunctionDeclaration")
        self.parameters = parameters
        self.name = name
        self.body = body
        self.range = range

    def __repr__(self):
        return str({"kind": "FunctionDeclaration", "name": self.name, "parameters": self.parameters, "body": self.body, "range": self.range})

class AssignmentExpr(Expr):
    def __init__(self, assign: Expr, value: Expr, range: list):
        super().__init__("AssignmentExpr")
        self.assign = assign
        self.value = value
        self.range = range

    def __repr__(self):
        return str({"kind": "AssignmentExpr", "assign": self.assign, "value": self.value, "range": self.range})

class BinaryExpr(Expr):
    def __init__(self, left: Expr, right: Expr, operator: str, range: list):
        super().__init__("BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator
        self.range = range

    def __repr__(self):
        return str({"kind": "BinaryExpr", "left": self.left, "right": self.right, "body": self.operator, "range": self.range})
    
class UnaryExpr(Expr):
    def __init__(self, args: list[Expr], operator: str, range: list):
        super().__init__("UnaryExpr")
        self.args = args
        self.operator = operator
        self.range = range

    def __repr__(self):
        return str({"kind": "UnaryExpr", "args": self.args, "body": self.operator, "range": self.range})
    
class LogicalExpr(Expr):
    def __init__(self, left: Expr, right: Expr, operator: str, range: list):
        super().__init__("LogicalExpr")
        self.left = left
        self.right = right
        self.operator = operator
        self.range = range

    def __repr__(self):
        return str({"kind": "LogicalExpr", "left": self.left, "right": self.right, "body": self.operator, "range": self.range})

class CallExpr(Expr):
    def __init__(self, args: list[Expr], caller: Expr, range: list):
        super().__init__("CallExpr")
        self.args = args
        self.caller = caller
        self.range = range

    def __repr__(self):
        return str({"kind": "CallExpr", "args": self.args, "caller": self.caller, "range": self.range})

class MemberExpr(Expr):
    def __init__(self, object: Expr, property: Expr, operator: str, computed: bool = False, range: list = []):
        super().__init__("MemberExpr")
        self.object = object
        self.property = property
        self.operator = operator
        self.computed = computed
        self.range = range

    def __repr__(self):
        return str({"kind": "MemberExpr", "object": self.object, "property": self.property, "operator": self.operator, "computed": self.computed, "range": self.range})

class Identifier(Expr):
    def __init__(self, symbol: str, range: list = []):
        super().__init__("Identifier")
        self.symbol = symbol
        self.range = range

    def __repr__(self):
        return str({"kind": "Identifier", "symbol": self.symbol, "range": self.range})

class NumericLiteral(Expr):
    def __init__(self, value: int, range: list = []):
        super().__init__("NumericLiteral")
        self.value = value
        self.range = range

    def __repr__(self):
        return str({"kind": "NumericLiteral", "value": self.value, "range": self.range})
    
class StringLiteral(Expr):
    def __init__(self, value: str, range: list):
        super().__init__("StringLiteral")
        self.value = value
        self.range = range

    def __repr__(self):
        return str({"kind": "StringLiteral", "value": self.value, "range": self.range})

class Property(Expr):
    def __init__(self, key: str, value: Expr = None, range: list = []):
        super().__init__("Property")
        self.key = key
        self.value = value
        self.range = range

    def __repr__(self):
        return str({"kind": "Property", "key": self.key, "value": self.value, "range": self.range})
    
    def as_dict(self):
        return {self.key: self.value}

class ObjectLiteral(Expr):
    def __init__(self, properties: list[Property], range: list = []):
        super().__init__("ObjectLiteral")
        self.properties = properties
        self.range = range

    def __repr__(self):
        return str({"kind": "ObjectLiteral", "properties": self.properties, "range": self.range})
    
class VarargLiteral(Expr):
    def __init__(self, range: list = []):
        super().__init__("VarargLiteral")
        self.value = "..."
        self.range = range

    def __repr__(self):
        return str({"kind": "VarargLiteral", "value": self.value, "range": self.range})