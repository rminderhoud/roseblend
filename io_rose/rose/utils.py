import struct


def list_2d(width, length, default=None):
    """ Create a 2-dimensional list of width x length """
    return [[default] * width for i in range(length)]

class Vector2:
    def __init__(self):
        self.x = 0
        self.y = 0

class Vector3:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

def read_i8(f):
    return struct.unpack("b", f.read(1))[0]

def read_i32(f):
    return struct.unpack("<i", f.read(4))[0]

def read_f32(f):
    return struct.unpack("<f", f.read(4))[0]

def read_bool(f):
    return struct.unpack("?", f.read(1))[0]

def read_bstr(f):
    """ Read byte-prefixed string """
    size = struct.unpack("B", f.read(1))[0]
    if size == 0:
        return ""

    bstring = f.read(size)
    return bstring.decode("EUC-KR")

def read_str(f):
    """ Read null-terminated string """
    bstring = bytes("", encoding="EUC-KR")
    while True:
        byte = f.read(1)
        if byte == b"\x00":
            break
        else:
            bstring += byte
    return bstring.decode("EUC-KR")


