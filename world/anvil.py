import os
from os import path
import gzip
import zlib
import io
import numpy
import math
import bisect
import arrow
from . import nbt
from . import chunk

__null_sector = bytes(4096)

class Sector(object):
    __slots__ = ('offset', 'count')
    def __init__(self, offset, count):
        self.offset = offset
        self.count = count
    
    @property
    def end(self) -> int:
        return self.offset + self.count
    
    @property
    def size(self) -> int:
        return self.count * 4096
    
    @property
    def file_offset(self):
        return self.offset * 4096
    
    def __lt__(self, other):
        if type(other) == Sector:
            return (self.offset + self.count) <= other.offset
    
    def __gt__(self, other):
        if type(other) == Sector:
            return self.offset >= (other.offset + other.count)
    
    def __eq__(self, other):
        if type(other) == Sector:
            return self.offset == other.offset and self.count == other.count
        return False
    
    def intersects(self, other):
        if type(other) == Sector:
            if self.offset <= other.offset and self.end > other.offset:
                return True
            if other.offset <= self.offset and other.end > self.offset:
                return True
            return False
    
    def to_bytes(self):
        with io.BytesIO() as buff:
            buff.write(self.offset.to_bytes(3, 'big', signed=False))
            buff.write(self.count.to_bytes(1, 'big', signed=False))
            return buff.getvalue()
    
    def __repr__(self):
        return f'Sector(offset={self.offset}, count={self.count})'

# TODO: Refactor RegionFile
#   I'm going to need to completely rewrite the region files upon saving them, so I'm going to work
#   out some kind of system to do that.
class RegionFile:
    #   This class looks AWFUL right now. We can fix that.

    __slots__ = ('filename','chunks','sectors','loaded_chunks','loaded_indices')

    @staticmethod
    def get_index(x : int, z : int):
        return ((x & 31) | ((z & 31) << 5))
    
    @staticmethod
    def expand_index(index):
        return ((index & 0b11111), ((index & 0b1111100000) >> 5))

    def __init__(self, filename : str):
        self.filename = filename
        self.chunks = numpy.ndarray(shape=(1024), dtype=numpy.object_)
        self.sectors = []
        self.loaded_chunks = dict()
        self.loaded_indices = set()
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        if path.isfile(filename):
            with open(self.filename, 'rb') as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(0)

                self.sectors.append(Sector(0, 2))
                for i in range(1024):
                    offset = int.from_bytes(f.read(3), byteorder='big', signed=False)
                    sector_count = int.from_bytes(f.read(1), byteorder='big', signed=False)
                    if offset >= 2 and sector_count > 0:
                        sector = Sector(offset, sector_count)
                        self.chunks[i] = sector
                        bisect.insort(self.sectors, sector)
                    else:
                        self.chunks[i] = None
    
    def save(self):
        output_path = self.filename + '.out'
        with open(output_path, 'wb') as outfile:
            with open(self.filename, 'rb') as infile:
                outfile.write(__null_sector)
                outfile.write(__null_sector)
                outfile.seek(0)
                for i in range(1024):
                    sect = self.chunks[i]
                    if sect is not None:
                        outfile.write(sect.offset.to_bytes(3, 'big', signed=False)
                        outfile.write(sect.count.to_bytes(1, 'big', signed=False))
                    else:
                        outfile.write(b'\x00\x00\x00\x00')
                utc = arrow.utcnow()
                utc_ts = utc.int_timestamp
                utc_bs = utc_ts.to_bytes(4, 'big', signed=False)
                for i in range(1024):
                    outfile.write(utc_bs)
                for i in range(1024):
                    sect = self.chunks[i]
                    if sect is not None:

    
    def set_sector(self, index, sector):
        self.chunks[index] = sector
        bisect.insort(self.sectors, sector)

    def delete_sector(self, index):
        if 0 <= index < 1024:
            sect = self.chunks[index]
            if sect != None:
                sect_ind = bisect.bisect_left(self.sectors, sect)
                if sect_ind != len(self.sectors) and self.sectors[sect_ind] == sect:
                    del self.sectors[sect_ind]
                self.chunks[index] = None
    
    def get_free(self, size_in_bytes,insert=True):
        sector_count = math.ceil(size_in_bytes / 4096)
        for i in range(0, len(self.sectors) - 1):
            dist_between = self.sectors[i+1].offset - self.sectors[i].end
            if dist_between >= sector_count:
                sector = Sector(self.sectors[i].end, sector_count)
                if insert:
                    bisect.insort(self.sectors, sector)
                return sector
        #   We reached the end of the file, so we'll need to append some sectors.
        end_sector = self.sectors[-1]
        sector = Sector(end_sector.end, sector_count)
        if insert:
            bisect.insort(self.sectors, sector)
        return sector

    def read_chunk(self, offsetX : int, offsetZ : int) -> chunk.Chunk:
        result = self.read_chunk_tag(offsetX, offsetZ)
        if result is not None:
            ch = chunk.Chunk(result[0])
            self.loaded_chunks[offsetX, offsetZ] = ch
            self.loaded_indices.add(RegionFile.get_index(offsetX, offsetZ))
            return ch
    
    def read_chunk_tag(self, offsetX : int, offsetZ : int) -> nbt.nbt_tag:
        """
        Reads the chunk (decompressed) from the region file and returns the NBT.
        """
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        decompressed_data = None
        ind = ((offsetX & 31) + (offsetZ & 31) * 32)

        with open(self.filename,'rb') as f:
            f.seek(ind * 4)
            chunk_offset = int.from_bytes(f.read(3),'big')
            if chunk_offset == 0:
                return
            f.seek(chunk_offset * 4096)
            data_length = int.from_bytes(f.read(4),'big')
            compression_type = int.from_bytes(f.read(1),'big')
            # 1 GZip, 2 Zlib, 3 uncompressed
            if compression_type == 2:
                return nbt.load(zlib.decompress(f.read(data_length-1)))
            elif compression_type == 1:
                return nbt.load(gzip.decompress(f.read(data_length-1)))
            elif compression_type == 3:
                return nbt.load(f.read(data_length-1))
    
    def write_chunk(self, chunk_ : chunk.Chunk):
        tag = chunk_.to_nbt()
        self.write_chunk_tag(chunk_.xPos, chunk_.zPos, tag)
    
    def write_chunk_tag(self, offsetX : int, offsetZ : int, chunk_tag : nbt.nbt_tag):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        chunk_data = zlib.compress(nbt.dump(chunk_tag))
        ind = ((offsetX & 31) + (offsetZ & 31) * 32)
        if self.chunks[ind] != None:
            self.delete_sector(ind)
        free = self.get_free(len(chunk_data)+5)
        self.set_sector(ind, free)
        self.chunks[ind] = free
        #ensure the capacity of our file:
        with open(self.filename, 'ab') as f:
            offset = free.offset * 4096
            f.seek(offset)
            f.write((len(chunk_data) + 1).to_bytes(4, 'big', signed=False))
            f.write(b'\x02')
            f.write(chunk_data)

    
    
    
    def read_chunk_raw(self, offsetX : int, offsetZ : int) -> bytes:
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        decompressed_data = None
        ind = ((offsetX & 31) + (offsetZ & 31) * 32)

        with open(self.filename,'rb') as f:
            f.seek(ind * 4)
            chunk_offset = int.from_bytes(f.read(3),'big')
            if chunk_offset == 0:
                return
            f.seek(chunk_offset * 4096)
            data_length = int.from_bytes(f.read(4),'big')
            compression_type = int.from_bytes(f.read(1),'big')
            # 1 GZip, 2 Zlib, 3 uncompressed
            if compression_type == 2:
                return zlib.decompress(f.read(data_length-1))
            elif compression_type == 1:
               return gzip.decompress(f.read(data_length-1))
            elif compression_type == 3:
                return f.read(data_length-1)
    
    def has_chunk(self, offsetX : int, offsetZ : int) -> bool:
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        ind = ((offsetX & 31) + (offsetZ & 31) * 32)
        with open(self.filename, 'rb') as f:
            f.seek(ind * 4)
            return int.from_bytes(f.read(3), 'big') != 0