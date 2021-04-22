"""
This module is for the block state registry. All block states are registered here.
"""

import functools
from . import nbt

__all__ = ['BlockState', 'find', 'register']

# TODO: Add field to BlockState for callback to call when this blockstate is used.
# TODO:
class BlockState:
    __slots__ = ('unique_key', 'id', 'properties')

    def __new__(cls, id, properties=None):
        return register(id, properties)

    def __repr__(self):
        return f'BlockState({repr(self.id)}, {repr(self.properties)})'
    
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def to_nbt(state):
        items = {}
        items['Name'] = nbt.t_string(state.id)
        if state.properties is not None and len(state.properties) > 0:
            props = { k : nbt.t_string(v) for k, v in state.properties.items()}
            props_tag = nbt.t_compound(props)
            items['Properties'] = props_tag
        return nbt.t_compound(items)

# This registry is where ids are stored as minecraft ids.
# Each entry in this registry is a list of BlockState, each with different properties.
_id_state_registry = dict()
# This registry uses the BlockState's unique object as keys.
_key_state_registry = dict()

_mc_namespace = 'minecraft:'

def find(id, props = None):
    """
    Finds the state in the registry.
    """
    if type(id) == str and not id.startswith(_mc_namespace) and ':' not in id:
        id = _mc_namespace + id
    # First try the id registry
    if type(id) == str and id in _id_state_registry:
        for p in _id_state_registry[id]:
            if p.properties == props:
                return p
    else:
        # It's not in the id registry, so maybe it is a unique object id.
        return _key_state_registry.get(id, None)

def register(id : str, props = None) -> BlockState:
    """
    First tries to find the state if it already exists, then creates it if it does not.
    The return value is the BlockState that was registered.
    """
    if type(id) == str:
        if not id.startswith(_mc_namespace) and ':' not in id:
            id = _mc_namespace + id
        state = find(id, props)
        if state is not None:
            return state
        state = object.__new__(BlockState)
        state.id = id
        state.properties = props
        state.unique_key = object()
        _key_state_registry[state.unique_key] = state
        if state.id in _id_state_registry:
            _id_state_registry[state.id].append(state)
        else:
            _id_state_registry[id] = [state]
        return state