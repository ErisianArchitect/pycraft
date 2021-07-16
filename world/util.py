"""
These are functions that may be used throughout the codebase.
"""

import math
import struct

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