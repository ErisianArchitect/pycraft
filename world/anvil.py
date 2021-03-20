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

null_sector = bytes(4096)

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
    """
    Class used to represent Minecraft Region files in the Anvil file format.
    This function includes functions for loading chunks, and will have functions for saving in the future.
    """
    #   This class looks AWFUL right now. We can fix that.
    #   I'm thinking of extracting all the data from the region file then
    #   putting each chunk into a seperate files for easy modification.
    #   Once the user is done modifying the chunks, they can save them back into the region file.

    __slots__ = ('filename','chunks','sectors','loaded_chunks','loaded_indices')

    @staticmethod
    def get_index(x : int, z : int):
        """
        Returns an index where 0 <= index < 1024.
        : int x : A value between 0 and 31.
        : int z : A value between 0 and 31.
        """
        return ((x & 31) | ((z & 31) << 5))
    
    @staticmethod
    def expand_index(index) -> tuple:
        """
        This will return a tuple containing the two values stored in index.
        The max value of index is 1023, the minimum is 0.
        This means that index has 10 bits.
        The first 5 bits are the first value in the tuple returned.
        The second 5 bits are the second value.
        """
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

        """
        This function will first create a temporary output file to write to.
        It will then read through the region file extracting data to write to the output file.
        When it encounters a chunk that has been loaded, it will write that chunk to the file instead
        of the data that is in the region file.
        """
        # TODO: Check if the region file will even change.
        #       This can be accomplished by setting a "dirty" flag on the region file and chunks.
        output_path = self.filename + '.out'
        with open(output_path, 'wb') as outfile:
            with open(self.filename, 'rb') as infile:
                #   First write 8192 bytes to the file.
                #   This is where sector information and timestamps are stored.
                #   TODO: Don't forget to change the sector data after writing to the region file.
                outfile.write(null_sector)
                outfile.write(null_sector)

                # First write all the data while saving the sector information.
                # After writing all the data, seek to the beginning of the file and write the header data.

                new_sectors = numpy.ndarray(shape=(1024,), dtype=numpy.object_)

                for i in range(1024):

                    new_sect = Sector(0,0)

                    file_offset = outfile.tell()

                    new_sect.offset = file_offset // 4096

                    if i in self.loaded_indices:

                        coord = RegionFile.expand_index(i)
                        loaded_chunk = self.loaded_chunks[coord]
                        if loaded_chunk is not None:
                            # TODO: Eventually I plan on writing a save function for Chunk that doesn't require converting to NBT.
                            chunk_nbt = loaded_chunk.to_nbt()
                            chunk_data = zlib.compress(nbt.dump(chunk_nbt))

                            chunk_size = len(chunk_data)

                            data_length = chunk_size + 1

                            total_size = chunk_size + 5

                            pad_size = 0

                            if (total_size % 4096) != 0:
                                pad_size = 4096 - (total_size % 4096)
                            
                            padded_size = total_size + pad_size

                            new_sect.count = padded_size // 4096

                            outfile.write(data_length.to_bytes(4, 'big', signed=False))
                            outfile.write(b'\x02')

                            outfile.write(chunk_data)
                            outfile.write(bytes(pad_size))
                    else:
                        #   The chunk hasn't been loaded, so we'll just write it from the infile.
                        sect = self.chunks[i]
                        if sect is not None:
                            infile.seek(sect.offset * 4096)
                            outfile.write(infile.read(4096 * sect.count))
                            new_sect.count = sect.count
                        else:
                            new_sect.offset = 0
                            new_sect.count = 0
                    new_sectors[i] = new_sect if new_sect.count > 0 and new_sect.offset >= 2 else None
                #   Now we will write the sector information to the file.
                outfile.seek(0)
                null_data4 = b'\x00\x00\x00\x00'
                for i in range(1024):
                    if new_sectors[i] is not None:
                        outfile.write(new_sectors[i].offset.to_bytes(3, 'big', signed=False))
                        outfile.write(new_sectors[i].count.to_bytes(1, 'big', signed=False))
                    else:
                        outfile.write(null_data4)
        # Now we are done writing to the output file, so we will swap it with the original.
        os.replace(output_path, self.filename)

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