import os
from os import path
import gzip
import zlib
import io
import numpy
import math
import bisect
from . import nbt
from . import chunk

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
        return (self.offset + self.count) <= other.offset
    
    def __gt__(self, other):
        return self.offset >= (other.offset + other.count)
    
    def __eq__(self, other):
        return self.offset == other.offset and self.count == other.count
    
    def intersects(self, other):
        if self.offset <= other.offset and self.end > other.offset:
            return True
        if other.offset <= self.offset and other.end > self.offset:
            return True
        return False
    
    def __repr__(self):
        return f'Sector(offset={self.offset}, count={self.count})'

class RegionFile:

    __slots__ = ('filename','items','sectors')

    def __init__(self, filename : str):
        self.filename = filename
        self.items = numpy.ndarray(shape=(1024), dtype=numpy.object_)
        self.sectors = None
        if path.isfile(filename):
            with open(self.filename, 'rb') as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(0)
                if size < 8192 or (size % 4096) != 0:
                    raise Exception('Invalid region file!')

                sect_count = size // 4096

                self.sectors = [Sector(0, 2)]
                for i in range(1024):
                    offset = int.from_bytes(f.read(3), byteorder='big', signed=False)
                    sector_count = int.from_bytes(f.read(1), byteorder='big', signed=False)
                    if offset >= 2 and sector_count > 0:
                        sector = Sector(offset, sector_count)
                        self.items[i] = sector
                        bisect.insort(self.sectors, sector)
    
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
        tag, _ = self.__read_chunk_tag(offsetX, offsetZ)
        return chunk.Chunk(tag)
    
    def read_chunk_tag(self, offsetX : int, offsetZ : int) -> nbt.nbt_tag:
        """
        Reads the chunk (decompressed) from the region file and returns the NBT.
        """
        if not os.path.exists(self.filename):
            return
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
    
    def read_chunk_raw(self, offsetX : int, offsetZ : int) -> bytes:
        if not os.path.exists(self.filename):
            return
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
            return False
        ind = ((offsetX & 31) + (offsetZ & 31) * 32)
        with open(self.filename, 'rb') as f:
            f.seek(ind * 4)
            return int.from_bytes(f.read(3), 'big') != 0