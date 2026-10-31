from frontend.ast import BinaryExpr, Expr, Identifier, NumericLiteral, Program, Stmt, VarDeclaration, AssignmentExpr, ObjectLiteral, Property, CallExpr, MemberExpr, FunctionDeclaration, StringLiteral, Comment, IfStatement, ForStatement, ReturnStatement, BreakStatement, ContinueStatement, IfClause, LogicalExpr, UnaryExpr, VarargLiteral
from frontend.lexer import tokenize, TokenType
from frontend.errorhandler import ErrorHandler

class Parser:
    def __init__(self):
        self.tokens = []
        self.breakStatement = [False, []]
        self.continueStatement = [False, []]

    def not_eof(self) -> bool:
        return self.tokens[0].type != TokenType.EOF
    
    def at(self):
        return self.tokens[0]
    
    def nextToken(self):
        prev = self.tokens.pop(0)
        return prev
    
    def expect(self, type: TokenType, err):
        prev = self.tokens.pop(0)
        if not prev or prev.type != type:
            ErrorHandler(f"{err}", prev.range)

        return prev
    
    def produceAST(self, sourceCode: str, openFile: str) -> Program:
        self.selectedFile = openFile.split("/")[-1]
        self.tokens = tokenize(sourceCode)
        indexLines = self.tokens[-1].range[2]
        program = Program([], [], [0, self.tokens[-1].range[1] - 1])

        while (self.not_eof()):
            currentToken = self.parse_stmt()
            if currentToken:
                if currentToken.kind == "Comment":
                    program.comments.append(currentToken)
                else:
                    program.body.append(currentToken)
        return program, indexLines
    
    def parse_stmt(self) -> Stmt:
        if self.at().type == TokenType.Local:
            return self.parse_var_declaration()
        elif self.at().type == TokenType.Fn:
            return self.parse_fn_declaration()
        elif self.at().type == TokenType.If:
            return self.parse_if_statement()
        elif self.at().type == TokenType.For:
            return self.parse_for_statement()
        elif self.at().value == ")":
            ErrorHandler(f"Expected identifier when parsing expression, got '{self.at().value}'", self.at().range)
        else:
            return self.parse_expr()
    
    def parse_for_statement(self) -> Stmt:
        TokenIndex = self.at().range[0]
        self.nextToken()
        variable = self.parse_args()[0]
        if self.at().value == "in":
            self.nextToken()
            increment = self.parse_expr()
            if not isinstance(increment, CallExpr):
                ErrorHandler(f"Expected 'pairs' near {self.at().value}")
            for i in variable:
                if not (isinstance(i, Identifier)):
                    ErrorHandler(f"Expected 'Identifier' in for statement (got {i.kind})", self.at().range)
        elif self.at().value != "=":
            self.expect(TokenType.Semicolon, "Expected ',' after 'identifier'")
        if (self.at().value == "="):
            self.nextToken()
            variable = variable[0]
            condition = BinaryExpr(variable, self.parse_expr(), "<=", variable.range)
            if len(condition.right) == 2:
                increment = BinaryExpr(variable, NumericLiteral(1, variable.range), "+=", variable.range)
            elif len(condition.right) == 3:
                increment = BinaryExpr(variable, NumericLiteral(condition.right[2].value, variable.range), "+=", variable.range)
            else:
                ErrorHandler(f"Expected 'do' near ','", self.at().range)
        else:
            condition = None
        if self.at().value == "do":
            TokenIndex3 = self.at().range
            self.nextToken()
        else:
            ErrorHandler(f"Expected 'do' (got '{self.at().value}')")
        body = []
        self.breakStatement = [True, TokenIndex3]
        self.continueStatement = [True, TokenIndex3]
        while self.at().type != TokenType.End:
            body.append(self.parse_stmt())
        self.breakStatement = [False, []]
        self.continueStatement = [False, []]
        TokenIndex2 = self.expect(TokenType.End, f"Expected 'end' (to close 'do' at line 1), got <eof>").range[1]
        statement = ForStatement(variable, condition, increment, body, [TokenIndex, TokenIndex2])
        return statement
    
    def parse_if_statement(self) -> Stmt:
        TokenIndex = self.tokens[0].range[0]
        clauses = []

        def checkStatement():
            TokenIndex2 = self.tokens[0].range[0]
            self.nextToken()
            body = []
            condition = self.parse_expr()
            self.expect(TokenType.Then, "Expected 'then' after if statement condition.")
            while (self.not_eof() and not self.at().type in [TokenType.End, TokenType.Elseif, TokenType.Else]):
                body.append(self.parse_expr())

            TokenIndex3 = self.at().range[0] - 1
            clauses.append(IfClause(condition, body, [TokenIndex2, TokenIndex3]))
            if self.at().type == TokenType.Elseif:
                TokenIndex2 = self.at().range[0]
                checkStatement()
            elif self.at().type == TokenType.Else:
                TokenIndex2 = self.at().range[0]
                body = []
                self.nextToken()
                self.expect(TokenType.Then, "Expected 'then' after if statement condition.")
                while (self.not_eof() and not self.at().type in [TokenType.End, TokenType.Elseif, TokenType.Else]):
                    body.append(self.parse_expr())
                clauses.append(IfClause(None, body, [TokenIndex2, self.at().range[0]]))

        checkStatement()
        TokenIndex2 = self.expect(TokenType.End, "Expected 'end' after if statement.").range[1]

        statement = IfStatement(clauses, [TokenIndex, TokenIndex2])
        return statement
    
    def parse_fn_declaration(self) -> Stmt:
        TokenIndex = self.at().range[0]
        self.nextToken()
        if self.at().type == TokenType.Identifier:
            name = self.parse_member_expr()
        else:
            if self.at().type != TokenType.OpenParen:
                ErrorHandler(f"Expected '(' after function keyword (got {self.tokens[1].type})", self.at().range)
            name = None
        args = self.parse_args(True)
        params = []
        for arg in args[0]:
            if arg.kind != "Identifier":
                ErrorHandler("Expected parameters to be of type string inside function.", self.at().range)
            
            params.append(Identifier(arg, arg.range).symbol)

        body = []

        while self.at().type != TokenType.EOF and self.at().type != TokenType.End and self.at().type != TokenType.Return:
            body.append(self.parse_stmt())

        if self.at().type == TokenType.Return:
            TokenIndex2 = self.nextToken().range[0]
            arguments = self.parse_stmt()
            if isinstance(arguments, list):
                body.append(ReturnStatement(arguments, [TokenIndex2, arguments[-1].range[1]]))
            else:
                body.append(ReturnStatement(arguments, [TokenIndex2, arguments.range[1]]))

        TokenIndex2 = self.expect(TokenType.End, "Expected 'end' inside function declaration.").range[1]
        fn = FunctionDeclaration(params, name, body, [TokenIndex, TokenIndex2])
        return fn
        
    def parse_var_declaration(self) -> Stmt:
        TokenIndex = self.at().range[0]
        self.nextToken()
        if self.at().type == TokenType.Fn and self.at().value == "function":
            return self.parse_expr()
        identifier = self.expect(TokenType.Identifier, "Expected identifier name following local keyword.").value

        if self.at().type in [TokenType.Identifier, TokenType.Semicolon]:
            TokenIndex2 = self.at().range[1]
            if self.at().type == TokenType.Semicolon:
                self.nextToken()
            return VarDeclaration(identifier, None, False, [TokenIndex, TokenIndex2])
        
        self.expect(TokenType.Equals, "Expected '=' following identifier in var declaration.")
        value = self.parse_expr()
        
        TokenIndex2 = value.range[1]
        declaration = VarDeclaration(identifier, value, False, [TokenIndex, TokenIndex2])
        return declaration
    
    def parse_expr(self) -> Expr:
        return self.parse_assignment_expr()
    
    def parse_assignment_expr(self) -> Expr:
        print(self.at().type)
        left = self.parse_args()[0]
        if len(left) == 1:
            left = left[0]
        TokenIndex = (left.range[0] if not isinstance(left, list) else left[0].range[0]) if left else 1

        if self.at().type == TokenType.Equals:
            self.nextToken()
            if self.at().type != TokenType.EOF:
                value = self.parse_assignment_expr()
                return AssignmentExpr(left, value, [TokenIndex, value.range[1] if not isinstance(value, list) else value[-1].range[1]])
            else:
                ErrorHandler("Expected identifier after AssignmentExpr", self.at().range)
        elif self.at().value in ["+=", "-=", "*=", "/=", "^=", "%="]:
            operator = self.at().value
            self.nextToken()
            right = self.parse_expr()
            left = BinaryExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )
        
        return left
    
    def parse_object_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        if self.at().type != TokenType.OpenBrace:
            return self.parse_binary_expr()
        
        self.nextToken()
        properties = []

        while (self.not_eof() and self.at().type != TokenType.CloseBrace):
            if self.at().type == TokenType.Identifier:
                key = self.at()
                key.type = "string"
                key.range = [key.range[0], key.range[1]]
            elif self.at().type == TokenType.OpenBracket:
                self.nextToken()
                if self.at().type in [TokenType.String, TokenType.Number]:
                    key = self.at()
                    self.nextToken()
                elif self.at().type == TokenType.Identifier:
                    key = self.parse_expr()
                else:
                    ErrorHandler(f"String, number or identifier expected in table key (got '{self.at().value}')", self.at().range)
                key.range = [key.range[0], key.range[1]]

            if self.tokens[1].type == TokenType.Comma:
                values = self.parse_expr()
                if isinstance(values, list):
                    for value in values:
                        properties.append(Property(None, value, [value.range[0], value.range[1]]))
                else:
                    self.nextToken()
                continue
            elif self.tokens[1].type == TokenType.CloseBrace:
                value = self.parse_expr()
                properties.append(Property(None, value, [value.range[0], value.range[1]]))
                continue
            
            self.nextToken()
            self.expect(TokenType.Equals, "Missing '=' following identifier in ObjectExpr")
            value = self.parse_object_expr()

            properties.append(Property(key, value, [key.range[0], value.range[1]]))
            if self.at().type != TokenType.CloseBrace:
                self.expect(TokenType.Comma, "Expected ',' or '}' following property")
        TokenIndex2 = self.expect(TokenType.CloseBrace, "Object literal missing '}'").range[1]
        return ObjectLiteral(properties, [TokenIndex, TokenIndex2])
    
    def parse_binary_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        left = self.parse_additive_expr()

        while (self.at().value in ["..", "==", "!="]):
            operator = self.nextToken().value
            right = self.parse_additive_expr()
            left = BinaryExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )

        return left

    def parse_additive_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        left = self.parse_multiplicative_expr()

        while (self.at().value in ["+", "-"]):
            operator = self.nextToken().value
            right = self.parse_multiplicative_expr()
            left = BinaryExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )

        return left
    
    def parse_multiplicative_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        left = self.parse_exponential_expr()

        while (self.at().value in ["/", "*", "%"]):
            operator = self.nextToken().value
            right = self.parse_exponential_expr()
            left = BinaryExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )

        return left
    
    def parse_exponential_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        left = self.parse_logical_expr()

        while (self.at().value == "^"):
            operator = self.nextToken().value
            right = self.parse_logical_expr()
            left = BinaryExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )

        return left
    
    def parse_logical_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        left = self.parse_call_member_expr()

        while (self.at().value in ["and", "or"]):
            operator = self.nextToken().value
            right = self.parse_call_member_expr()
            left = LogicalExpr(
                left = left,
                right = right,
                operator = operator,
                range = [TokenIndex, right.range[1]]
            )

        return left
    
    def parse_call_member_expr(self) -> Expr:
        member = self.parse_member_expr()

        if self.at().type == TokenType.OpenParen:
            return self.parse_call_expr(member)
        
        return member

    def parse_call_expr(self, caller: Expr) -> Expr:
        TokenIndex = caller.range[0]
        arguments = self.parse_args(True)
        call_expr: Expr = CallExpr(arguments[0], caller, [TokenIndex, arguments[1]])

        if self.at().type == TokenType.OpenParen:
            call_expr = self.parse_call_expr(call_expr)

        return call_expr

    def parse_args(self, inParen = False) -> list[Expr]:
        if inParen:
            self.expect(TokenType.OpenParen, f"Expected '(' near '{self.at().value}'")
        args = [] if self.at().type == TokenType.CloseParen else self.parse_arguments_list()
        TokenIndex = self.at().range[1]
        if inParen:
            self.expect(TokenType.CloseParen, f"Expected ')' near '{self.at().value}'")
        return args, TokenIndex

    def parse_arguments_list(self) -> list[Expr]:
        args = [self.parse_object_expr()]

        while self.at().type == TokenType.Comma and self.nextToken():
            args.append(self.parse_object_expr())

        return args

    def parse_member_expr(self) -> Expr:
        TokenIndex = self.at().range[0]
        object = self.parse_primary_expr()

        while self.at().type in [TokenType.Dot, TokenType.Colon, TokenType.OpenBracket]:
            operator = self.nextToken()
            property: Expr
            computed: bool

            if operator.type == TokenType.Dot:
                computed = False
                property = self.parse_primary_expr()

                if property.kind != "Identifier":
                    ErrorHandler("Cannot use '.' without right hand side being an identifier.", self.at().range)
                
                TokenIndex2 = property.range[1]
            elif operator.type == TokenType.Colon:
                computed = False
                property = self.parse_primary_expr()

                if property.kind != "Identifier":
                    ErrorHandler("Cannot use ':' without right hand side being an identifier.", self.at().range)
                
                TokenIndex2 = property.range[1]
            else:
                computed = True
                property = self.parse_expr()
                TokenIndex2 = self.at().range[1]
                self.expect(TokenType.CloseBracket, "Missing ']' in computed value.")
            
            object = MemberExpr(object, property, operator.value, computed, [TokenIndex, TokenIndex2])
        return object
    
    def parse_primary_expr(self) -> Expr:
        tk = self.at().type
        TokenRange = [self.at().range[0], self.at().range[1]]
        if tk == TokenType.Identifier:
            return Identifier(self.nextToken().value, TokenRange)
        elif tk == TokenType.Number:
            return NumericLiteral(self.nextToken().value, TokenRange)
        elif tk == TokenType.String:
            return StringLiteral(self.nextToken().value, TokenRange)
        elif tk == TokenType.Comment:
            return Comment(self.nextToken().value, TokenRange)
        elif tk == TokenType.OpenParen:
            self.nextToken()
            left = self.parse_expr()
            right = ""

            while True:
                if (self.at().value in ["and", "or"]):
                    operator = self.at().value
                    self.nextToken()
                    right = self.parse_expr()
                    if (self.at().value in ["and", "or"]):
                        left = LogicalExpr(left, right, operator, [left.range[0], right.range[1]])
                    else:
                        left = LogicalExpr(left, right, operator, [left.range[0], right.range[1]])
                        break
                else:
                    break
                
            self.expect(TokenType.CloseParen, "Unexpected token found inside parenthesed expression")
            return left
        elif tk == TokenType.Return:
            self.nextToken()
            value = self.parse_expr()
            return ReturnStatement(value, [TokenRange[0], value.range[1]])
        elif tk == TokenType.Break:
            if self.breakStatement[0]:
                self.nextToken()
                return BreakStatement(TokenRange)
            elif self.breakStatement[0] == None:
                ErrorHandler(f"Expected 'end' (to close 'do' at line 1), got 'break'", self.at().range)
        elif tk == TokenType.Continue:
            self.nextToken()
            return ContinueStatement(TokenRange)
        elif tk == TokenType.Fn:
            return self.parse_stmt()
        elif tk == TokenType.Hashtag:
            currentTokenRange = self.at().range[0]
            self.nextToken()
            value = self.parse_expr()
            return UnaryExpr(value, "#", [currentTokenRange, value.range[1]])
        elif tk == TokenType.Not:
            currentTokenRange = self.at().range[0]
            self.nextToken()
            value = self.parse_expr()
            return UnaryExpr(value, "not", [currentTokenRange, value.range[1]])
        elif tk == TokenType.Vararg:
            currentToken = self.at()
            self.nextToken()
            return VarargLiteral(currentToken.range)
        elif self.at().value == "-":
            currentTokenRange = self.at().range[0]
            self.nextToken()
            value = self.parse_expr()
            return UnaryExpr(value, "-", [currentTokenRange, value.range[1]])
        else:
            ErrorHandler(f"Expected identifier when parsing expression, got '{self.at().value}'", self.at().range)