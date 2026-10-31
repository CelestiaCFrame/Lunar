from frontend.parser import Parser
from runtime.interpreter import interpreter
from runtime.environment import createGlobalEnv
def func1(args, scope=None):
    string = ""
    stack = 0
    var2 = 0
    skip = 0
    var = str(args)
    for i in var:
        if skip > 0:
            skip -= 1
            var2 += 1
            continue
        if i == "[" and var[var2 + 1] != "'":
            if var[var2 + 1] != "]":
                stack += 1
                string = string + "[\n" + ("   " * stack)
            else:
                string = string + i
        elif i == "]":
            if var[var2 - 1] != "[":
                stack -= 1
                string = string + "\n" + ("   " * stack) + "]"
            else:
                string = string + i
        elif i == "{":
            stack += 1
            string = string + "{\n" + ("   " * stack)
        elif i == "}":
            stack -= 1
            string = string + "\n" + ("   " * stack) + "}"
        elif i == ",":
            skip += 1
            string = string + ",\n" + ("   " * stack)
        else:
            string = string + i

        var2 += 1

    print(string)

"""
    print("CLua v2.9")
    parser = Parser()
    openFile = "main.py"
    env = createGlobalEnv(openFile)

    while True:
        src = input("> ")
        if src == "exit()":
            break

        try:
            program, indexLines = parser.produceAST(src, openFile)
            env.indexLines = indexLines
            result = interpreter(program, env)
            print(result)
        except Exception as exception:
            print(exception)
"""

parser = Parser()

openFile = "test.lua"
env = createGlobalEnv(openFile)
with open(openFile) as selectedFile:
    src = selectedFile.read()
    
#try:
program, indexLines = parser.produceAST(src, openFile)
env.indexLines = indexLines
result = interpreter(program, env)
#except Exception as exception:
    #print(str(exception))