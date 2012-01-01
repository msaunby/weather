# This Python file uses the following encoding: utf-8
import struct

from xdrlib import Unpacker
from minpydap.model import *


START_OF_SEQUENCE = '\x5a\x00\x00\x00'
END_OF_SEQUENCE = '\xa5\x00\x00\x00'

class DapUnpacker(object):
    def __init__(self, xdrdata, var):
        self._buf = xdrdata
        self.var = var
        self._pos = 0

    def getvalue(self):
        if isinstance(self.var, SequenceType):
            out = []
            mark = self._unpack_uint()
            while mark == 1509949440:
                var = self.var
                # Create a structure with the sequence vars:
                self.var = StructureType(name=self.var.name)
                self.var.update(var)
                out.append(self.getvalue())
                self.var = var
                mark = self._unpack_uint()

        elif isinstance(self.var, StructureType):
            out = []
            for child in self.var.walk():
                var = self.var
                self.var = child
                out.append(self.getvalue())
                self.var = var
            out = tuple(out)

        else:
            # Get data length.
            n = 1
            if getattr(self.var, 'shape', False):
                n = self._unpack_uint()
                if self.var.type not in [Url, String]:
                    self._unpack_uint()
                
            # Bytes are treated differently.
            if self.var.type == Byte:
                out = self._unpack_bytes(n)
                out = numpy.array(out, self.var.type.typecode)
            # As are strings...
            elif self.var.type in [Url, String]:
                out = self._unpack_string(n)
                out = numpy.array(out, self.var.type.typecode)
            else:
                i = self._pos
                self._pos = j = i + (n*self.var.type.size)
                #dtype = ">%s%s" % (self.var.type.typecode, self.var.type.size)
                #out = numpy.fromstring(self._buf[i:j], dtype=dtype)
                if self.var.type.typecode == 'i':
                    un = Unpacker(self._buf[i:j])
                    out = un.unpack_farray( n, un.unpack_int )
                elif (self.var.type.typecode == 'f') and (self.var.type.size == 8):
                    un = Unpacker(self._buf[i:j])
                    out = un.unpack_farray( n, un.unpack_double )
                elif (self.var.type.typecode == 'f') and (self.var.type.size == 4):
                    un = Unpacker(self._buf[i:j])
                    out = un.unpack_farray( n, un.unpack_float )
                else:
                    print "type", self.var.type.typecode
                    pass
            #print out
        return out

    def _unpack_uint(self):
        i = self._pos
        self._pos = j = i+4
        data = self._buf[i:j]
        if len(data) < 4:
            raise EOFError
        x = struct.unpack('>L', data)[0]
        try:
            return int(x)
        except OverflowError:
            return x

