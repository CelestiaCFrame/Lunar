from frontend.ast import Identifier, BinaryExpr, AssignmentExpr, ObjectLiteral, CallExpr, MemberExpr, LogicalExpr, StringLiteral, NumericLiteral, UnaryExpr
from frontend.lexer import token
from runtime.values import NumberVal, RuntimeVal, NilVal, ObjectVal, BoolVal, FunctionValue, StringVal, VarargVal, NativeFnValue
from runtime.environment import Environment
from frontend.errorhandler import ErrorHandler

def interpret_numeric_binary_expr(lhs: RuntimeVal, rhs: RuntimeVal, binop: BinaryExpr, env: Environment) -> RuntimeVal:
    result = 0
    operator = binop.operator
    if operator == "+":
        if lhs.value != "nil" or rhs.value != "nil":
            result = lhs.value + rhs.value
        else:
            return NilVal()
    elif operator == "-":
        if lhs.value != "nil" or rhs.value != "nil":
            result = lhs.value - rhs.value
        else:
            return NilVal()
    elif operator == "*":
        if lhs.value != "nil" or rhs.value != "nil":
            result = lhs.value * rhs.value
        else:
            return NilVal()
    elif operator == "/":
        if lhs.value != "nil" or rhs.value != "nil":
            if rhs.value == 0:
                if lhs.value == 0:
                    result = float("nan")
                else:
                    result = float("inf")
            else:
                result = lhs.value / rhs.value
        else:
            return NilVal()
    elif operator == "%":
        result = lhs.value % rhs.value
    elif operator == "^":
        try:
            result = lhs.value ** rhs.value
        except:
            result = float("inf")
    elif operator == "..":
        result = str(lhs.value) + str(rhs.value)
    elif operator == "==":
        result = lhs.value == rhs.value
    elif operator == ">=":
        result = lhs.value >= rhs.value
    elif operator == "<=":
        result = lhs.value <= rhs.value
    elif operator == "!=":
        result = lhs.value != rhs.value
    elif operator == "<":
        result = lhs.value < rhs.value
    elif operator == ">":
        result = lhs.value > rhs.value
    elif operator == "+=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value + rhs.value))
    elif operator == "-=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value - rhs.value))
    elif operator == "*=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value * rhs.value))
    elif operator == "/=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value / rhs.value))
    elif operator == "^=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value ** rhs.value))
    elif operator == "%=":
        env.assignVar(binop.left.symbol, NumberVal(lhs.value % rhs.value))

    if isinstance(result, bool):
        return BoolVal(result)
    return NumberVal(result)

def interpret_binary_expr(binop: BinaryExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    if isinstance(binop.left, list):
        binop.left = binop.left[0]
    leftHandSide = interpreter(binop.left, env)
    rightHandSide = interpreter(binop.right, env)

    if (isinstance(leftHandSide, NumberVal) and isinstance(rightHandSide, NumberVal)) or binop.operator in ["!=", "==", ">=", "<=", ">", "<"]:
        return interpret_numeric_binary_expr(leftHandSide, rightHandSide, binop, env)
    elif binop.operator == "..":
        if (isinstance(leftHandSide, StringVal) or isinstance(leftHandSide, NumberVal)) and isinstance(rightHandSide, StringVal) or isinstance(rightHandSide, NumberVal):
            return interpret_numeric_binary_expr(leftHandSide, rightHandSide, binop, env)
        else:
            ErrorHandler(f"Attempt to concatenate {leftHandSide.type} with {rightHandSide.type}", binop.range, env)
    elif isinstance(leftHandSide, BoolVal) and isinstance(rightHandSide, BoolVal) and not (binop.operator in ["+", "-", "*", "/", "^", "%"]):
        return interpret_numeric_binary_expr(leftHandSide, rightHandSide, binop, env)
    else:
        if binop.operator in ["+", "+="]:
            ErrorHandler(f"Attempt to perform arithmetic (add) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
        elif binop.operator in ["-", "-="]:
            ErrorHandler(f"Attempt to perform arithmetic (sub) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
        elif binop.operator in ["*", "*="]:
            ErrorHandler(f"Attempt to perform arithmetic (mul) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
        elif binop.operator in ["/", "/="]:
            ErrorHandler(f"Attempt to perform arithmetic (div) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
        elif binop.operator in ["^", "^="]:
            ErrorHandler(f"Attempt to perform arithmetic (pow) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
        elif binop.operator in ["%", "%="]:
            ErrorHandler(f"Attempt to perform arithmetic (mod) on {leftHandSide.type} and {rightHandSide.type}", binop.range, env)
    
    return NilVal()

def interpret_logical_expr(binop: LogicalExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    lhs = interpreter(binop.left, env)
    rhs = interpreter(binop.right, env)
    operator = binop.operator
    if operator == "and":
        if lhs.value != "true":
            if lhs.value == "false":
                return BoolVal(False)
            elif lhs.value == "nil":
                return NilVal()
        if not (rhs.value in ["false", "nil"]):
            return rhs
        else:
            return NilVal()
    elif operator == "or":
        if lhs.value == "true" or rhs.value == "true":
            return BoolVal(True)
        if not (lhs.value in ["false", "nil"]):
            return lhs
        if not (rhs.value in ["false", "nil"]):
            return rhs

def interpret_identifier(ident: Identifier, env: Environment) -> RuntimeVal:
    val = env.lookupVar(ident.symbol)
    return val

def interpret_assignment(node: AssignmentExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    if not isinstance(node.assign, list):
        node.assign = [node.assign]
    if not isinstance(node.value, list):
        node.value = [node.value]
    i = 0
    for index in range(len(node.value)):
        variable = node.assign[i]
        if variable.kind == "Identifier":
            if node.value[index].kind == "FunctionDeclaration" and node.value[i].name == None:
                node.value[index].name = variable
            varName = variable.symbol
            value = interpreter(node.value[index], env)
            if isinstance(value, list) or isinstance(value, tuple):
                for n in value:
                    if len(node.assign) <= i:
                        break
                    env.assignVar(node.assign[i].symbol, n)
                    i += 1
                i -= 1
            else:
                env.assignVar(varName, value)
        elif variable.kind == "MemberExpr":
            result = []
            expr = variable
            while isinstance(expr, MemberExpr):
                if isinstance(expr.property, StringLiteral) or isinstance(expr.property, NumericLiteral):
                    result.append(expr.property.value)
                elif isinstance(expr.property, Identifier) and expr.computed == True:
                    value = str(interpreter(expr.property, env).value)
                    if value != "nil":
                        result.append(value)
                    else:
                        ErrorHandler(f"Table index cannot be nil.", None)
                elif isinstance(expr.property, Identifier) and expr.computed == False:
                    result.append(expr.property.symbol)
                expr = expr.object

            result.append(expr.symbol)
            result = result[::-1]
            env.changeVarValue(result, interpreter(node.value[i], env), node)
        else:
            ErrorHandler(f"Invaild LHS inside assignment expr {variable}", None)
        i += 1

def interpret_unary_expr(node: UnaryExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    if node.operator == "#":
        value = interpreter(node.args, env)
        if isinstance(value, StringVal):
            return NumberVal(len(value.value))
        elif isinstance(value, ObjectVal):
            return NumberVal(len(value.properties))
        elif isinstance(value, VarargVal):
            return NumberVal(len(value.values[0]))
        else:
            ErrorHandler(f"Attempt to get length of a {value.type} value", node.range, env, env.selectedFile)
    elif node.operator == "not":
        if isinstance(node.args, StringLiteral) or isinstance(node.args, NumericLiteral) or isinstance(node.args, ObjectLiteral):
            return BoolVal(False)
        else:
            value = interpreter(node.args, env)
            if value.value == "true":
                return BoolVal(False)
            elif value.value == "false":
                return BoolVal(True)
            elif value.value == "nil":
                return BoolVal(True)
    elif node.operator == "-":
        value = interpreter(node.args, env)
        if value.type == "number":
            return NumberVal(-value.value)
        else:
            ErrorHandler(f"Attempt to perform arithmetic on {value.type}", node.range, env, env.selectedFile)

def interpret_object_expr(obj: ObjectLiteral, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    object = ObjectVal({})
    properties = obj.properties
    indexRange = 1
    for i in properties:
        for n in i.as_dict():
            if isinstance(n, Identifier):
                k = interpreter(n, env)
                if k.value == "nil":
                    ErrorHandler("Table index is nil", obj.range, env, env.selectedFile)
            else:
                k = n
            v = i.as_dict()[n]
        if k == None:
            k = NumberVal(indexRange)
            indexRange += 1
        runtimeVal = env.lookupVar(k) if v == None else interpreter(v, env)
        if isinstance(runtimeVal, FunctionValue) and runtimeVal.name == None:
            runtimeVal.name = i.key.value
        alreadyInTable = False
        for i in object.properties:
            if i.type == k.type and i.value == k.value:
                alreadyInTable = i
                break
        if alreadyInTable == False:
            object.properties[k] = runtimeVal
        else:
            object.properties[alreadyInTable] = runtimeVal

    return object

def interpret_call_expr(expr: CallExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    args = []
    for arg in expr.args:
        if hasattr(arg, "kind"):
            try:
                args.append(interpreter(arg, env))
            except Exception as exception:
                raise Exception(exception)
        else:
            args.append(arg)
    fn = interpreter(expr.caller, env) if not isinstance(expr.caller, NativeFnValue) else expr.caller
    if isinstance(fn, tuple):
        fn = fn[0]
    if not isinstance(fn, StringLiteral):
        if isinstance(fn.type, type(None)):
            ErrorHandler(f"Attempt call a nil value", expr.range, env)
        if fn.type == "nativefn":
            try:
                result = fn.call(*args, env=env)
                return result
            except Exception as exception:
                ErrorHandler(exception, expr.range, env, env.selectedFile)
        if fn.type == "function":
            func = fn
            scope = Environment(func.declarationEnv)
            if isinstance(expr.caller, MemberExpr):
                if expr.caller.operator == ":":
                    if func.name and isinstance(func.name, str):
                        if func.parameters[0].symbol != "self":
                            ErrorHandler(f"The colon operator can only be used with methods", None)
                    elif func.name.operator == expr.caller.operator:
                        scope.declareVar("self", interpreter(expr.caller.object, env), False)
                    else:
                        ErrorHandler(f"The colon operator can only be used with methods", None)
                elif expr.caller.operator == ".":
                    if func.name and isinstance(func.name, str):
                        if func.parameters[0].symbol == "self":
                            ErrorHandler(f"Methods cannot be called with dot operator", None)
                    elif func.name and func.name.operator != expr.caller.operator:
                        ErrorHandler(f"Methods cannot be called with dot operator", None)
            for i in range(len(func.parameters)):
                if i >= len(args) - 1:
                    args.append(NilVal())
                varname = func.parameters[i].symbol
                scope.declareVar(varname, args[i], False)

            result = NilVal()
            for stmt in func.body:
                if stmt.kind == "ReturnStatement":
                    result = interpreter(stmt, scope)["value"]
                    break
                result = interpreter(stmt, scope) or NilVal()
                if isinstance(result, dict):
                    result = result["value"]
                    break

            return result
    
    if isinstance(fn, StringVal):
        if expr.caller.operator == ":":
            if expr.caller.property.symbol == "sub":
                result = interpreter(expr.caller.object, env)
                result.value = result.value[args[0].value - 1:args[1].value]
                return result
            else:
                ErrorHandler(f"Attempt to call missing method '{expr.caller.property.symbol}' of string", expr.range, env, env.selectedFile)
        else:
            ErrorHandler("Cannot call methods with dot operator", expr.range, env, env.selectedFile)
    elif isinstance(fn, NumberVal):
        ErrorHandler(f"Attempt to index number with {expr.caller.property.symbol}", expr.range, env, env.selectedFile)
    ErrorHandler(f"Cannot call a {fn.type} value", expr.range, env, env.selectedFile)

def interpret_member_expr(expr: MemberExpr, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    result = []
    result2 = expr
    while isinstance(expr, MemberExpr):
        if isinstance(expr.property, StringLiteral) or isinstance(expr.property, NumericLiteral):
            result.append(expr.property.value)
        elif isinstance(expr.property, Identifier) and expr.computed == True:
            value = interpreter(expr.property, env).value
            if value != "nil":
                result.append(value)
            else:
                ErrorHandler(f"Table index cannot be nil.", None)
        elif isinstance(expr.property, Identifier) and expr.computed == False:
            result.append(expr.property.symbol)
        expr = expr.object

    IsString = False
    if isinstance(expr, Identifier):
        result.append(expr.symbol)
    elif isinstance(expr, StringLiteral) or isinstance(expr, NumericLiteral) or isinstance(expr, ObjectLiteral):
        ErrorHandler(f"Expected identifier when parsing expression, got '{result2.operator}'", expr.range, env, env.selectedFile)
    result = result[::-1]
    if IsString == False:
        try:
            result2 = env.lookupVar(result[0])
        except:
            ErrorHandler("Attempt to call a nil value", expr.range, env, env.selectedFile)
        if isinstance(result2, StringVal):
            IsString = True
        elif isinstance(result2, FunctionValue) or isinstance(result2, NumberVal):
            ErrorHandler(f"Attempt to index {result2.type} with '{result[-1]}'", expr.range, env, env.selectedFile)
    index = 1
    index2 = 1
    if IsString == False:
        while index < len(result):
            if isinstance(result2, dict):
                if result2 == {}:
                    result2 = NilVal()
                    break

                if result[index] == "nil":
                    result2 = NilVal()
                    break

                for i in result2:
                    if i.value == result[index]:
                        result2 = result2.get(i)
                        index += 1
                        index2 = 0
                        break
                    index2 += 1

                if isinstance(result2, dict) and index2 == len(result2):
                    return NilVal()
            else:
                result2 = result2.properties

    return result2