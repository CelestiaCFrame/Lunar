from runtime.values import RuntimeVal, NumberVal, StringVal, VarargVal
from frontend.ast import Stmt
from runtime.environment import Environment
from runtime.interpret.expressions import interpret_identifier, interpret_binary_expr, interpret_assignment, interpret_object_expr, interpret_call_expr, interpret_member_expr, interpret_logical_expr, interpret_unary_expr
from runtime.interpret.statements import interpret_program, interpret_var_declaration, interpret_function_declaration, interpret_if_statement, interpret_for_statement, interpret_return_statement, interpret_break_statement, interpret_continue_statement

def interpreter(astNode: Stmt, env: Environment) -> RuntimeVal:
    if astNode.kind == "NumericLiteral":
        return NumberVal(astNode.value)
    elif astNode.kind == "StringLiteral":
        return StringVal(astNode.value)
    elif astNode.kind == "Comment":
        return StringVal(astNode.value)
    elif astNode.kind == "Identifier":
        return interpret_identifier(astNode, env)
    elif astNode.kind == "ObjectLiteral":
        return interpret_object_expr(astNode, env)
    elif astNode.kind == "CallExpr":
        return interpret_call_expr(astNode, env)
    elif astNode.kind == "AssignmentExpr":
        return interpret_assignment(astNode, env)
    elif astNode.kind == "BinaryExpr":
        return interpret_binary_expr(astNode, env)
    elif astNode.kind == "LogicalExpr":
        return interpret_logical_expr(astNode, env)
    elif astNode.kind == "MemberExpr":
        return interpret_member_expr(astNode, env)
    elif astNode.kind == "Program":
        return interpret_program(astNode, env)
    elif astNode.kind == "VarDeclaration":
        return interpret_var_declaration(astNode, env)
    elif astNode.kind == "FunctionDeclaration":
        return interpret_function_declaration(astNode, env)
    elif astNode.kind == "IfStatement":
        return interpret_if_statement(astNode, env)
    elif astNode.kind == "ForStatement":
        return interpret_for_statement(astNode, env)
    elif astNode.kind == "ReturnStatement":
        return interpret_return_statement(astNode, env)
    elif astNode.kind == "BreakStatement":
        return interpret_break_statement(astNode, env)
    elif astNode.kind == "ContinueStatement":
        return interpret_continue_statement(astNode, env)
    elif astNode.kind == "UnaryExpr":
        return interpret_unary_expr(astNode, env)
    elif astNode.kind == "VarargLiteral":
        return VarargVal(astNode.value)
    else:
        raise Exception(f"This AST Node has not yet been setup for interpretation: {astNode.kind}")