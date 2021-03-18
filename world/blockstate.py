"""
This module is for the block state registry. All block states are registered here.
"""
from enum import Enum

class BlockState:
    __slots__ = ('unique_key', 'id', 'properties')
    def __init__(self, id, properties):
        self.unique_key = object()
        self.id = id
        self.properties = properties
    
    def __repr__(self):
        return f'BlockState({repr(self.id)}, {repr(self.properties)})'

_id_state_registry = dict()
_key_state_registry = dict()

def find(id, props = {}):
    """
    Finds the state in the registry.
    """
    if id in _id_state_registry:
        for p in _id_state_registry[id]:
            if p.properties == props:
                return p
    return _key_state_registry.get(id, None)

def register(id : str, props = None) -> BlockState:
    """
    First tries to find the state if it already exists, then creates it if it does not.
    The return value is the BlockState that was registered.
    """
    state = find(id, props)
    if state:
        return state
    state = BlockState(id, props)
    _key_state_registry[state.unique_key] = state
    if id in _id_state_registry:
        _id_state_registry[id].append(state)
    else:
        _id_state_registry[id] = [state]
    return state

class blocks(Enum):
    air = register('minecraft:air')
    bedrock = register('minecraft:bedrock')