"""
This module is for the block state registry. All block states are registered here.
"""

class BlockState:
    __slots__ == ('key', 'id', 'properties')
    def __init__(self, id, properties):
        self.unique_key = object()
        self.id = id
        self.properties = properties

_id_state_registry = dict()
_key_state_registry = dict()

def find_state(id, props):
    if id in _state_registry:
        for p in _id_state_registry[id]:
            if p.properties == props:
                return p
    return _key_state_registry.get(id, None)

def register_state(id : str, props):
    state = find_state(id, props)
    if state:
        return state
    state = BlockState(id, props)
    _key_state_registry[state.unique_key] = state
    if id in _id_state_registry:
        _id_state_registry.append(state)
    else:
        _id_state_registry[id] = [state]
    return state