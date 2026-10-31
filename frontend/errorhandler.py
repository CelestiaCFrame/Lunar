class ErrorHandler:
    def __init__(self, message: str, index: list, env = None, selectedFile = None):
        if len(index) == 2:
            indexLines = env.indexLines
        else:
            indexLines = index[2]
        index[0] = index[0] - 1
        Index = 1
        if len(indexLines) != 0:
            for i in range(len(indexLines)):
                if index[0] >= indexLines[i]:
                    Index += 1
                else:
                    break

        raise Exception(f"{selectedFile}:{Index}: {str(message)}\nStack Begin\nScript '{selectedFile}', Line {Index}\nStack End")