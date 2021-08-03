# (c) E-kvadrat Consulting & Media, 2021

class Log:
    def __init__(self, file):
        self.file = file

    def print(self, *args, **kwargs):
        print(*args, **kwargs)
        print(*args, **kwargs, file=self.file)
