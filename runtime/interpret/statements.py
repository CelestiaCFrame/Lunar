from frontend.ast import Program, VarDeclaration, FunctionDeclaration, IfStatement, ForStatement, ReturnStatement, BreakStatement, ContinueStatement, LogicalExpr, MemberExpr, UnaryExpr, Identifier, CallExpr
from runtime.interpret.expressions import interpret_binary_expr, interpret_logical_expr, interpret_unary_expr, interpret_identifier
from runtime.values import RuntimeVal, NilVal, FunctionValue, ObjectVal
from runtime.environment import Environment

def interpret_program(program: Program, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    lastInterpreted: RuntimeVal = NilVal()
    
    for statement in program.body:
        lastInterpreted = interpreter(statement, env)

    return lastInterpreted

def interpret_var_declaration(declaration: VarDeclaration, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    value = interpreter(declaration.value, env) if declaration.value else NilVal()
    
    return env.declareVar(declaration.Identifier, value, declaration.constant)

def interpret_function_declaration(declaration: FunctionDeclaration, env: Environment) -> RuntimeVal:
    if declaration.name == None:
        return FunctionValue(declaration.name, declaration.parameters, env, declaration.body, declaration.range)
    elif isinstance(declaration.name, MemberExpr):
        fn = FunctionValue(declaration.name, declaration.parameters, env, declaration.body, declaration.range)
        result = []
        expr = declaration.name
        while isinstance(expr, MemberExpr):
            result.append(expr.property.symbol)
            expr = expr.object

        result.append(expr.symbol)
        result = result[::-1]
        return env.changeVarValue(result, fn, fn)
    fn = FunctionValue(declaration.name.symbol, declaration.parameters, env, declaration.body, declaration.range)
    return env.declareVar(declaration.name.symbol, fn, False)

def interpret_if_statement(statement: IfStatement, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    for n in statement.clauses:
        if n.condition != None:
            if (isinstance(n.condition, LogicalExpr)):
                conditionResult = interpret_logical_expr(n.condition, env).value
            elif (isinstance(n.condition, UnaryExpr)):
                conditionResult = interpret_unary_expr(n.condition, env).value
            elif (isinstance(n.condition, Identifier)):
                conditionResult = interpret_identifier(n.condition, env).value
            else:
                conditionResult = interpret_binary_expr(n.condition, env).value
        else:
            conditionResult = "true"
        result = True
        if conditionResult == "true":
            result = True
        else:
            result = False
        if result:
            for i in n.body:
                result2 = interpreter(i, env)
                if result2 in ["break", "continue"]:
                    return result2
                elif isinstance(result2, dict):
                    return result2
            break

def interpret_for_statement(statement: ForStatement, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter

    if (statement.condition == None):
        if isinstance(statement.increment, CallExpr):
            ObjectValue = interpreter(statement.increment, env)
        else:
            raise Exception(f"An error occured")
        
        while True:
            try:
                result = interpreter(CallExpr([ObjectValue[1], result[0]], ObjectValue[0], []), env)
            except:
                result = interpreter(CallExpr([ObjectValue[1]], ObjectValue[0], []), env)
            for index in range(len(statement.variable)):
                env.assignVar(statement.variable[index].symbol, result[index])
            if result[0].type != "nil" and result[1].type != "nil":
                for i in statement.body:
                    result2 = interpreter(i, env)
                    if result2 in ["break", "continue"]:
                        break
                if len(statement.body) != 0 and result2 == "break":
                    break
            else:
                break
        """
        result = {}
        def ObjectValueToDict(n):
            table = {}
            for i in n.properties:
                if isinstance(n.properties[i], ObjectVal):
                    table[i.value] = ObjectValueToDict(n.properties[i])
                else:
                    table[i.value] = n.properties[i].value
            return table

        result = ObjectValueToDict(ObjectValue)
        for n in result:
            env.assignVar(statement.variable.symbol, n)
            for i in statement.body:
                result2 = interpreter(i, env)
                if result2 in ["break", "continue"]:
                    break
            if len(statement.body) != 0 and result2 == "break":
                    break
        """
    else:
        env.declareVar(statement.variable.symbol, interpreter(statement.condition.right[0], env), False)
        statement.condition.right = statement.condition.right[1]
        while interpreter(statement.condition, env).value == "true": #env.variables[statement.condition.left.symbol].value <= statement.condition.right.value:
            """if statement.body == []:
                env.variables[statement.condition.left.symbol].value = statement.condition.right.value
                break"""
            for i in statement.body:
                result2 = interpreter(i, env)
                if result2 in ["break", "continue"]:
                    break
            if len(statement.body) != 0 and result2 == "break":
                break
            interpreter(statement.increment, env) #env.variables[statement.condition.left.symbol].value += 1
        env.variables.pop(statement.condition.left.symbol)

def interpret_return_statement(statement: ReturnStatement, env: Environment) -> RuntimeVal:
    from runtime.interpreter import interpreter
    values = [interpreter(arg, env) for arg in statement.arguments] if isinstance(statement.arguments, list) else interpreter(statement.arguments, env)
    return {"kind": "return", "value": values}

def interpret_break_statement(statement: BreakStatement, env: Environment) -> RuntimeVal:
    return "break"

def interpret_continue_statement(statement: ContinueStatement, env: Environment) -> RuntimeVal:
    return "continue"