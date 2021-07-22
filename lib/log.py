from safetywrap import Result

class Log:
    def __init__(self, file):
        self.file = open(file, 'a')

    def print(self, message, console=True):
        if console:
            print(message)
        self.file.write(f"{message}\n")

    def result(self, result: Result):
        for err in result.err():
            self.print(err)
        return result
