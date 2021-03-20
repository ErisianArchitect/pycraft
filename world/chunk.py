import math
import numpy
from . import util
from . import nbt
from . import block

"""
As of March 16th, 2021 at 4:45AM(UTC), this file is severely incomplete.
There is very little that is usable here, if anything at all.
Also, there are errors.
"""

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
    bitsize = max((palette_size - 1).bit_length(), 4)
    #vpl = values per long
    vpl = 64 // bitsize
    mask = 2**bitsize-1
    state_index = full_index // vpl
    value_offset = (full_index % vpl) * bitsize
    slot = int(block_states[state_index])
    return (slot & (mask << value_offset)) >> value_offset

def inject_index(full_index, palette_size, block_states, value):
    bitsize = max((palette_size - 1).bit_length(), 4)
    #vpl = values per long
    vpl = 64 // bitsize
    mask = 2**bitsize-1
    masked_value = value & mask
    state_index = full_index // vpl
    value_offset = (full_index % vpl) * bitsize

    tmp = block_states[state_index]

    tmp = (tmp & ~(mask << value_offset)) | (value << value_offset)

    block_states[state_index] = tmp

def calc_blockstates_size(palette_size):
    bitsize = max((palette_size - 1).bit_length(), 4)
    vpl = 64 // bitsize
    return (4096 // vpl) + (1 if (4096 % vpl) != 0 else 0)

# TODO: Refactor so that a ChunkSection can be loaded directly from streams.
class ChunkSection:

    @staticmethod
    def from_nbt(section_tag : nbt.nbt_tag):
        blocklight = None
        skylight = None
        y = None
        if 'Y' in section_tag:
            y = section_tag['Y'].value

        tmp = section_tag['BlockLight']
        if tmp is not None:
            blocklight = numpy.zeros(shape=(4096,), dtype='>i1')
            for i in range(2048):
                blocklight[i*2] = tmp.data[i] & 0x0F
                blocklight[i*2+1] = (tmp.data[i] >> 4) & 0x0F
        tmp = section_tag['SkyLight']
        if tmp is not None:
            skylight = numpy.zeros(shape=(4096,), dtype='>i1')
            for i in range(2048):
                skylight[i*2] = tmp.data[i] & 0x0F
                skylight[i*2+1] = (tmp.data[i] >> 4) & 0x0F
        #   I can make BlockStates an array with a size of 4096 for ease of use.
        #   I can also translate the palette into some other data structure.
        
        blocks = None
        states_tag = section_tag['BlockStates']
        palette = section_tag['Palette']

        
        if palette is not None and states_tag is not None:
            states = list()
            blocks = numpy.ndarray(shape=(4096,),dtype=numpy.object_)
            for v in palette.data:
                name = v.Name.value
                props = {}
                if 'Properties' in v:
                    props = { k : val.value for k, val in v.Properties.data.items() }
                states.append(block.register(name, props))
            
            for i in range(4096):
                ind = extract_index(i, len(palette.data), states_tag.data)
                blocks[i] = states[ind].unique_key
        
        return ChunkSection(y, blocks, blocklight, skylight)

    __slots__ = ('BlockLight','Blocks','SkyLight','Y')
    def __init__(self, y, blocks = None, blocklight = None, skylight = None):
        self.Y = y
        self.Blocks = blocks
        self.BlockLight = blocklight
        self.SkyLight = skylight
    
    def to_nbt(self):

        tag_items = {}

        if self.BlockLight is not None:
            blocklight = nbt.t_bytes(numpy.zeros(2048, dtype='>u1'))
            for i in range(2048):
                blocklight[i] = (self.BlockLight[i*2] & 0x0F) | ((self.BlockLight[i*2+1] & 0x0F) << 4)
            tag_items['BlockLight'] = blocklight

        if self.Blocks is not None:
            palette = [block.find(x) for x in set(self.Blocks)]
            palette_table = { v.unique_key : i for i, v in enumerate(palette) if v is not None }
            states = numpy.zeros(shape=(calc_blockstates_size(len(palette))), dtype='>i8')

            for i in range(4096):
                inject_index(i, len(palette), states, palette_table[self.Blocks[i]])
            
            tag_items['BlockStates'] = nbt.t_longs(states)

            palette_items = [block.BlockState.to_nbt(v) for v in palette]

            tag_items['Palette'] = nbt.t_list(nbt.t_compound, palette_items)

        if self.SkyLight is not None:
            skylight = nbt.t_bytes(numpy.zeros(2048, dtype='>u1'))
            for i in range(2048):
                skylight[i] = (self.SkyLight[i*2] & 0x0F) | ((self.SkyLight[i*2+1] & 0x0F) << 4)
            tag_items['SkyLight'] = skylight
        
        if self.Y is not None:
            tag_items['Y'] = nbt.t_byte(self.Y)
        
        return nbt.t_compound(tag_items)
    
    def get(self, x, y, z):
        return block.find(self.Blocks[y*256 + z*16 + x])
    
    def set(self, x, y, z, id, props = {}):
        if type(id) == str:
            state = block.register(id, props)
            self.Blocks[y*256 + z*16 + x] = state.unique_key
        elif type(id) == block.BlockState:
            self.Blocks[y*256+z*16+x] = id.unique_key

# TODO: Refactor Chunk to be able to load directly from stream rather than from NBT.
# TODO: Figure out what data to populate a new chunk with.
# TODO: Currently, the bottom and top ChunkSections are not valid sections to place blocks in. Figure out how to change that.
class Chunk:
    __slots__ = ('Biomes', 'CarvingMasks', 'DataVersion', 'Entities', 'Heightmaps', 'InhabitedTime', 'LastUpdate', 'Lights', 'LiquidTicks', 'LiquidsToBeTicked', 'PostProcessing', 'Sections', 'Status', 'Structures', 'TileEntities', 'TileTicks', 'ToBeTicked', 'xPos', 'zPos','isDirty')

    _level_tag_slots = ('Biomes', 'CarvingMasks', 'Entities', 'Heightmaps', 'InhabitedTime', 'LastUpdate', 'Lights', 'LiquidTicks', 'LiquidsToBeTicked', 'PostProcessing', 'Status', 'Structures', 'TileEntities', 'TileTicks', 'ToBeTicked')

    def __init__(self, chunk_tag):
        self.isDirty = False
        self.DataVersion = chunk_tag['DataVersion'].value
        level_tag = chunk_tag['Level']

        self.xPos = level_tag['xPos'].value
        self.zPos = level_tag['zPos'].value

        sections = level_tag['Sections']

        self.Sections = dict()

        for section in sections.data:
            tmp = ChunkSection.from_nbt(section)
            self.Sections[tmp.Y] = tmp

        for slot in Chunk._level_tag_slots:
            if slot in level_tag:
                setattr(self, slot, level_tag[slot])
            else:
                setattr(self, slot, None)

    def to_nbt(self):
        items = {}
        items['DataVersion'] = nbt.t_int(self.DataVersion)

        level_data = {}

        sections = []
        sect_keys = list(self.Sections.keys())
        sect_keys.sort()
        for key in sect_keys:
            sections.append(self.Sections[key].to_nbt())
        
        level_data['Sections'] = nbt.t_list(nbt.t_compound, sections)

        for key in Chunk._level_tag_slots:
            tmp = getattr(self, key, None)
            if tmp is not None:
                level_data[key] = tmp
        
        level_data['xPos'] = nbt.t_int(self.xPos)
        level_data['zPos'] = nbt.t_int(self.zPos)
        
        items['Level'] = nbt.t_compound(level_data)

        return nbt.t_compound(items)

    
    def __getitem__(self, coord):
        if type(coord) == tuple and len(coord) == 3:
            return self.get(coord[0], coord[1], coord[2])
    
    def __setitem__(self, coord, value):
        self.set(coord[0], coord[1], coord[2], *value)
    
    def __delitem__(self, coord):
        self.set(coord[0], coord[1], coord[2], block.air)
    
    def remove(self, x, y, z):
        self.set(x,y,z, 'minecraft:air')

    def get(self,x,y,z):
        sect_y = y // 16
        if -1 <= sect_y < 16:
            chunk_y = y % 16
            if sect_y in self.Sections:
                return self.Sections[sect_y].get(x,chunk_y, z)
            else:
                return block.air
    
    def set(self, x, y, z, id, props={}):
        self.isDirty = True
        sect_y = y // 16
        chunk_y = y % 16
        if -1 <= sect_y < 16:
            if sect_y in self.Sections:
                self.Sections[sect_y].set(x,chunk_y,z,id, props)
            else:
                sect = ChunkSection(sect_y)
                self.Sections[sect_y] = sect
                sect.set(x,chunk_y,z,id, props)