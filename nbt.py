from abc import ABC, abstractmethod
import struct
import io
from functools import partial
import util

tag_id_table = {
    1 : 'TAG_Byte',
    2 : 'TAG_Short',
    3 : 'TAG_Int',
    4 : 'TAG_Long',
    5 : 'TAG_Float',
    6 : 'TAG_Double',
    7 : 'TAG_Byte_Array',
    8 : 'TAG_String',
    9 : 'TAG_List',
    10 : 'TAG_Compound',
    11 : 'TAG_Int_Array',
    12 : 'TAG_Long_Array',
    'TAG_Byte' : 1,
    'TAG_Short' : 2,
    'TAG_Int' : 3,
    'TAG_Long' : 4,
    'TAG_Float' : 5,
    'TAG_Double' : 6,
    'TAG_Byte_Array' : 7,
    'TAG_String' : 8,
    'TAG_List' : 9,
    'TAG_Compound' : 10,
    'TAG_Int_Array' : 11,
    'TAG_Long_Array' : 12
}

def read_byte(stream):
    return int.from_bytes(stream.read(1),'big',signed=True)

def read_short(stream):
    return int.from_bytes(stream.read(2), 'big', signed=True)

def read_ushort(stream):
    return int.from_bytes(stream.read(2), 'big', signed=False)

def read_int(stream):
    return int.from_bytes(stream.read(4), 'big', signed=True)

def read_long(stream):
    return int.from_bytes(stream.read(8), 'big', signed=True)

def read_float(stream):
    return struct.unpack('>f', stream.read(4))[0]

def read_double(stream):
    return struct.unpack('>d', stream.read(8))[0]

def read_string(stream):
    length = read_ushort(stream)
    return stream.read(length).decode('utf-8')

def write_fmt(stream, fmt, value):
    stream.write(struct.pack(fmt, value))

class nbt_tag(ABC):
    @abstractmethod
    def write(self, stream):
        pass
    @abstractmethod
    def to_bytes(self):
        pass
    @abstractmethod
    def copy(self):
        pass

class t_byte(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>b', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_byte(self.value)

class t_short(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>h', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_short(self.value)


class t_int(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>i', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_int(self.value)

class t_long(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>q', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_long(self.value)

class t_float(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0.0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>f', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_float(self.value)

class t_double(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value=0):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>d', self.value))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_double(self.value)

class t_string(nbt_tag):
    __slots__ = ('value',)

    def __init__(self, value :str =''):
        self.value = value
    
    def write(self, stream):
        stream.write(struct.pack('>h', len(self.value)))
        stream.write(self.value.encode('utf-8'))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_string(self.value)

class t_bytes(nbt_tag):
    __slots__ = ('data',)

    def __init__(self, data=None):
        if type(data) == list:
            self.data = list(data)
        elif type(data) in {bytes, bytearray}:
            self.data = list()
            for v in data:
                self.data.append(util.byte_to_sbyte(v))
        else:
            self.data = list()
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        if -128 <= value < 128:
            self.data[index] = value
        elif 128 <= value < 256:
            self.data[index] = value - 256
        else:
            raise Exception('Value is invalid.')
    
    def write(self, stream):
        stream.write(struct.pack('>i', len(self.data)))
        for v in self.data:
            stream.write(struct.pack('>b', v))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_bytes(self.data)

class t_ints(nbt_tag):
    __slots__ = ('data',)

    def __init__(self, data=None):
        if type(data) == list:
            self.data = list(data)
        else:
            self.data = list()
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        if -2147483648 <= value < 2147483648:
            self.data[index] = value
        elif 2147483648 <= value < 4294967296:
            self.data[index] = value - 4294967296
        else:
            raise Exception('Value is invalid.')
    
    def write(self, stream):
        stream.write(struct.pack('>i', len(self.data)))
        for v in self.data:
            stream.write(struct.pack('>i', v))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_ints(self.data)

class t_longs(nbt_tag):
    __slots__ = ('data',)

    def __init__(self, data=None):
        if type(data) == list:
            self.data = list(data)
        else:
            self.data = list()
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        if -9223372036854775808 <= value < 9223372036854775808:
            self.data[index] = value
        elif 9223372036854775808 <= value < 18446744073709551616:
            self.data[index] = value - 18446744073709551616
        else:
            raise Exception('Value is invalid.')
    
    def write(self, stream):
        stream.write(struct.pack('>i', len(self.data)))
        for v in self.data:
            stream.write(struct.pack('>q', v))
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()

    def copy(self) -> nbt_tag:
        return t_longs(self.data)

class t_list(nbt_tag):
    __slots__ = ('data', 'type')

    def __init__(self, tag_type, data=None):
        if type(tag_type) == int:
            self.type = tag_type
        elif type(tag_type) == str:
            self.type = tag_id_table[tag_type]
        elif issubclass(tag_type, nbt_tag):
            self.type = tag_type_table[tag_type]
        else:
            self.type = 0
        if type(data) == list:
            self.data = list(data)
        else:
            self.data = list()
    
    def __getitem__(self, index):
        return self.data[index]
    
    def write(self, stream):
        write_fmt(stream, '>B', self.type)
        write_fmt(stream, '>i', len(self.data))
        for v in self.data:
            v.write(stream)
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self) -> nbt_tag:
        return t_list(self.type, self.data)

class t_compound(nbt_tag):
    __slots__ = ('data',)

    def __init__(self, data : dict):
        """
        data must be a dict where the keys are of type str, and the values are of type nbt_tag.
        """
        self.data = dict(data)
    
    def __getitem__(self, id):
        return self.data.get(id, None)
    
    def __setitem__(self, id, value):
        self.data[id] = value
    
    def __delitem__(self, id):
        del self.data[id]

    def __contains__(self, id):
        return id in self.data
    
    def __getattr__(self, id):
        return self.data.get(id, None)
    
    def write(self, stream):
        for k, v in self.data.items():
            tag_type = tag_type_table[type(v)]
            stream.write(struct.pack('>B', tag_type))
            stream.write(struct.pack('>H', len(k)))
            stream.write(k.encode('utf-8'))
            v.write(stream)
        stream.write(b'\x00')
    
    def to_bytes(self) -> bytes:
        with io.BytesIO() as buffer:
            self.write(buffer)
            return buffer.getvalue()
    
    def copy(self):
        return t_compound(self.data)

def read_tag_data(stream, id):
    if id == 1:
        return t_byte(read_byte(stream))
    if id == 2:
        return t_short(read_short(stream))
    if id == 3:
        return t_int(read_int(stream))
    if id == 4:
        return t_long(read_long(stream))
    if id == 5:
        return t_float(read_float(stream))
    if id == 6:
        return t_double(read_double(stream))
    if id == 7:
        size = read_int(stream)
        return t_bytes(stream.read(size))
    if id == 8:
        size = read_ushort(stream)
        return t_string(stream.read(size).decode('utf-8'))
    if id == 9:
        tagid = read_byte(stream)
        size = read_int(stream)
        items = []
        for i in range(size):
            items.append(read_tag_data(stream, tagid))
        return t_list(tagid, items)
    if id == 10:
        items = dict()
        tagid = read_byte(stream)
        while tagid != 0:
            tag_name = read_string(stream)
            tag = read_tag_data(stream, tagid)
            items[tag_name] = tag
            tagid = read_byte(stream)
        return t_compound(items)
    if id == 11:
        size = read_int(stream)
        items = []
        for i in range(size):
            items.append(read_int(stream))
        return t_ints(items)
    if id == 12:
        size = read_int(stream)
        items = []
        for i in range(size):
            items.append(read_long(stream))
        return t_longs(items)

def load(data : bytes):
    with io.BytesIO(data) as stream:
        tag_id = read_byte(stream)
        if tag_id == 10:
            name = read_string(stream)
            print(len(name))
            tag = read_tag_data(stream, 10)
            return tag

def dump(tag : nbt_tag) -> bytes:
    with io.BytesIO() as stream:
        if type(tag) == t_compound:
            stream.write(b'\x0A\x00\x00')
        tag.write(stream)
        return stream.getvalue()

tag_type_table = {
    0 : None,
    1 : t_byte,
    2 : t_short,
    3 : t_int,
    4 : t_long,
    5 : t_float,
    6 : t_double,
    7 : t_bytes,
    8 : t_string,
    9 : t_list,
    10 : t_compound,
    11 : t_ints,
    12 : t_longs,
    None : 0,
    t_byte : 1,
    t_short : 2,
    t_int : 3,
    t_long : 4,
    t_float : 5,
    t_double : 6,
    t_bytes : 7,
    t_string : 8,
    t_list : 9,
    t_compound : 10,
    t_ints : 11,
    t_longs : 12
}