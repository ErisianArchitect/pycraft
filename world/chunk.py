import math
from . import util
from . import nbt
from . import blockstate

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
    bitsize = max(math.ceil(math.log2(palette_size)), 4)
    #vpl = values per long
    vpl = 64 // bitsize
    mask = 2**bitsize-1
    state_index = full_index // vpl
    value_offset = (full_index % vpl) * bitsize
    slot = block_states[state_index]
    return (slot & (mask << value_offset)) >> value_offset

class BlockState:
    __slots__ = ('Name', 'Properties')
    def __init__(self, name : str, properties : dict):
        self.Name = name
        self.Properties = properties
    

class BlockStatePalette:
    __slots__ = ('items',)

    def __init__(self, palette_tag : nbt.nbt_tag):
        items = palette_tag.items
        self.items = 


class ChunkSection:

    __slots__ = ('Name', 'BlockLight','Blocks','SkyLight','Y')
    def __init__(self, section_tag):
        self.Name = section_tag.name
        self.BlockLight = bytearray(4096)
        self.SkyLight = bytearray(4096)
        tmp = section_tag['BlockLight']
        for i in range(2048):
            self.BlockLight[i*2] = tmp.data[i] & 0x0F
            self.BlockLight[i*2+1] = (tmp.data[i] >> 4) & 0x0F
        tmp = section_tag['SkyLight']
        for i in range(2048):
            self.SkyLight[i*2] = tmp.data[i] & 0x0F
            self.SkyLight[i*2+1] = (tmp.data[i] >> 4) & 0x0F
        #   I can make BlockStates an array with a size of 4096 for ease of use.
        #   I can also translate the palette into some other data structure.
        self.Blocks = list()
        states_tag = section_tag['BlockStates']
        palette = section_tag['Palette']

        states = list()

        for v in palette.data:
            name = v.Name.value
            props = {}
            if 'Properties' in v:
                props = { k : val.value for k, val in v.Properties.data.items() }
            states.append(blockstate.register(name, props))

        for i in range(4096):
            ind = extract_index(i, len(palette.data), states.data)
            self.Blocks.append(states[ind].unique_key)

        self.Y = section_tag['Y'].value
    
    def get_block(self, x, y, z):
        ind = y*256 + z*16 + x
        return blockstate.find(self.Blocks[ind])
    
    def set_block(self, x, y, z, id, props = {}):
        ind = y*256 + z*16 + x
        state = blockstate.register(id, props)
        self.Block[ind] = state.unique_key
    
    def to_nbt(self) -> nbt.nbt_tag:
        tag_items = list()

        # BlockLight
        block_light = nbt.TAG_Byte_Array('BlockLight', )


class LevelData:
    __slots__ = ('Biomes', 'CarvingMasks', 'Entities', 'Heightmaps', 'LastUpdate','Lights','LiquidsToBeTicked','LiquidTicks','InhabitedTime','PostProcessing','Sections','Status','TileEntities','TileTicks','ToBeTicked','Structures','xPos','zPos')
    def __init__(self, level_tag):
        #   Over time, as I understand more about the file format and how it translates
        #   to Minecraft, I can move these various tags into their own classes.

        sections = level_tag['Sections']

        self.Sections = list()

        for section in sections:
            self.Sections.append(ChunkSection(section))

        self.Biomes = level_tag['Biomes']
        self.CarvingMasks = level_tag['CarvingMasks']
        self.Entities = level_tag['Entities']
        self.Heightmaps = level_tag['Heightmaps']
        self.LastUpdate = level_tag['LastUpdate']
        self.Lights = level_tag['Lights']
        self.LiquidsToBeTicked = level_tag['LiquidsToBeTicked']
        self.LiquidTicks = level_tag['LiquidTicks']
        self.InhabitedTime = level_tag['InhabitedTime']
        self.PostProcessing = level_tag['PostProcessing']
        self.Status = level_tag['Status']
        self.TileEntites = level_tag['TileEntities']
        self.TileTicks = level_tag['TileTicks']
        self.ToBeTicked = level_tag['ToBeTicked']
        self.Structures = level_tag['Structures']
        self.xPos = level_tag['xPos'].value
        self.zPos = level_tag['zPos'].value

class Chunk:
    __slots__ = ('DataVersion','Level')