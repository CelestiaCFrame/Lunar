from runtime.values import RuntimeVal, BoolVal, NilVal, NativeFnValue, NumberVal, ObjectVal, StringVal, FunctionValue
from frontend.ast import MemberExpr, CallExpr, FunctionDeclaration
from frontend.lexer import token
from frontend.errorhandler import ErrorHandler

class Environment:
    def __init__(self, parentENV: "Environment" = None, selectedFile: str = ""):
        global_ = True if parentENV else False
        self.parent = parentENV
        self.variables = {}
        self.constants = {}
        self.indexLines = {}
        self.selectedFile = selectedFile
        self.timeStarted = 0

    def declareVar(self, varName: str, value: RuntimeVal, constant: bool) -> RuntimeVal:
        if varName in self.constants:
            ErrorHandler(f"Cannot reassign to {varName}, as it was a declared constant.", None)
        self.variables[varName] = value
        if constant:
            self.constants[varName] = value
        return value
    
    def assignVar(self, varName: str, value: RuntimeVal) -> RuntimeVal:
        env = self.resolve(varName)
        if varName in env.constants:
            ErrorHandler(f"Cannot reassign to {varName}, as it was a declared constant.", None)
        env.variables[varName] = value
        return value
    
    def changeVarValue(self, varName: list, value: RuntimeVal, value2: RuntimeVal) -> RuntimeVal:
        env = self.resolve(varName[0])
        result = env.variables[varName[0]]
        if isinstance(value, FunctionValue) and value.name == None:
            value.name = varName[-1]
        index = 1
        while index < len(varName) - 1:
            if isinstance(result, dict):
                if len(result) == 0:
                    ErrorHandler(f"Attempt to index a nil value", value2.range)
                for i in result:
                    if i.value == varName[index]:
                        result = result.get(i)
                        index += 1
                        break
            else:
                result = result.properties
                
        if isinstance(result, ObjectVal):
            if result.isfrozen:
                ErrorHandler(f"Attempt to modify a readonly table", value2.range)
            result = result.properties
        else:
            ErrorHandler(f"Attempt to index a '{result.type}' value", value2.range)
        
        if len(result) == 0:
            if isinstance(varName[-1], int):
                result[NumberVal(varName[-1])] = value
            else:
                result[StringVal(varName[-1])] = value
        else:
            for i in result:
                if i.value == varName[-1]:
                    result[i] = value
                    return value
            if isinstance(varName[-1], int):
                result[NumberVal(int(varName[-1]))] = value
            else:
                result[StringVal(varName[-1])] = value
        return value
    
    def lookupVar(self, varName: str) -> RuntimeVal:
        env = self.resolve(varName)
        return env.variables[varName]

    def resolve(self, varName: str) -> "Environment":
        if varName in self.variables:
            return self
        
        if self.parent == None:
            self.variables[varName] = NilVal()
            return self
        
        return self.parent.resolve(varName)
    
    def __repr__(self):
        return str(self.__dict__)
    
def createGlobalEnv(selectedFile):
    import random
    import math
    import time
    import re
    import struct
    from runtime.interpreter import interpreter
    env = Environment(selectedFile = selectedFile)
    env.timeStarted = time.time()

    def checkIntAndFloat(n):
        result = (float(int(n.value)) == float(n.value)) if n.value != float("inf") else False
        if result == True:
            return int(n.value)
        return False

    def changeToParserType(v):
        if isinstance(v, int):
            return NumberVal(v)
        elif isinstance(v, str):
            return StringVal(v)
        elif isinstance(v, dict):
            return ObjectVal(v, False)

    class LuaGlobals:
        _G = ObjectVal({})
        _VERSION = StringVal("Luau")
        _ENV = ObjectVal(env)

        def printFunction(*args: list, env: Environment):
            def printFunction2(arg: RuntimeVal, env: Environment):
                if isinstance(arg, NumberVal):
                    if str(arg.value) == "nan":
                        print("-nan", end=" ")
                    elif checkIntAndFloat(arg):
                        print(int(arg.value), end=" ")
                    else:
                        print(arg.value, end=" ")
                elif isinstance(arg, StringVal) or isinstance(arg, BoolVal) or isinstance(arg, NilVal):
                    print(arg.value, end=" ")
                elif isinstance(arg, ObjectVal):
                    def ObjectValueToDict(n):
                        table = "{"
                        indexValue = 1
                        for i in n.properties:
                            if isinstance(n.properties[i], ObjectVal):
                                table = table + f'["{i.value}"] = ' + ObjectValueToDict(n.properties[i])
                            else:
                                if (isinstance(n.properties[i], FunctionValue) or isinstance(n.properties[i], NativeFnValue)):
                                    table = table + f'["{i.value}"] = ' + "function: " + i.value
                                else:
                                    indexValue2 = checkIntAndFloat(i)
                                    if indexValue2 == False:
                                        indexValue2 = i.value
                                    if indexValue == len(n.properties):
                                        if (isinstance(i, StringVal)):
                                            if (isinstance(n.properties[i], StringVal)):
                                                table = table + f'["{indexValue2}"] = ' + f'"{n.properties[i].value}"'
                                            else:
                                                table = table + f'["{indexValue2}"] = ' + f'{n.properties[i].value}'
                                        else:
                                            if (isinstance(n.properties[i], StringVal)):
                                                table = table + f'[{indexValue2}] = ' + f'"{n.properties[i].value}"'
                                            else:
                                                table = table + f'[{indexValue2}] = ' + f'{n.properties[i].value}'
                                    else:
                                        if (isinstance(i, StringVal)):
                                            if (isinstance(n.properties[i], StringVal)):
                                                table = table + f'["{indexValue2}"] = ' + f'"{n.properties[i].value}", '
                                            else:
                                                table = table + f'["{indexValue2}"] = ' + f'{n.properties[i].value}, '
                                        else:
                                            if (isinstance(n.properties[i], StringVal)):
                                                table = table + f'[{indexValue2}] = ' + f'"{n.properties[i].value}", '
                                            else:
                                                table = table + f'[{indexValue2}] = ' + f'{n.properties[i].value}, '
                            indexValue += 1
                        var = table + "}"
                        string = ""
                        stack = 0
                        var2 = 0
                        skip = 0
                        for i in var:
                            if skip > 0:
                                skip -= 1
                                var2 += 1
                                continue
                            if i == "{":
                                if var[var2 + 1] != "}":
                                    stack += 1
                                    string = string + "{\n" + ("   " * stack)
                                else:
                                    string = string + i
                            elif i == "}":
                                if var[var2 - 1] != "{":
                                    stack -= 1
                                    string = string + "\n" + ("   " * stack) + "}"
                                else:
                                    string = string + i
                            elif i == ",":
                                skip += 1
                                string = string + ",\n" + ("   " * stack)
                            elif i == "\n":
                                continue
                            else:
                                string = string + i

                            var2 += 1
                        return string
                    print(ObjectValueToDict(arg), end=" ")
                elif isinstance(arg, FunctionValue):
                    if isinstance(arg.name, MemberExpr):
                        print("function: " + arg.name.property.symbol, end=" ")
                    else:
                        print("function: " + arg.name, end=" ")
                elif isinstance(arg, NativeFnValue):
                    print(f"function: {arg.call.__name__}", end=" ")
                else:
                    raise Exception(f"An unexpected error occured during interpreting: {arg}")
            
            for arg in args:
                if isinstance(arg, tuple):
                    for i in arg:
                        printFunction2(i, env)
                else:
                    printFunction2(arg, env)
            print("")
            return NilVal()
    
        def timeFunction(env: Environment):
            return NumberVal(time.time() - env.timeStarted)
        
        def assertFunction(value = NilVal(), errorMessage = NilVal(), env = NilVal()):
            if errorMessage.type == "nil":
                errorMessage = "assertion failed!"
            else:
                errorMessage = errorMessage.value
            if value.value == "false":
                raise Exception(errorMessage)

        def errorFunction(message = NilVal(), level = NilVal(), env = NilVal()):
            raise Exception(message.value)

        def getmetatableFunction(t = NilVal(), env = NilVal()):
            print("Not yet implemented")

        def ipairs(t = NilVal(), env = NilVal()):
            assert t.type == "nil", f"Invalid argument #1 to 'ipairs' (expected table, got {t.type})"
            index = 1
            for value in t.properties:
                yield NumberVal(index), value
                index += 1

        def loadstring(contents = NilVal(), chunkname = NilVal(), env = NilVal()):
            from frontend.parser import Parser
            env2 = createGlobalEnv(env.selectedFile)
            parser2 = Parser()
            program, indexLines = parser2.produceAST(contents.value, env.selectedFile)
            env2.indexLines = indexLines
            interpreter(program, env2)

        def next(t = NilVal(), lastKey = NilVal(), env = NilVal()):
            assert t.type == "table", f"Invalid argument #1 to 'next' (expected table, got {t.type})"
            keys = []
            for k in t.properties:
                keys.append(k)

            keys = sorted(keys, key=lambda x: x.value)

            if lastKey.type == "nil":
                return NumberVal(keys[0].value), t.properties[keys[0]]
            
            if lastKey.value == keys[-1].value:
                return NilVal(), NilVal()
            
            for i in range(0, len(keys)):
                if keys[i].value == lastKey.value:
                    return NumberVal(keys[i + 1].value), t.properties[keys[i + 1]]
                
            raise Exception(f"Invalid key to 'next'")
            """
            keys = list(t.properties.keys())
            if lastKey.type == "nil":
                if keys:
                    return NumberVal(keys[0].value), t.properties[keys[0]]
                else:
                    return NilVal(), NilVal()
            else:
                for i in range(len(keys)):
                    if keys[i].value == lastKey.value:
                        if i + 1 >= len(keys):
                            return NumberVal(keys[0].value), t.properties[keys[0]]
                        if keys[i + 1].value == lastKey.value + 1:
                            return NumberVal(keys[i + 1].value), t.properties[keys[i + 1]]
                        else:
                            return NilVal(), NilVal()
                raise Exception(f"Invalid key to 'next'")
            """

        def pairs(t = NilVal(), env = NilVal()):
            assert t.type == "table", f"Invalid argument #1 to 'pairs' (expected table, got {t.type})"
            return NativeFnValue(LuaGlobals.next), t, NilVal()

        def pcall(func = NilVal(), *args, env = NilVal()):
            assert func.type != "nil", f"Missing argument #1"
            try:
                interpreter(CallExpr(args, FunctionDeclaration(func.parameters, func.name, func.body, func.range), func.range), env)
                return BoolVal(True)
            except Exception as ErrorMessage:
                return BoolVal(False), ErrorMessage

        def rawequal(v1 = NilVal(), v2 = NilVal(), env = NilVal()):
            assert v1.type != "nil", f"Missing argument #1"
            assert v2.type != "nil", f"Missing argument #2"
            return v1.value == v2.value

        def rawget(t = NilVal(), index = NilVal(), env = NilVal()):
            assert t.type == "table", f"Invalid argument #1 to 'rawget' (table expected, got {t.type})"
            assert index.type != "nil", "Missing argument #2"
            for i in t.properties:
                if i.value == index.value:
                    return t.properties[i].value

        def rawlen(t = NilVal(), env = NilVal()):
            assert t.type == "table" or t.type == "string", "Invalid argument #1 to 'rawlen' (table or string expected)"
            return NumberVal(len(t.properties)) if t.type == "table" else NumberVal(len(t.value))

        def rawset(t = NilVal(), index = NilVal(), value = NilVal(), env = NilVal()):
            assert t.type == "table", "Missing argument #1 to 'rawset' (table expected)"
            assert index.type != "nil", "Missing argument #2"
            assert value.type != "nil", "Missing argument #3"
            t.properties[index] = value

        def select(index = NilVal(), *args, env = NilVal()):
            if index.value == "#":
                return NumberVal(len(args))
            else:
                result = []
                index.value = int(index.value)
                for i in range(index.value - 1, len(args)):
                    result.append(args[i])
                return tuple(result)

        def setmetatable(t = NilVal(), newMeta = NilVal(), env = NilVal()):
            assert t.type == "table", f"Invalid argument #1 to 'setmetatable' (expected table, got {t.type})"
            print("Not yet implemented")

        def tonumber(arg = NilVal(), base = NilVal(), env = NilVal()):
            assert arg.type == "string", f"Invalid argument #1 to 'tonumber' (expected string, got {arg.type})"
            try:
                if arg.value[0:2] == "0x" and base.type == "nil":
                    return NumberVal(float.fromhex(arg.value))
                if base.type != "nil":
                    return NumberVal(float(arg.value))
                base = 10
                return NumberVal(float(arg.value))
            except Exception as e:
                return NilVal()

        def tostring(e = NilVal(), env = NilVal()):
            if e.type == "table":
                return StringVal(f"table")
            elif e.type == "function":
                return StringVal(f"function")
            else:
                if checkIntAndFloat(e):
                    return StringVal(str(int(e.value)))
                else:
                    return StringVal(str(e.value))

        def type(v = NilVal(), env = NilVal()):
            return StringVal(v.type)

        def unpack(list = NilVal(), i = NilVal(), j = NilVal(), env = NilVal()):
            assert list.type == "table", f"Attempt to index a {list.type}"
            newList = ObjectVal({k: list.properties[k] for k in list.properties})
            if i.type != "nil":
                assert i.type == "number", f"Invalid argument #2 to 'unpack' (expected number, got {i.type})"
            if j.type != "nil":
                assert i.type == "number", f"Invalid argument #3 to 'unpack' (expected number, got {i.type})"
            newList.properties = (newList.properties[i.value:j.value + 1]) if i.type != "nil" else newList.properties
            newList.properties = [newList.properties[value] for value in newList.properties]
            return tuple(newList.properties)

        def xpcall(f = NilVal(), err = NilVal(), *args, env = NilVal()):
            try:
                interpreter(CallExpr(args, FunctionDeclaration(f.parameters, f.name, f.body, f.range), f.range), env)
                return BoolVal(True)
            except:
                return BoolVal(False), err.value
        
        def elapsedTime(env):
            return NumberVal(time.time() - env.timeStarted)

        def require(module = NilVal(), env = NilVal()):
            print("Not yet implemented")
            return NilVal()

        def tick(env):
            return NumberVal(time.time())

        def typeof(object = NilVal(), env = NilVal()):
            return StringVal(object.type)

        def version(env):
            return LuaGlobals._VERSION

        def warn(*params, env):
            LuaGlobals.printFunction(params, env=env)
    
    class tableLibrary:
        def insert(t = NilVal(), value = NilVal(), env: Environment = NilVal()):
            t.properties[NumberVal(len(t.properties) + 1)] = value

        def clear(table = NilVal(), env: Environment = NilVal()):
            table.properties = {}

        def clone(t = NilVal(), env = NilVal()):
            result = ObjectVal({})
            for k in t.properties:
                result.properties[k] = t.properties[k]
            return result

        def concat(t = NilVal(), sep = NilVal(), i = NilVal(), j = NilVal(), env = NilVal()):
            result = ""
            sep = "" if sep.type == "nil" else sep.value
            i = 1 if i.type == "nil" else i.value
            j = len(t.properties) if j.type == "nil" else j.value
            for k in range(i, j + 1):
                for k2 in t.properties:
                    if checkIntAndFloat(k2):
                        k2.value = int(k2.value)
                    if k2.value == k:
                        result = result + sep + t.properties[k2].value
                        break
                else:
                    break
            return result

        def create(count = NilVal(), value = NilVal(), env = NilVal()):
            return ObjectVal({NumberVal(k + 1): value for k in range(checkIntAndFloat(count))})

        def find(haystack = NilVal(), needle = NilVal(), init = NilVal(), env = NilVal()):
            result = 0
            init = 1 if init.type == "nil" else init.value
            for i in range(init, len(haystack.properties) + 1):
                if haystack.get(i).value == needle.value:
                    return NumberVal(i)
            return BoolVal(False)

        def foreach(t = NilVal(), f = NilVal(), env = NilVal()):
            for i in t.properties:
                interpreter(CallExpr([i, t.properties[i]], FunctionDeclaration(f.parameters, f.name, f.body, f.range), f.range), env)

        def foreachi(t = NilVal(), f = NilVal(), env = NilVal()):
            for i in range(1, len(t.properties) + 1):
                value = t.get(i)
                if value.type != "nil":
                    interpreter(CallExpr([NumberVal(i), value], FunctionDeclaration(f.parameters, f.name, f.body, f.range), f.range), env)

        def freeze(t = NilVal(), env = NilVal()):
            if t.isfrozen:
                raise Exception("Invalid argument #1 to 'freeze' (table is already frozen)")
            t.isfrozen = True

        def getn(t = NilVal(), env = NilVal()):
            return NumberVal(len(t.properties))

        def isfrozen(t = NilVal(), env = NilVal()):
            return BoolVal(True) if t.isfrozen else BoolVal(False)

        def maxn(t = NilVal(), env = NilVal()):
            result = 0
            for i in t.properties:
                if i.value > result:
                    result = i.value
            return result

        def move(src = NilVal(), a = NilVal(), b = NilVal(), t = NilVal(), dst = NilVal(), env = NilVal()):
            result = ObjectVal({})
            for i in range(a.value, b.value):
                result.properties[len(result.properties) + dst.value] = t.properties[i]
            return result

        def pack(*values, env):
            return ObjectVal({NumberVal(k + 1): values[k] for k in range(len(values))})

        def remove(t = NilVal(), pos = NilVal(), env = NilVal()):
            for i in t.properties:
                if i.value == pos.value:
                    t.properties.pop(i)
                    break

        def sort(t = NilVal(), comp = NilVal(), env = NilVal()):
            return sorted(t.properties, key=comp.value)

        def unpack(list = NilVal(), i = NilVal(), j = NilVal(), env = NilVal()):
            i = 1 if i.type == "nil" else i.value
            j = len(list.properties) if j.type == "nil" else j.value
            result = []
            for index in list.properties:
                if index.value >= i and index.value <= j:
                    result.append(list.properties[index])
            return tuple(result)

    class stringLibrary:
        def sub(s = NilVal(), i = NilVal(), j = NilVal(), env = NilVal()):
            assert s.type == "string", f"Invalid argument #1 to 'sub' (expected string, got {s.type})"
            assert i.type == "number", f"Invalid argument #2 to 'sub' (expected number, got {i.type})"
            assert j.type == "number", f"Invalid argument #3 to 'sub' (expected number, got {j.type})"
            assert checkIntAndFloat(i), "Invalid argument #2 to 'sub' (number is not an integer)"
            assert checkIntAndFloat(j), "Invalid argument #3 to 'sub' (number is not an integer)"
            i = int(i.value)
            j = int(j.value)
            return StringVal(s.value[i:j + 1])

        def find(s = NilVal(), pattern = NilVal(), init = NilVal(), plain = NilVal(), env = NilVal()):
            if init.type != "nil":
                assert checkIntAndFloat(init), "Invalid argument #3 to 'find' (number is not an integer)"
                init = int(init.value) - 1
            else:
                init = 0
            if plain.type != "nil" and plain.value != "false":
                pos = s.value.find(pattern.value, init)
                return (NumberVal(pos + 1), pos + len(pattern.value)) if pos != -1 else NilVal()
            else:
                regex = re.compile(pattern.value)
                match = regex.search(s.value, init)
                return (NumberVal(match.start() + 1), NumberVal(match.end())) if match else NilVal()

        def gmatch(s = NilVal(), pattern = NilVal(), env = NilVal()):
            regex = re.compile(pattern.value)
            matches = regex.finditer(s.value)
            for match in matches:
                yield match.group()

        def len(s = NilVal(), env = NilVal()):
            return NumberVal(len(s.value))

        def rep(s = NilVal(), n = NilVal(), env = NilVal()):
            assert checkIntAndFloat(n), f"Invalid argument #2 to 'rep' (number is not an int)"
            return StringVal(s.value * int(n.value))

        def byte(s = NilVal(), i = NilVal(), j = NilVal(), env = NilVal()):
            if i.type == "nil":
                i = 1
                j = 1
            else:
                assert float(int(i.value)) == float(i.value), f"Invalid argument #1 to 'byte' (number is not an integer)"
                i = int(i.value)
                if j.type == "nil":
                    j = i
                else:
                    assert float(int(j.value)) == float(j.value), f"Invalid argument #2 to 'byte' (number is not an integer)"
                    j = int(j.value)
            substring = s.value[i - 1:j]
            ascii_values = tuple(StringVal(ord(char)) for char in substring)
            return ascii_values

        def gsub(s = NilVal(), pattern = NilVal(), replacement = NilVal(), replacements = NilVal(), env = NilVal()):
            if replacements:
                return re.sub(pattern.value, replacement.value, s.value, count=replacements.value)
            else:
                return re.sub(pattern.value, replacement.value, s.value)

        def pack(format = NilVal(), *string, env = NilVal()):
            result = struct.pack(format.value, *string.value)
            return result

        def lower(s = NilVal(), env = NilVal()):
            return StringVal(s.value.lower())

        def match(s = NilVal(), pattern = NilVal(), init = NilVal(), env = NilVal()):
            if init.type == "nil":
                init = 1
            else:
                init = init.value

            regex = re.compile(pattern.value)
            match = regex.search(s, init - 1)
            return match.group() if match else NilVal()

        def split(s = NilVal(), separator = NilVal(), env = NilVal()):
            return s.split(separator.value)

        def upper(s = NilVal(), env = NilVal()):
            return StringVal(s.value.upper())

        def format(formatstring = NilVal(), *values, env = NilVal()):
            return formatstring.value % values.value

        def unpack(format = NilVal(), data = NilVal(), readStart = NilVal(), env = NilVal()):
            if readStart == None:
                readStart = 0
            else:
                readStart = readStart.value
            return struct.unpack_from(format.value, data.value, readStart)

        def reverse(s = NilVal(), env = NilVal()):
            return StringVal(s.value[::-1])

        def packsize(format = NilVal(), env = NilVal()):
            return struct.calcsize(format)

        def char(*values, env = NilVal()):
            result = []
            for i in range(len(values)):
                assert checkIntAndFloat(values[i]), f"Invalid argument #{i + 1} to 'char' (number is not an integer)"
                result.append(chr(int(values[i].value)))
            return StringVal("".join(result))

    class mathLibrary:
        def abs(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'abs' (expected number, got {x.type})"
            try:
                return NumberVal(abs(x.value))
            except:
                return NumberVal("nan")

        def acos(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'acos' (expected number, got {x.type})"
            try:
                return NumberVal(math.acos(x.value))
            except:
                return NumberVal("nan")

        def asin(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'asin' (expected number, got {x.type})"
            return NumberVal(math.asin(x.value))

        def atan(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'atan' (expected number, got {x.type})"
            return NumberVal(math.atan(x.value))

        def atan2(y = NilVal(), x = NilVal(), env = NilVal()):
            assert y.type == "number", f"Invalid argument #1 to 'atan2' (expected number, got {y.type})"
            assert x.type == "number", f"Invalid argument #2 to 'atan2' (expected number, got {x.type})"
            return NumberVal(math.atan2(y.value, x.value))

        def ceil(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'ceil' (expected number, got {x.type})"
            return NumberVal(math.ceil(x.value))

        def clamp(x = NilVal(), min_value = NilVal(), max_value = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'clamp' (expected number, got {x.type})"
            assert min_value.type == "number", f"Invalid argument #2 to 'clamp' (expected number, got {min_value.type})"
            assert max_value.type == "number", f"Invalid argument #3 to 'clamp' (expected number, got {max_value.type})"
            return NumberVal(max(min(x.value, max_value.value), min_value.value))

        def cos(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'cos' (expected number, got {x.type})"
            return NumberVal(math.cos(x.value))

        def cosh(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'cosh' (expected number, got {x.type})"
            return NumberVal(math.cosh(x.value))

        def deg(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'deg' (expected number, got {x.type})"
            return NumberVal(math.degrees(x.value))

        def exp(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'exp' (expected number, got {x.type})"
            return NumberVal(math.exp(x.value))

        def floor(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'floor' (expected number, got {x.type})"
            return NumberVal(math.floor(x.value))

        def fmod(x = NilVal(), y = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'fmod' (expected number, got {x.type})"
            assert y.type == "number", f"Invalid argument #2 to 'fmod' (expected number, got {y.type})"
            return NumberVal(math.fmod(x.value, y.value))

        def frexp(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'frexp' (expected number, got {x.type})"
            return NumberVal(math.frexp(x.value))

        def ldexp(x = NilVal(), e = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'ldexp' (expected number, got {x.type})"
            assert e.type == "number", f"Invalid argument #2 to 'ldexp' (expected number, got {e.type})"
            if checkIntAndFloat(e):
                e = int(e.value)
            else:
                e = e.value
            if e == 1:
                return NumberVal("inf")
            return NumberVal(math.ldexp(x.value, e))

        def log(x = NilVal(), base = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'log' (expected number, got {x.type})"
            assert base.type == "number", f"Invalid argument #2 to 'log' (expected number, got {base.type})"
            if base.value == 1 and x.value > 1:
                return NumberVal(float("inf"))
            elif base.value == 1 and x.value == 1:
                return NumberVal(-math.nan)
            elif base.value == 1 and x.value < 0:
                return NumberVal(-math.nan)
            elif base.value == 1 and x.value < 1:
                return NumberVal(-math.inf)
            elif base.value == 0 and x.value > 0:
                return NumberVal(0)
            elif base.value == 0 and x.value <= 0:
                return NumberVal(-math.nan)
            elif base.value < 0:
                return NumberVal(-math.nan)
            return NumberVal(math.log(x.value, base.value))

        def log10(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'log10' (expected number, got {x.type})"
            return NumberVal(math.log10(x.value))

        def max(x = NilVal(), *values, env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'max' (expected number, got {x.type})"
            assert len(values) != 0, "Invalid argument #2 to 'max' (expected number, got nil)"
            result = x.value
            for i in values:
                result = max(result, i.value)
            return NumberVal(result)

        def min(x = NilVal(), *values, env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'min' (expected number, got {x.type})"
            assert len(values) != 0, "Invalid argument #2 to 'min' (expected number, got nil)"
            result = x.value
            for i in values:
                result = min(result, i.value)
            return NumberVal(result)

        def modf(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'modf' (expected number, got {x.type})"
            result = math.modf(x.value)
            return (NumberVal(result[1]), NumberVal(result[0]))

        def pow(x = NilVal(), y = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'pow' (expected number, got {x.type})"
            assert y.type == "number", f"Invalid argument #2 to 'pow' (expected number, got {y.type})"
            return NumberVal(math.pow(x.value, y.value))

        def rad(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'rad' (expected number, got {x.type})"
            return NumberVal(math.radians(x.value))

        def random(m = NilVal(), n = NilVal(), env = NilVal()):
            assert m.type == "number", f"Invalid argument #1 to 'random' (expected number, got {m.type})"
            assert n.type == "number", f"Invalid argument #2 to 'random' (expected number, got {n.type})"
            return NumberVal(random.randint(m.value, n.value))

        def randomseed(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'randomseed' (expected number, got {x.type})"
            return NumberVal(random.seed(x.value))

        def round(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'round' (expected number, got {x.type})"
            return NumberVal(round(x.value))

        def sign(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'sign' (expected number, got {x.type})"
            if x.value < 0:
                return NumberVal(-1)
            elif x.value > 0:
                return NumberVal(1)
            else:
                return NumberVal(0)

        def sin(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'sin' (expected number, got {x.type})"
            return NumberVal(math.sin(x.value))

        def sinh(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'sinh' (expected number, got {x.type})"
            return NumberVal(math.sinh(x.value))

        def sqrt(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'sqrt' (expected number, got {x.type})"
            return NumberVal(math.sqrt(x.value))

        def tan(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'tan' (expected number, got {x.type})"
            return NumberVal(math.tan(x.value))

        def tanh(x = NilVal(), env = NilVal()):
            assert x.type == "number", f"Invalid argument #1 to 'tanh' (expected number, got {x.type})"
            return NumberVal(math.tanh(x.value))

        huge = NumberVal(float("inf"))

        pi = NumberVal(math.pi)
    
    env.declareVar("true", BoolVal(True), True)
    env.declareVar("false", BoolVal(False), True)
    env.declareVar("nil", NilVal(), True)
    env.declareVar("_G", LuaGlobals._G, True)
    env.declareVar("_VERSION", LuaGlobals._VERSION, True)
    env.declareVar("_ENV", LuaGlobals._ENV, True)
    env.declareVar("print", NativeFnValue(LuaGlobals.printFunction), False)
    env.declareVar("time", NativeFnValue(LuaGlobals.timeFunction), False)
    env.declareVar("assert", NativeFnValue(LuaGlobals.assertFunction), False)
    env.declareVar("elapsedTime", NativeFnValue(LuaGlobals.elapsedTime), False)
    env.declareVar("error", NativeFnValue(LuaGlobals.errorFunction), False)
    env.declareVar("getmetatable", NativeFnValue(LuaGlobals.getmetatableFunction), False)
    env.declareVar("ipairs", NativeFnValue(LuaGlobals.ipairs), False)
    env.declareVar("loadstring", NativeFnValue(LuaGlobals.loadstring), False)
    env.declareVar("next", NativeFnValue(LuaGlobals.next), False)
    env.declareVar("pairs", NativeFnValue(LuaGlobals.pairs), False)
    env.declareVar("pcall", NativeFnValue(LuaGlobals.pcall), False)
    env.declareVar("rawequal", NativeFnValue(LuaGlobals.rawequal), False)
    env.declareVar("rawget", NativeFnValue(LuaGlobals.rawget), False)
    env.declareVar("rawlen", NativeFnValue(LuaGlobals.rawlen), False)
    env.declareVar("rawset", NativeFnValue(LuaGlobals.rawset), False)
    env.declareVar("require", NativeFnValue(LuaGlobals.require), False)
    env.declareVar("setmetatable", NativeFnValue(LuaGlobals.setmetatable), False)
    env.declareVar("tick", NativeFnValue(LuaGlobals.tick), False)
    env.declareVar("select", NativeFnValue(LuaGlobals.select), False)
    env.declareVar("tonumber", NativeFnValue(LuaGlobals.tonumber), False)
    env.declareVar("tostring", NativeFnValue(LuaGlobals.tostring), False)
    env.declareVar("type", NativeFnValue(LuaGlobals.type), False)
    env.declareVar("unpack", NativeFnValue(LuaGlobals.unpack), False)
    env.declareVar("version", NativeFnValue(LuaGlobals.version), False)
    env.declareVar("typeof", NativeFnValue(LuaGlobals.typeof), False)
    env.declareVar("xpcall", NativeFnValue(LuaGlobals.xpcall), False)
    env.declareVar("warn", NativeFnValue(LuaGlobals.warn), False)
    env.declareVar("math", ObjectVal({
        token("identifier", "abs"): NativeFnValue(mathLibrary.abs),
        token("identifier", "acos"): NativeFnValue(mathLibrary.acos),
        token("identifier", "asin"): NativeFnValue(mathLibrary.asin),
        token("identifier", "atan"): NativeFnValue(mathLibrary.atan),
        token("identifier", "atan2"): NativeFnValue(mathLibrary.atan2),
        token("identifier", "ceil"): NativeFnValue(mathLibrary.ceil),
        token("identifier", "clamp"): NativeFnValue(mathLibrary.clamp),
        token("identifier", "cos"): NativeFnValue(mathLibrary.cos),
        token("identifier", "cosh"): NativeFnValue(mathLibrary.cosh),
        token("identifier", "deg"): NativeFnValue(mathLibrary.deg),
        token("identifier", "exp"): NativeFnValue(mathLibrary.exp),
        token("identifier", "floor"): NativeFnValue(mathLibrary.floor),
        token("identifier", "fmod"): NativeFnValue(mathLibrary.fmod),
        token("identifier", "frexp"): NativeFnValue(mathLibrary.frexp),
        token("identifier", "ldexp"): NativeFnValue(mathLibrary.ldexp),
        token("identifier", "log"): NativeFnValue(mathLibrary.log),
        token("identifier", "log10"): NativeFnValue(mathLibrary.log10),
        token("identifier", "max"): NativeFnValue(mathLibrary.max),
        token("identifier", "min"): NativeFnValue(mathLibrary.min),
        token("identifier", "modf"): NativeFnValue(mathLibrary.modf),
        token("identifier", "pow"): NativeFnValue(mathLibrary.pow),
        token("identifier", "rad"): NativeFnValue(mathLibrary.rad),
        token("identifier", "random"): NativeFnValue(mathLibrary.random),
        token("identifier", "randomseed"): NativeFnValue(mathLibrary.randomseed),
        token("identifier", "round"): NativeFnValue(mathLibrary.round),
        token("identifier", "sign"): NativeFnValue(mathLibrary.sign),
        token("identifier", "sin"): NativeFnValue(mathLibrary.sin),
        token("identifier", "sinh"): NativeFnValue(mathLibrary.sinh),
        token("identifier", "sqrt"): NativeFnValue(mathLibrary.sqrt),
        token("identifier", "tan"): NativeFnValue(mathLibrary.tan),
        token("identifier", "tanh"): NativeFnValue(mathLibrary.tanh),
        token("identifier", "huge"): mathLibrary.huge,
        token("identifier", "pi"): mathLibrary.pi
        }), False)
    env.declareVar("table", ObjectVal({
        token("identifier", "insert"): NativeFnValue(tableLibrary.insert),
        token("identifier", "clear"): NativeFnValue(tableLibrary.clear),
        token("identifier", "clone"): NativeFnValue(tableLibrary.clone),
        token("identifier", "concat"): NativeFnValue(tableLibrary.concat),
        token("identifier", "create"): NativeFnValue(tableLibrary.create),
        token("identifier", "find"): NativeFnValue(tableLibrary.find),
        token("identifier", "foreach"): NativeFnValue(tableLibrary.foreach),
        token("identifier", "foreachi"): NativeFnValue(tableLibrary.foreachi),
        token("identifier", "freeze"): NativeFnValue(tableLibrary.freeze),
        token("identifier", "getn"): NativeFnValue(tableLibrary.getn),
        token("identifier", "isfrozen"): NativeFnValue(tableLibrary.isfrozen),
        token("identifier", "maxn"): NativeFnValue(tableLibrary.maxn),
        token("identifier", "move"): NativeFnValue(tableLibrary.move),
        token("identifier", "pack"): NativeFnValue(tableLibrary.pack),
        token("identifier", "remove"): NativeFnValue(tableLibrary.remove),
        token("identifier", "sort"): NativeFnValue(tableLibrary.sort),
        token("identifier", "unpack"): NativeFnValue(tableLibrary.unpack)
        }), False)
    env.declareVar("string", ObjectVal({
        token("identifier", "byte"): NativeFnValue(stringLibrary.byte),
        token("identifier", "char"): NativeFnValue(stringLibrary.char),
        token("identifier", "find"): NativeFnValue(stringLibrary.find),
        token("identifier", "format"): NativeFnValue(stringLibrary.format),
        token("identifier", "gmatch"): NativeFnValue(stringLibrary.gmatch),
        token("identifier", "gsub"): NativeFnValue(stringLibrary.gsub),
        token("identifier", "len"): NativeFnValue(stringLibrary.len),
        token("identifier", "lower"): NativeFnValue(stringLibrary.lower),
        token("identifier", "match"): NativeFnValue(stringLibrary.match),
        token("identifier", "pack"): NativeFnValue(stringLibrary.pack),
        token("identifier", "packsize"): NativeFnValue(stringLibrary.packsize),
        token("identifier", "rep"): NativeFnValue(stringLibrary.rep),
        token("identifier", "reverse"): NativeFnValue(stringLibrary.reverse),
        token("identifier", "split"): NativeFnValue(stringLibrary.split),
        token("identifier", "sub"): NativeFnValue(stringLibrary.sub),
        token("identifier", "unpack"): NativeFnValue(stringLibrary.unpack),
        token("identifier", "upper"): NativeFnValue(stringLibrary.upper)
        }), False)

    return env