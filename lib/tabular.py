DELIM='\t'
QUOTE="`"

class Writer:
    def __init__(self, file, row_type):
        self.file = file
        self.row_type = row_type

    def write(self, row):
        assert type(row) == self.row_type
        fields = map(lambda x: str(x), row)
        self.file.write('\t'.join(fields) + '\n')

def decode_line(line: str, row_type):
    line = line.rstrip('\n')
    row = line.split('\t', len(row_type.__annotations__))
    fields_converted = []
    for field_index, field_type in enumerate(row_type.__annotations__.values()):
        raw_value = row[field_index]
        converted = None

        if field_type == bool:
            converted = raw_value == 'True'
        elif field_type == int:
            converted = int(raw_value)
        elif field_type == str:
            converted = raw_value
        else:
            raise TypeError('Unsupported type', field_type)

        fields_converted.append(converted)

    return row_type(*fields_converted)

class Reader:
    def __init__(self, file, row_type):
        self.file = file
        self.row_type = row_type

    def __iter__(self):
        for line in self.file:
            yield decode_line(line, self.row_type)

def read_last_line(file, row_type):
    last_line = None
    with open(file, mode='r') as file:
        for line in file:
            last_line = line
    if last_line is not None:
        return decode_line(last_line, row_type)
