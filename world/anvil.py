import os
import gzip
import zlib
import io
from . import nbt

class RegionFile:

    __slots__ = ('filename')

    def __init__(self, filename : str):
        self.filename = filename
    
    def read_chunk(self, offsetX : int, offsetZ : int) -> nbt.nbt_tag:
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