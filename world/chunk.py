import util
import nbt

class BlockStatePalette:
    __slots__ = ('items',)

    def __init__(self, palette_tag : nbt.nbt_tag):
        self.items = palette_tag.items

class ChunkSection:

    __slots__ = ('Name', 'BlockLight','BlockStates','Palette','SkyLight','Y')
    def __init__(self, section_tag):
        self.Name = section_tag.name
        self.BlockLight = bytearray(4096)
        self.SkyLight = bytearray(4096)
        tmp = section_tag['BlockLight']
        for i in range(2048):
            self.BlockLight[i*2] = tmp.items[i] & 0x0F
            self.BlockLight[i*2+1] = (tmp.items[i] >> 4) & 0x0F
        tmp = section_tag['SkyLight']
        for i in range(2048):
            self.SkyLight[i*2] = tmp.items[i] & 0x0F
            self.SkyLight[i*2+1] = (tmp.items[i] >> 4) & 0x0F
        #   I can make BlockStates an array with a size of 4096 for ease of use.
        #   I can also translate the palette into some other data structure.
        self.BlockStates = list()
        states = section_tag['BlockStates']
        palette = section_tag['Palette']

        self.Palette = BlockStatePalette(palette)

        for i in range(4096):
            ind = util.extract_index(i, len(palette.items), states.items)
            self.BlockStates.append(ind)

        self.Y = section_tag['Y'].value
    
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
        self.xPos = level_tag['xPos']
        self.zPos = level_tag['zPos']

class Chunk:
    __slots__ = ('DataVersion','Level')