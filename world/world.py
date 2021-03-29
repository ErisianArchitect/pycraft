from abc import ABC, abstractmethod
from . import anvil


"""
#######################################################################
The goal of this file is to provide a class for Minecraft worlds.
There should be a class called World for worlds, and then we can have
another class called ChunkManager.
ChunkManager will load, save, create, and store chunks.
The World class will "ask" the ChunkManager for a chunk, and the
ChunkManager will return the chunk if it is already loaded, or it will
load and return the chunk.
"""

class ChunkManager(ABC):
    @abstractmethod
    def get(self, x : int, y : int, z : int):
        pass

    @abstractmethod
    def save(self):
        pass