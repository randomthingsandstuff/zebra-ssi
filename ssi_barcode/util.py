def xxd_format(data):
    def is_printable(byte):
        return 32 <= byte <= 126

    output = ''
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        address = f"{i:08x}"
        binary_data = ' '.join(f"{byte:02x}" for byte in chunk)
        ascii_data = ''.join(chr(byte) if is_printable(byte) else '.' for byte in chunk)
        
        # Print the formatted string without colors
        output += f"{address}: {binary_data:<47} {ascii_data}\n"
    return output


class BinaryDecoder:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def read_byte(self):
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read_uint32_be(self):
        value = int.from_bytes(self.data[self.offset:self.offset+4], 'big')
        self.offset += 4
        return value

    def read_bytes(self, length):
        value = self.data[self.offset:self.offset+length]
        self.offset += length
        return value

    def is_done(self):
        return self.offset == len(self.data)
