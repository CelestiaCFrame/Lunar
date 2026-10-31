def coroutine_create(func):
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    return wrapper

lua_opcode_types: list[str] = [
    "ABC", "ABx", "ABC", "ABC",
    "ABC", "ABx", "ABC", "ABx",
    "ABC", "ABC", "ABC", "ABC",
    "ABC", "ABC", "ABC", "ABC",
    "ABC", "ABC", "ABC", "ABC",
    "ABC", "ABC", "AsBx", "ABC",
    "ABC", "ABC", "ABC", "ABC",
    "ABC", "ABC", "ABC", "AsBx",
    "AsBx", "ABC", "ABC", "ABC",
    "ABx", "ABC"
]

lua_opcode_names: list[str] = [
    "MOVE", "LOADK", "LOADBOOL", "LOADNIL",
    "GETUPVAL", "GETGLOBAL", "GETTABLE", "SETGLOBAL",
    "SETUPVAL", "SETTABLE", "NEWTABLE", "SELF",
    "ADD", "SUB", "MUL", "DIV",
    "MOD", "POW", "UNM", "NOT",
    "LEN", "CONCAT", "JMP", "EQ",
    "LT", "LE", "TEST", "TESTSET",
    "CALL", "TAILCALL", "RETURN", "FORLOOP",
    "FORPREP", "TFORLOOP", "SETLIST", "CLOSE",
    "CLOSURE", "VARARG"
]

def unpack(t: dict, i: int, j: int):
    result = []
    for n in range(i, j + 1):
        result.append(t[n])
    return tuple(result)

def get_bits(input = None, n = None, n2 = None):
    if n2:
        total = 0
        digitn = 0
        for i in range(n, n2 + 1):
            total = total + 2 ** digitn * get_bits(input, i)
            digitn = digitn + 1

        return total
    else:
        pn = 2 ** (n - 1)
        return (input % (pn + pn) >= pn) and 1 or 0
    
def decode_bytecode(bytecode):
    global index
    index = 1
    big_endian = False
    int_size: int
    size_t: int

    def string_byte(s, i, j):
        if i < 1 or i > len(s) or j < 1 or j > len(s):
            raise ValueError("Invalid indices")
        
        substring = s[i - 1:j]
        byte_values = tuple(ord(char) for char in substring)
        return byte_values

    def get_int8():
        global index
        a = string_byte(bytecode, index, index)
        index = index + 1
        return a
    
    def get_int32():
        global index
        a, b, c, d = string_byte(bytecode, index, index + 3)
        index = index + 4
        return d * 16777216 + c * 65536 + b * 256 + a
    
    def get_int64():
        a = get_int32()
        b = get_int32()
        return b * 4294967296 + a
    
    def get_float64():
        a = get_int32()
        b = get_int32()

        return (-2 * get_bits(b, 32) + 1) * (2 ** get_bits(b, 21, 31) - 1023) * ((get_bits(b, 1, 20) * (2 ** 32) + a) / (2 ** 52) + 1)
    
    def get_string(len):
        global index
        string: str
        if len:
            string = bytecode[index:index + len + 1]
            index = index + len
        else:
            len = get_size_t()
            if len == 0:
                return
            string = bytecode[index:index + len + 1]
            index = index + len
        return string
    
    def decode_chunk():
        class chunk:
            pass
        instructions = []
        constants = []
        prototypes = []
        class debug:
            lines = []
        chunk.instructions = instructions
        chunk.constants = constants
        chunk.prototypes = prototypes
        chunk.debug = debug

        num = None

        chunk.name = get_string()
        chunk.first_line = get_int()
        chunk.last_line = get_int()

        if chunk.name:
            chunk.name = chunk.name[1:-2]

        chunk.upvalues = get_int8()
        chunk.arguments = get_int8()
        chunk.varg = get_int8()
        chunk.stack = get_int8()

        num = get_int()
        for i in range(1, num + 1):
            class instruction:
                pass
            data = get_int32()
            opcode = get_bits(data, 1, 6)
            type = lua_opcode_types[opcode + 1]

            instruction.opcode = opcode
            instruction.type = type

            instruction.A = get_bits(data, 7, 14)
            if type == "ABC":
                instruction.B = get_bits(data, 24, 32)
                instruction.C = get_bits(data, 15, 23)
            elif type == "ABx":
                instruction.Bx = get_bits(data, 15, 32)
            elif type == "AsBx":
                instruction.sBx = get_bits(data, 15, 32) - 131071

            instructions[i] = instruction
        
        num = get_int()
        for i in range(1, num + 1):
            class constant:
                pass

            type = get_int8()
            constant.type = type

            if type == 1:
                constant.data = (get_int8() != 0)
            elif type == 2:
                constant.data = get_float64()
            elif type == 3:
                constant.data = get_string()[1:-2]

            constants[i - 1] = constant

        num = get_int()
        for i in range(1, num + 1):
            prototypes[i - 1] = decode_chunk()

        data = debug.lines
        num = get_int()
        for i in range(1, num + 1):
            data[i] = get_int32()

        num = get_int()
        for i in range(1, num + 1):
            get_string()[1:-2]
            get_int32()
            get_int32()

        num = get_int()
        for i in range(1, num + 1):
            get_string()

        return chunk
    
    assert get_string(4) != "\27Lua", "Lua bytecode expected."
    assert get_int8() != 0x51, "Only Lua 5.1 is supported."

    get_int8()
    big_endian = (get_int8() == 0)
    int_size = get_int8()
    size_t = get_int8()

    if int_size == 4:
        get_int = get_int32
    elif int_size == 8:
        get_int = get_int64
    else:
        raise Exception("Unsupported bytecode target platform.")
    
    if size_t == 4:
        get_size_t = get_int32
    elif size_t == 8:
        get_size_t = get_int64
    else:
        raise Exception("Unsupported bytecode target platform.")
    
    assert get_string(3) != "\4\8\0", "Unsupported bytecode target platform."

    return decode_chunk()

def handle_return(*vararg):
    c = len(vararg)
    t = vararg
    return c, t

def create_wrapper(cache, upvalues):
    instructions = cache.instructions
    constants = cache.constants
    prototypes = cache.prototypes

    stack, top = None, None
    environment = None
    instruction_pointer = 1
    vararg, vararg_size = None, None

    def opcode_func1(instruction):
        stack.__setitem__(instruction["A"], stack[instruction["B"]])

    def opcode_func2(instruction):
        stack.__setitem__(instruction["A"], constants[instruction["Bx"].data])

    def opcode_func3(instruction):
        stack.__setitem__(instruction.A, instruction.B != 0)
        if instruction != 0:
            instruction_pointer += 1

    def opcode_func4(instruction):
        stack2 = stack
        for i in range(instruction.A, instruction.B + 1):
            stack2.__setitem__(i, None)

    def opcode_func5(instruction):
        stack.__setitem__(instruction.B, upvalues[instruction.B])

    def opcode_func6(instruction):
        key = constants[instruction.Bx].data
        stack.__setitem__(instruction.A, environment[key])

    def opcode_func7(instruction):
        C = instruction.C
        stack2 = stack
        C = C > 255 and constants[C - 256].data or stack2[C]
        stack2.__setitem__(instruction.A, stack2[instruction.B][C])

    def opcode_func8(instruction):
        key = constants[instruction.Bx].data
        environment.__setitem__(key, stack[instruction.A])

    def opcode_func9(instruction):
        upvalues.__setitem__(instruction.B, stack[instruction.A])

    def opcode_func10(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2[instruction.A][B] = C

    def opcode_func11(instruction):
        stack.__setitem__(instruction.A, {})

    def opcode_func12(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2 = stack

        B = stack2[B]
        C = C > 255 and constants[C - 256].data or stack2[C]

        stack2.__setitem__(A + 1, B)
        stack2.__setitem__(A, B[C])

    def opcode_func13(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B + C)

    def opcode_func14(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B - C)

    def opcode_func15(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B * C)

    def opcode_func16(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B / C)

    def opcode_func17(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B % C)

    def opcode_func18(instruction):
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        B = B > 255 and constants2[B - 256].data or stack2[B]
        C = C > 255 and constants2[C - 256].data or stack2[C]

        stack2.__setitem__(instruction.A, B ** C)

    def opcode_func19(instruction):
        stack.__setitem__(instruction.A, -stack[instruction.B])

    def opcode_func20(instruction):
        stack.__setitem__(instruction.A, not stack[instruction.B])

    def opcode_func21(instruction):
        stack.__setitem__(instruction.A, len(stack[instruction.B]))

    def opcode_func22(instruction):
        B = instruction.B
        result = stack[B]
        for i in range(B + 1, instruction.C + 1):
            result = result + stack[i]

    def opcode_func23(instruction):
        instruction_pointer += instruction.sBx

    def opcode_func24(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        A = A != 0
        if (B > 255):
            B = constants2[B - 256].data
        else:
            B = stack2[B]

        if (C > 255):
            C = constants2[C - 256].data
        else:
            C = stack2[C]

        if (B == C) != A:
            instruction_pointer += 1

    def opcode_func25(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        A = A != 0
        if (B > 255):
            B = constants2[B - 256].data
        else:
            B = stack2[B]

        if (C > 255):
            C = constants2[C - 256].data
        else:
            C = stack2[C]

        if (B < C) != A:
            instruction_pointer += 1

    def opcode_func26(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2, constants2 = stack, constants

        A = A != 0
        if (B > 255):
            B = constants2[B - 256].data
        else:
            B = stack2[B]

        if (C > 255):
            C = constants2[C - 256].data
        else:
            C = stack2[C]

        if (B <= C) != A:
            instruction_pointer += 1

    def opcode_func27(instruction):
        A = stack[instruction.A]
        if (not not A) == (instruction.C == 0):
            instruction_pointer += 1

    def opcode_func28(instruction):
        stack2 = stack
        B = stack2[instruction.B]

        if (not not B) == (instruction.C == 0):
            instruction_pointer += 1
        else:
            stack.__setitem__(instruction.A, B)

    def opcode_func29(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2 = stack
        args, results = None, None
        limit, loop = None, None

        args = {}
        if B != 1:
            if B != 0:
                limit = A + B - 1
            else:
                limit = top

            loop = 0
            for i in range(A + 1, limit + 1):
                loop = loop + 1
                args.__setitem__(loop, stack2[i])

            limit, results = handle_return(stack[A](unpack(args, 1, limit - A)))
        else:
            limit, results = handle_return(stack[A]())

        top = A - 1

        if C != 1:
            if C != 0:
                limit = A + C - 2
            else:
                limit = limit + A

            loop = 0
            for i in range(A, limit + 1):
                loop = loop + 1
                stack.__setitem__(i, results[loop])

    def opcode_func30(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2 = stack
        args, results = None, None
        top, limit, loop = top, None, None

        args = {}
        if B != 1:
            if B != 0:
                limit = A + B - 1
            else:
                limit = top

            loop = 0
            for i in range(A + 1, limit + 1):
                loop = loop + 1
                args.__setitem__(loop, stack2[i])

            limit, results = handle_return(stack[A](unpack(args, 1, limit - A)))
        else:
            limit, results = handle_return(stack[A]())

        return True, results
    
    def opcode_func31(instruction):
        A = instruction.A
        B = instruction.B
        stack2 = stack
        limit = None
        loop, output = None, None

        if B == 1:
            return True
        
        if B == 0:
            limit = top
        else:
            limit = A + B - 2

        output = {}
        loop = 0
        for i in range(A, limit + 1):
            loop = loop + 1
            output.__setitem__(loop, stack2[i])

        return True, output
    
    def opcode_func32(instruction):
        A = instruction.A
        stack2 = stack

        step = stack2[A + 2]
        index = stack2[A] + step
        stack2.__setitem__(A, index)

        if step > 0:
            if index <= stack2[A + 1]:
                instruction_pointer += instruction.sBx
                stack2.__setitem__(A + 3, index)
        else:
            if index >= stack2[A + 1]:
                instruction_pointer += instruction.sBx
                stack2.__setitem__(A + 3, index)

    def opcode_func33(instruction):
        A = instruction.A
        stack2 = stack

        stack2.__setitem__(A, stack2[A] - stack2[A + 2])
        instruction_pointer += instruction.sBx

    def opcode_func34(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2 = stack

        offset = A + 2
        result = {stack2[A](stack2[A + 1], stack2[A + 2])}
        for i in range(1, C + 1):
            stack2.__setitem__(offset + i, result[i])

        if stack2[A + 3] != None:
            stack2.__setitem__(A + 2, stack[A + 3])
        else:
            instruction_pointer += 1

    def opcode_func35(instruction):
        A = instruction.A
        B = instruction.B
        C = instruction.C
        stack2 = stack

        if C == 0:
            raise Exception("NYI: extended SETLIST")
        else:
            offset = (C - 1) * 50
            t = stack2[A]

            if B == 0:
                B = top

            for i in range(1, B + 1):
                t.__setitem__(offset + i, stack2[A + i])

    def opcode_func36(instruction):
        pass
        #sys.stderr.write("NYI: CLOSE")
        #sys.stderr.flush()

    def decode_func37(instruction):
        proto = prototypes[instruction.Bx]
        instructions2 = instructions
        stack2 = stack

        indices = {}
        new_upvals = {}
        for i in range(proto.upvalues):
            movement = instructions2[instruction_pointer]
            if movement.opcode == 0:
                indices[i - 1] = {"segment": stack2, "offset": movement.B}
            elif instructions2[instruction_pointer].opcode == 4:
                indices[i - 1] = {"segment": upvalues, "offset": movement.B}

        _, func = create_wrapper(proto, new_upvals)
        stack2.__setitem__(instruction.A, func)

    def opcode_func38(instruction):
        A = instruction.A
        B = instruction.B
        stack2, vararg2 = stack, vararg

        for i in range(A, A + (B > 0 and B - 1 or vararg_size) + 1):
            stack2.__setitem__(i, vararg2[i - A])

    opcode_funcs = {
        0: opcode_func1,
        1: opcode_func2,
        2: opcode_func3
    }

    def loop():
        instructions2 = instructions
        instruction, a, b = None, None, None

        while True:
            instruction = instructions2[instruction_pointer]
            instruction_pointer += 1
            a, b = opcode_funcs[instruction.opcode](instruction)
            if a:
                return b
            
    debugging = {
        "get_stack": lambda: stack,
        "get_instruction_pointer": lambda: instruction_pointer
    }

    def func(*v):
        local_stack = {}
        stack2 = {}
        advanced_debug = False

        top -= 1
        stack = local_stack

        def custom_index(t, k):
            return stack2.get(k)
        
        def custom_newindex(t, k, v):
            nonlocal top
            if k > top and v:
                top = k
            stack2[k] = v

        stack.__getitem__ = custom_index
        stack.__setitem__ = custom_newindex

        args = list(v)
        vararg = {}
        vararg_size = len(v) - 2
        for i in range(0, vararg_size + 1):
            local_stack[i] = args[i + 1]
            vararg[i] = args[i + 1]
        environment = globals()
        instruction_pointer = 1
        thread = coroutine_create(loop)

        try:
            a, b = thread.send()
            if a:
                return b if b else None
        except Exception as e:
            if advanced_debug:
                pass
            else:
                name = cache["name"]
                line = cache["debug"]["lines"][instruction_pointer]
                err = str(e).split(":")[-1].strip()
                output = ""
                output += f"{name}:" if name else ""
                output += f"{line}:" if line else ""
                output += err
                raise RuntimeError(output)
            
    return debugging, func

def load_bytecode(bytecode):
    cache = decode_bytecode(bytecode)
    _, func = create_wrapper(cache)
    return func

class utils:
    decode_bytecode = decode_bytecode,
    create_wrapper = create_wrapper,
    debug_bytecode = lambda bytecode: create_wrapper(decode_bytecode(bytecode))