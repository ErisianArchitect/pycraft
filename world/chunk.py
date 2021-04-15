import math
import numpy
from . import util
from . import nbt
from . import blockregistry
from . import blocks


__all__ = ['Chunk', 'ChunkSection']

# TODO: Research
#       We'll need to update a lot of different stuff in the chunk in order for it to be more valid to Minecraft.
#       Things to consider are things like heightmaps, TileEntities, water/lava sources, light sources, etc.

# TODO: nibble4() and chunk_block_index are likely useless, so we might remove them later.
def nibble4(arr, index):
    return arr[index//2] & 0x0F if index % 2 == 0 else (arr[index//2]>>4) & 0x0F

def chunk_block_index(*args):
    if len(args) == 3:
        return args[1]*256+args[2]*16+args[0]
    else:
        return args[0][1]*256+args[0][2]*16+args[0][0]

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
    #state_index is the index in the array of longs that our value will be injected to.
    state_index = full_index // vpl
    #value_offset represents the number of bits to shift to form our mask for setting the value.
    value_offset = (full_index % vpl) * bitsize
    #block_state will be a 64 bit integer
    block_state = block_states[state_index]
    #Injecting our value to the block_state
    block_states[state_index] = (block_state & ~(mask << value_offset)) | (value << value_offset)

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
                states.append(blockregistry.register(name, props))
            
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
            palette = [blockregistry.find(x) for x in set(self.Blocks)]
            palette_table = { v.unique_key : i for i, v in enumerate(palette) if v is not None }
            states = numpy.zeros(shape=(calc_blockstates_size(len(palette))), dtype='>i8')

            for i in range(4096):
                inject_index(i, len(palette), states, palette_table[self.Blocks[i]])
            
            tag_items['BlockStates'] = nbt.t_longs(states)

            palette_items = [blockregistry.BlockState.to_nbt(v) for v in palette]

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
        if self.Blocks is None:
            return blocks.air
        return blockregistry.find(self.Blocks[y*256 + z*16 + x])
    
    # TODO: Update lighting and heightmaps
    def set(self, x, y, z, id, props = None):
        if self.Blocks is None:
            return
        if type(id) == str:
            state = blockregistry.register(id, props)
            self.Blocks[y*256 + z*16 + x] = state.unique_key
        elif type(id) == blockregistry.BlockState:
            self.Blocks[y*256+z*16+x] = id.unique_key

class Heightmaps:

    @staticmethod
    def unpack_heightmap(arr):
        """
        This function will take a numpy array of longs and convert it to 256 unsigned int16s representing the heights.
        """
        result = numpy.zeros(shape=(256,), dtype=numpy.uint16)
        #   This is a tough one-liner, so let me break it down.
        #   There should be 37 values in arr with 7 values packed into each.
        #   So in order extract a value by index, we must figure out the index within arr first.
        #   To do that, we simply use the floor division operator to divide the full index by 7.
        #   Example:
        #       >>> 43 // 7
        #       6
        #   This means that the index in the array that we will find our value is 6.
        #   Next, we must extract from the value at that index.
        #   To do so, we create a bit mask of 9 bits. (0b111111111 or 0x1ff)
        #   We need to shift that mask to the bits that represent the value we want to extract.
        #   To get the number of bits to shift, you simply modulo our full index by 7.
        #       >>> 43 % 7
        #       1
        #   So now we know that the index should be 1.
        #   We multiply that value by 9 to get our shift count.
        #       >>> 1 * 9
        #       9
        #   We'll need to use this same value later to shift our value BACK to the 0 index.
        #   We now can left-shift our mask by 9 bits.
        #       >>> 0x1FF << 9
        #       261632
        #   With our new bit mask, we simply apply the bitwise AND operator with our arr value.
        #       >>> arr[6] & 261632
        #   We can then get our final value by right-shifting back to 0. Remember that value from earlier?
        #       >>> (arr[6] & 261632) >> 9
        #   And that is how this one-liner works.
        #   I know this comment seems excessive, but I would hate for anyone to look at this gargantuan
        #   one-liner and think to themselves "What the fuck does this even do?"
        #   The anwer to that question is that it extracts a 9-bit value from a 64-bit value within an
        #   array of 64-bit values.
        extract = lambda index: (result[index // 7] & (0x1FF << ((index % 7) * 9))) >> ((index % 7) * 9)
        for i in range(256):
            result[i] = extract(i)
        return result
    
    @staticmethod
    def pack_heightmap(arr):
        mask = 0x1FF
        result = numpy.zeros(shape=(37,), dtype=numpy.int64)
        # This does the opposite of what extract does in unpack_heightmap.
        # this will return a new 63 bit (or less) long value with value injected at index.
        inject = lambda long, index, value: (long & ~(0x1FF << (index * 9))) | (value << (index * 9))
        for i in range(256):
            resindex = i // 7
            subind = i % 7
            result[resind] = inject(result[resind], subind, arr[i])
        return result
        

    __slots__ = ('ocean_floor', 'motion_blocking_no_leaves', 'motion_blocking', 'world_surface')

    def __init__(self, heightmaps_tag : nbt.t_compound):
        self.ocean_floor = unpack_heightmap(heightmaps_tag['OCEAN_FLOOR'].data)
        self.motion_blocking_no_leaves = unpack_heightmap(heightmaps_tag['MOTION_BLOCKING_NO_LEAVES'].data)
        self.motion_blocking = unpack_heightmap(heightmaps_tag['MOTION_BLOCKING'].data)
        self.world_surface = unpack_heightmap(heightmaps_tag['WORLD_SURFACE'].data)
    
    def to_nbt(self):
        pass


# TODO: Refactor Chunk to be able to load directly from stream rather than from NBT.
# TODO: Figure out what data to populate a new chunk with.
# TODO: Currently, the bottom and top ChunkSections are not valid sections to place blocks in. Figure out how to change that.
class Chunk:
    __slots__ = ('Biomes', 'CarvingMasks', 'DataVersion', 'Entities', 'Heightmaps', 'InhabitedTime', 'LastUpdate', 'Lights', 'LiquidTicks', 'LiquidsToBeTicked', 'PostProcessing', 'Sections', 'Status', 'Structures', 'TileEntities', 'TileTicks', 'ToBeTicked', 'xPos', 'zPos','isDirty')

    _level_tag_slots = ('Biomes', 'CarvingMasks', 'Entities', 'Heightmaps', 'Lights', 'LiquidTicks', 'LiquidsToBeTicked', 'PostProcessing', 'Status', 'Structures', 'TileEntities', 'TileTicks', 'ToBeTicked')

    # Tags that will not have values:
    #   CarvingMasks
    #   Lights (I believe this is used for worldgen)
    #   LiquidsToBeTicked
    def __init__(self, chunk_tag):
        self.isDirty = False
        self.DataVersion = chunk_tag['DataVersion'].value
        level_tag = chunk_tag['Level']

        self.xPos = level_tag['xPos'].value
        self.zPos = level_tag['zPos'].value

        self.InhabitedTime = level_tag['InhabitedTime'].value
        self.LastUpdate = level_tag['LastUpdate'].value

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

        level_data['InhabitedTime'] = nbt.t_long(self.InhabitedTime)
        level_data['LastUpdate'] = nbt.t_long(self.LastUpdate)

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
        self.set(coord[0], coord[1], coord[2], blocks.air)
    
    def remove(self, x, y, z):
        self.set(x,y,z, 'minecraft:air')

    def get(self,x,y,z):
        sect_y = y // 16
        if -1 <= sect_y < 16:
            chunk_y = y % 16
            if sect_y in self.Sections:
                return self.Sections[sect_y].get(x,chunk_y, z)
            else:
                return blocks.air
    
    def set(self, x, y, z, id, props={}):
        # TODO: Check if the block will actually change anything before setting the isDirty flag.
        self.isDirty = True
        # The sections are 16 blocks high, so we can get our section index by dividing the y value
        # by 16.
        sect_y = y // 16
        # We can then get the local y value.
        chunk_y = y % 16
        # Constrain to 0-15 because we do not want to set blocks on any sections that may be outside
        # of that range.
        if 0 <= sect_y < 16:
            if sect_y in self.Sections:
                self.Sections[sect_y].set(x,chunk_y,z,id, props)
            else:
                sect = ChunkSection(sect_y)
                self.Sections[sect_y] = sect
                sect.set(x,chunk_y,z,id, props)