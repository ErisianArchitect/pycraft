"""
This module is for the block state registry. All block states are registered here.
"""
import functools
from . import nbt

#   This metaclass allows us to call BlockState(<id>, <properties>) without creating a new BlockState.
#   This means that if a BlockState already exists, it will find it and return it.
class _blockstatemeta(type):
    @staticmethod
    def __call__(id, properties={}):
        state = register(id, properties)
        return state

class BlockState(metaclass=_blockstatemeta):
    __slots__ = ('unique_key', 'id', 'properties')

    def __repr__(self):
        return f'BlockState({repr(self.id)}, {repr(self.properties)})'
    
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def to_nbt(state):
        items = {}
        items['Name'] = nbt.t_string(state.id)
        if len(state.properties) > 0:
            props = { k : nbt.t_string(v) for k, v in state.properties.items()}
            props_tag = nbt.t_compound(props)
            items['Properties'] = props_tag
        return nbt.t_compound(items)


_id_state_registry = dict()
_key_state_registry = dict()

_mc_namespace = 'minecraft:'

def find(id, props = {}):
    """
    Finds the state in the registry.
    """
    if type(id) == str and not id.startswith(_mc_namespace) and ':' not in id:
        id = 'minecraft:' + id
    if id in _id_state_registry:
        for p in _id_state_registry[id]:
            if p.properties == props:
                return p
    return _key_state_registry.get(id, None)

def register(id : str, props = {}) -> BlockState:
    """
    First tries to find the state if it already exists, then creates it if it does not.
    The return value is the BlockState that was registered.
    """
    if not id.startswith(_mc_namespace) and ':' not in id:
        id = 'minecraft:' + id
    state = find(id, props)
    if state:
        return state
    state = BlockState()
    state.id = id
    state.properties = props
    state.unique_key = object()
    _key_state_registry[state.unique_key] = state
    if id in _id_state_registry:
        _id_state_registry[id].append(state)
    else:
        _id_state_registry[id] = [state]
    return state

air = register('minecraft:air')
bedrock = register('minecraft:bedrock')
stone = register('minecraft:stone')
dirt = register('minecraft:dirt')
grass = register('minecraft:grass_block')
barrier = register('minecraft:barrier')