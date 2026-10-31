from frontend.errorhandler import ErrorHandler

class TokenType:
    Number = "number"
    String = "string"
    Identifier = "identifier"
    Equals = "equals"
    Comma = "comma"
    Dot = "dot"
    Colon = "colon"
    Semicolon = "semicolon"
    OpenParen = "openparen"
    CloseParen = "closeparen"
    OpenBrace = "openbrace"
    CloseBrace = "closebrace"
    OpenBracket = "openbracket"
    CloseBracket = "closebracket"
    BinaryOperator = "binaryoperator"
    Comment = "comment"
    Local = "local"
    If = "if"
    Fn = "function"
    Then = "then"
    End = "end"
    Do = "do"
    In = "in"
    For = "for"
    Return = "return"
    Break = "break"
    Continue = "continue"
    Elseif = "elseif"
    Else = "else"
    And = "and"
    Or = "or"
    Vararg = "vararg"
    Hashtag = "hashtag"
    Not = "not"
    EOF = "EOF"

class Token:
    def __init__(self, type: str, value: TokenType, range: list):
        self.type = type
        self.value = value
        self.range = range

    def __repr__(self):
        return str({"type": self.type, "value": self.value, "range": self.range})

Keywords = {
    "local": TokenType.Local,
    "if": TokenType.If,
    "then": TokenType.Then,
    "end": TokenType.End,
    "do": TokenType.Do,
    "in": TokenType.In,
    "for": TokenType.For,
    "return": TokenType.Return,
    "break": TokenType.Break,
    "continue": TokenType.Continue,
    "elseif": TokenType.Elseif,
    "else": TokenType.Else,
    "and": TokenType.And,
    "or": TokenType.Or,
    "not": TokenType.Not,
    "function": TokenType.Fn
}

def token(type: str, value: TokenType, range: list = []) -> Token:
    return Token(type, value, range)

def isALetter(src: str):
    return src.upper() != src.lower() or src == "_"

def isANumber(string: str):
    return string.isnumeric()

def isskippable(string: str):
    return string in [" ", "\n", "\t", "\r"]

def tokenize(sourceCode: str) -> list[Token]:
    tokens = []
    TokenIndex = [0, 1, []]
    src = ["" for n in range(len(sourceCode))]
    for i in range(len(sourceCode)):
        src[i] = sourceCode[i]

    while (len(src) > 0):
        if (src[0] == "("):
            tokens.append(token(TokenType.OpenParen, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == ")"):
            tokens.append(token(TokenType.CloseParen, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "{"):
            tokens.append(token(TokenType.OpenBrace, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "}"):
            tokens.append(token(TokenType.CloseBrace, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "[" and src[1] == "["):
            string = ""
            stringEnd = False
            src.pop(0)
            src.pop(0)
            while (len(src) > 0 and src[0] + src[1] != ']]'):
                string += src.pop(0)

            if (len(src) > 0 and src[0] + src[1] == ']]'):
                stringEnd = True

            if stringEnd == False:
                ErrorHandler(f"Unfinished string near '\"{string}'", TokenIndex)
            if len(src) != 0:
                src.pop(0)
                src.pop(0)
                    
            TokenIndex[1] += len(string) + 1
            tokens.append(token(TokenType.String, string, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
            TokenIndex[0] = TokenIndex[1] - 1
        elif (src[0] == "["):
            tokens.append(token(TokenType.OpenBracket, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "]"):
            tokens.append(token(TokenType.CloseBracket, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "-" and src[1] == "-"):
            string = ""
            src.pop(0)
            src.pop(0)

            while (len(src) > 0 and src[0] != "\n"):
                string += src.pop(0)

            TokenIndex[1] += len(string) + 1
            tokens.append(token(TokenType.Comment, string, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
            TokenIndex[0] = TokenIndex[1] - 1
        elif (len(src) > 1 and src[0] + src[1] in ["==", ">=", "<=", "!="]):
            TokenIndex[1] += 1
            tokens.append(token(TokenType.BinaryOperator, src.pop(0) + src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
            TokenIndex[0] += 1
        elif (len(src) > 1 and src[0] + src[1] in ["+=", "-=", "*=", "/=", "^="]):
            TokenIndex[1] += 1
            tokens.append(token(TokenType.BinaryOperator, src.pop(0) + src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
            TokenIndex[0] += 1
        elif (src[0] in ["+", "-", "*", "/", "^", "%", "<", ">"]):
            tokens.append(token(TokenType.BinaryOperator, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "#"):
            tokens.append(token(TokenType.Hashtag, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (len(src) > 2 and src[0] + src[1] + src[2] == "..."):
            tokens.append(token(TokenType.Vararg, src.pop(0) + src.pop(0) + src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (len(src) > 1 and src[0] + src[1] == ".."):
            tokens.append(token(TokenType.BinaryOperator, src.pop(0) + src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "="):
            tokens.append(token(TokenType.Equals, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == ";"):
            tokens.append(token(TokenType.Semicolon, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == ":"):
            tokens.append(token(TokenType.Colon, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == ","):
            tokens.append(token(TokenType.Comma, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        elif (src[0] == "."):
            tokens.append(token(TokenType.Dot, src.pop(0), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
        else:
            if (isANumber(src[0])):
                num = ""
                isHex = False
                if (len(src) > 1 and src[0] + src[1] == "0x"):
                    isHex = True
                if isHex == False:
                    while (len(src) > 0 and (isANumber(src[0]) or src[0] == ".")):
                        num += src.pop(0)
                else:
                    while len(src) > 0 and (src[0] == "." or (not isANumber(src[0]) and src[0].lower() in "abcdefghijklmnopqrstuvwxyz") or (isANumber(src[0]) and src[0] in "1234567890")):
                        num += src.pop(0)

                if (len(src) > 0 and src[0] == ";"):
                    src.pop(0)
                elif (len(src) > 0 and not (src[0] in [" ", "\n", ")", "}", ",", "]", "+", "-", "*", "/", "^", "%"])):
                    ErrorHandler("Malformed number", TokenIndex)

                TokenIndex[1] += len(num) - 1
                if isHex:
                    try:
                        tokens.append(token(TokenType.Number, float.fromhex(num), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                    except:
                        ErrorHandler("Malformed number", TokenIndex)
                else:
                    tokens.append(token(TokenType.Number, float(num), [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                TokenIndex[0] = TokenIndex[1] - 1
            elif (isALetter(src[0])):
                ident = ""
                while (len(src) > 0 and (isALetter(src[0]) or isANumber(src[0]))):
                    ident += src.pop(0)

                TokenIndex[1] += len(ident) - 1
                reserved = Keywords.get(ident)
                if reserved:
                    tokens.append(token(reserved, ident, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                else:
                    tokens.append(token(TokenType.Identifier, ident, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                TokenIndex[0] = TokenIndex[1] - 1
            elif (src[0] == '"'):
                string = ""
                stringEnd = False
                src.pop(0)
                while (len(src) > 0 and src[0] != '"' and src[0] != "\n"):
                    string += src.pop(0)

                if (len(src) > 0 and src[0] == '"'):
                    stringEnd = True

                if stringEnd == False:
                    ErrorHandler(f"Unfinished string near '\"{string}'", TokenIndex)
                if len(src) != 0:
                    src.pop(0)
                    
                TokenIndex[1] += len(string) + 1
                tokens.append(token(TokenType.String, string, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                TokenIndex[0] = TokenIndex[1] - 1
            elif (src[0] == "'"):
                string = ""
                stringEnd = False
                src.pop(0)
                while (len(src) > 0 and src[0] != "'" and src[0] != "\n"):
                    string += src.pop(0)

                if (len(src) > 0 and src[0] == "'"):
                    stringEnd = True

                if stringEnd == False:
                    ErrorHandler(f"Unfinished string near '\"{string}'", TokenIndex)
                if len(src) != 0:
                    src.pop(0)
                    
                TokenIndex[1] += len(string) + 1
                tokens.append(token(TokenType.String, string, [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
                TokenIndex[0] = TokenIndex[1] - 1
            elif (isskippable(src[0])):
                if src[0] == "\n":
                    TokenIndex[2].append(TokenIndex[0])
                src.pop(0)
            else:
                ErrorHandler(f"Unexpected character '{src[0]}'", TokenIndex)
            
        TokenIndex[0] += 1
        TokenIndex[1] += 1
            
    tokens.append(Token(TokenType.EOF, "<eof>", [TokenIndex[0], TokenIndex[1], TokenIndex[2]]))
    return tokens