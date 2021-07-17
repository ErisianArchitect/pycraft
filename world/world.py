"""
The goal of this file is to provide a class for Minecraft worlds.
There should be a class called World for worlds, and then we can have
another class called ChunkManager.
ChunkManager will load, save, create, and store chunks.
The World class will "ask" the ChunkManager for a chunk, and the
ChunkManager will return the chunk if it is already loaded, or it will
load and return the chunk.
If the chunk does not exist, the ChunkManager must then decide to
create a new chunk, and if it decides to create a new chunk, it must
decide how that chunk is created.
This leaves an opening for world generators.
"""

from abc import ABC, abstractmethod
from . import region

class ChunkManager(ABC):
    @abstractmethod
    def get(self, x : int, y : int, z : int):
        pass

    @abstractmethod
    def save(self):
        pass

class AnvilChunkManager(ChunkManager):
    __slots__ = ('region_folder', 'regions')

    def __init__(self, region_folder):
        self.region_folder = region_folder

    def get(self, x : int, y : int, z : int):
        pass

    def save(self):
        pass

class World:
    pass