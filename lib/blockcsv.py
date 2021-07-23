from io import StringIO
from typing import TextIO
import csv

class BlockNotFoundException(Exception):
    def __init__(self, file, headings):
        self.file = file
        self.headings = headings
    def __str__(self):
        return f"Data block not found in {self.file}. Expected headings: {self.headings}"

def reader(file: TextIO, headings: str):
    data_block = ''
    inside_block = False

    for line in file:
        if not inside_block:
            if line.startswith(headings):
                inside_block = True
                data_block += line
        else:
            if line != '\n':
                data_block += line
            else:
                break

    if not inside_block:
        raise BlockNotFoundException(file.name, headings)
    return csv.reader(StringIO(data_block))
