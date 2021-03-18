"""
nbtutil contains functions to help with NBT.
"""
import numpy
#   int
#   float
#   string
#   list
#   dict
#   bool

__convertible_types = {
    int,float,str,list,dict,bool,bytes,bytearray,
    numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64,
    numpy.float16, numpy.float32, numpy.float64,
    numpy.ndarray
}

def isconvertable(type_ : type):
    return type_ in __convertible_types