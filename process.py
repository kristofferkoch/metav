#!/usr/bin/python3
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

from metav.preproc import preproc
from metav.lex import vLexer
from metav.parse import vParser
import os.path

def _find_file(modulename, modpath=('.',)):
    if not modulename.endswith(".v"):
        modulename += ".v"
    for p in modpath:
        filename = os.path.join(p, modulename)
        #print("Trying " + filename)
        if os.path.isfile(filename):
            return filename
    raise IOError("Could not find "+modulename + " in " + ', '.join(modpath))

def process(top, modpath=('.',), incpath=('.',), debug=False, module_dict={}):
    if top in module_dict:
        return module_dict[top]
    lexer, codes = vLexer()
    parser = vParser()
    filename = _find_file(top, modpath=modpath)
    p = preproc(filename, incpath=incpath)
    print(p)
    modules = parser.parse(input=p, lexer=lexer, debug=debug)
    for module in modules:
        module_dict[module.name.value] = module
    for module in modules:
        name = module.name.value
        if name != top: continue
        
        for iname in module.insts:
            inst = module.insts[iname]
            if hasattr(inst, 'module'): continue
            inst.module = process(iname, modpath=modpath, incpath=incpath,
                                  debug=debug, module_dict=module_dict)
            inst.module.parent = module
        for code in codes.get(name, ()):
            exec(code, {'module': module,
                        'get_module': None,
                        'out': None})
        return module
    assert False
    
    
    

if __name__ == "__main__":
    import sys
    top = sys.argv[1]
    process(top, modpath=("test",), incpath=("test/include",))
    
    
