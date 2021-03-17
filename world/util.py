import math

def nibble4(arr, index):
    return arr[index//2] & 0x0F if index % 2 == 0 else (arr[index//2]>>4) & 0x0F

def chunk_block_index(*args):
    if len(args) == 3:
        return args[1]*256+args[2]*16+args[0]
    else:
        return args[0][1]*256+args[0][2]*16+args[0][0]

def chunk_index_bitsize(palette_size):
    return max(math.ceil(math.log2(palette_size)), 4)

def extract_index(full_index, palette_size, block_states):
    bitsize = max(math.ceil(math.log2(palette_size)), 4)
    #vpl = values per long
    vpl = 64 // bitsize
    mask = 2**bitsize-1
    state_index = full_index // vpl
    value_offset = (full_index % vpl) * bitsize
    slot = block_states[state_index]
    return (slot & (mask << value_offset)) >> value_offset

def sbyte_to_byte(v):
    if 0 <= v < 128:
        return v
    if -128 <= v < 0:
        return v + 256
    raise Exception('Unexpected value.')

def byte_to_sbyte(v):
    if 0 <= v < 128:
        return v
    if 128 <= v < 256:
        return v - 256
    raise Exception('Unexpected value.')

def short_to_ushort(v):
    if 0 <= v < 32768:
        return v
    if -32768 <= v < 0:
        return v + 65536

def ushort_to_short(v):
    if 0 <= v < 32768:
        return v
    if 32768 <= v < 65536:
        return v - 65536
    raise Exception('Unexcepted value.')

def int_to_uint(v):
    if 0 <= v < 2147483648:
        return v
    if -2147483648 <= v < 0:
        return v + 4294967296

def uint_to_int(v):
    if 0 <= v < 2147483648:
        return v
    if 2147483648 <= v < 4294967296:
        return v - 4294967296
    raise Exception('Unexpected value.')

def long_to_ulong(v):
    if 0 <= v < 9223372036854775808:
        return v
    if -9223372036854775808 <= v < 0:
        return v + 18446744073709551616
    raise Exception('Unexpected value.')

def ulong_to_long(v):
    if 0 <= v < 9223372036854775808:
        return v
    if 9223372036854775808 <= v < 18446744073709551616:
        return v - 18446744073709551616
    raise Exception('Unexpected value.')

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