import io
import nbt
from functools import partial

readbyte = nbt._read_byte
readshort = nbt._read_short
readushort = nbt._read_ushort
readint = nbt._read_int
readlong = nbt._read_long
readfloat = nbt._read_float
readdouble = nbt._read_double
readstring = nbt._read_string

infile = open('raw_chunk.nbt', 'rb')

og = infile.read()
infile.seek(0, io.SEEK_SET)

tag, name = nbt.load(og)
raw = nbt.dump(tag)
tag2, name2 = nbt.load(raw)
raw2 = nbt.dump(tag2)

print(f'Original Size: {len(og)}')
print(f'  Test 1 Size: {len(raw)}')
print(f'  Test 2 Size: {len(raw2)}')

def reset():
    infile.seek(0, io.SEEK_SET)

def readin():
    global infile
    if infile:
        try:
            infile.close()
        except:
            pass
    infile = open('raw_chunk.nbt','rb')

def tellread(func):
    t = infile.tell()
    v = func(infile)
    return (t, v)

def rbyte():
    t, v = tellread(readbyte)
    print(f'byte {v} at {t}')

def rshort():
    t, v = tellread(readshort)
    print(f'short {v} at {t}')

def rushort():
    t, v = tellread(readushort)
    print(f'ushort {v} at {t}')

def rint():
    t, v = tellread(readint)
    print(f'int {v} at {t}')

def rlong():
    t, v = tellread(readlong)
    print(f'long {v} at {t}')

def rfloat():
    t, v = tellread(readfloat)
    print(f'float {v} at {t}')

def rdouble():
    t, v = tellread(readdouble)
    print(f'double {v} at {t}')

def rstr():
    t, v = tellread(readstring)
    print(f'string {repr(v)} at {t}')
