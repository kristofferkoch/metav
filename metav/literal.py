# This file is part of metav.

# metav is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# metav is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.

# You should have received a copy of the GNU General Public License
# along with metav.  If not, see <http://www.gnu.org/licenses/>.

import re
from .vast import Expression, _get_end

UNSIZED = re.compile(r'^[0-9]+$')
BIN     = re.compile(r'^(?P<size>[0-9]*)\'[bB](?P<bin>[01_zxZX?]+)$')
DEC     = re.compile(r'^(?P<size>[0-9]*)\'[dD](?P<dec>[0-9_]+)$')
HEX     = re.compile(r'^(?P<size>[0-9]*)\'[hH](?P<hex>[0-9a-fA-FzxZX?_]+)$')

class VerilogNumber(Expression):
    def __init__(self, string):
        if type(string) == str:
            self.pos = ((),())
        else:
            self.pos = (string.pos_stack, _get_end(string))
            string = string.value
        self.orig = string
        unz = UNSIZED.match(string)
        if unz:
            self.value = int(string)
            self.size  = 32
            self.xmask = 0
            self.zmask = 0
            return
        bin_ = BIN.match(string)
        if bin_:
            s = bin_.group('bin').replace('_','').replace('?', 'z').lower()
            value = s.replace('z','0').replace('x', '0')
            self.value = int(value, 2)
            self._setsize(bin_.group('size'))
            x = s.replace('1','0').replace('z','0').replace('x','1')
            self.xmask = int(x, 2)
            z = s.replace('1','0').replace('z','1').replace('x','0')
            self.zmask = int(z, 2)
            return
        hex_ = HEX.match(string)
        if hex_:
            s = hex_.group('hex').replace('_','').replace('?', 'z').lower()
            value = s.replace('z','0').replace('x','0')
            self.value = int(value, 16)
            self._setsize(hex_.group('size'))
            x = re.sub(r'[a-f0-9z]', '0', s).replace('x', 'f')
            self.xmask = int(x, 16)
            z = re.sub(r'[a-f0-9x]', '0', s).replace('z', 'f')
            self.zmask = int(z, 16)
            return
        dec = DEC.match(string)
        if dec:
            s = dec.group('dec').replace('_','')
            self.value = int(s, 10)
            self._setsize(dec.group('size'))
            self.xmask = 0
            self.zmask = 0
            return
            
        assert False, "Unmatched verilog number"
    def _setsize(self, sizestr):
        if sizestr:
            self.size = int(sizestr)
            assert self.size > 0
        else:
            self.size = 32
        
    def asbin(self):
        chars = []
        for i in range(self.size):
            mask = 1<<i
            restmask = ~(mask - 1)
            v = (self.value>>i) & 1
            if not (self.xmask & restmask
                    or self.zmask & restmask
                    or self.value & restmask):
                break
            if self.xmask & mask:
                assert v == 0
                chars.insert(0, 'x')
            elif self.zmask & mask:
                assert v == 0
                chars.insert(0, 'z')
            else:
                chars.insert(0,str(v))
        if not chars:
            chars = ['0']
        return "%d'b%s" % (self.size, ''.join(chars))

    def __repr__(self):
        if self.orig:
            return "VerilogNumber(\"%s\")" % (self.orig)
        return "VerilogNumber(\"%s\")" % (self.asbin())
    def __str__(self):
        return self.orig
    def __int__(self):
        return self.value
    def __len__(self):
        return self.size

class String(VerilogNumber):
    def __init__(self, string):
        self.pos = (string.pos_stack, _get_end(string))
        string = string.value
        self.value = 0 # TODO
        self.xmask = 0
        self.zmask = 0
        self.size = len(string)*8
        self.orig = string

class VerilogReal(Expression):
    def __init__(self, string):
        self.string = string
