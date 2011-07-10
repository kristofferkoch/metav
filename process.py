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
import metav.vast
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

def _execute_edit_plan(edit_plan):
    files = {}
    ropes = {}
    for p in edit_plan:
        instruction = p[0]
        
        if instruction in ("remove", "delete"):
            begin = p[1][0][-1]
            end   = p[1][1][-1]
            assert begin[0] == end[0] == 'file'
            assert begin[1] == end[1]
            filename = begin[1]
            begin = begin[2]
            end   = end[2]
            assert begin < end
        elif instruction == "insert":
            begin = p[1][-1]
            assert begin[0] == "file"
            filename = begin[1]
            begin = begin[2]
        if not filename in files:
            files[filename] = {
                'contents': open(filename).read(),
                'pos': 0,
                }
            ropes[filename] = []
            assert begin >= files[filename]['pos']
        if begin > files[filename]['pos']:
            to_copy = begin - files[filename]['pos']
            ropes[filename].append(files[filename]['contents'][:to_copy])
            files[filename]['pos'] += to_copy
            files[filename]['contents'] = files[filename]['contents'][to_copy:]

        if instruction in ("remove", "delete"):
            to_skip = end - begin
            files[filename]['pos'] += to_skip
            skipped = files[filename]['contents'][:to_skip]
            files[filename]['contents'] = files[filename]['contents'][to_skip:]

        if instruction == "remove":
            ropes[filename].extend(["/*metav_delete:", skipped, ":metav_delete*/"])
        elif instruction == "delete":
            pass
        elif instruction == "insert":
            insert = str(p[2])
            ropes[filename].extend(["/*metav_generated:*/\n",
                                    insert,
                                    "\n/*:metav_generated*/"])
        else:
            assert False, "Unknown edit plan instruction, "+repr(instruction)

    for filename in ropes:
        fd = open(filename+".out", 'w')
        for string in ropes[filename]:
            fd.write(string)
        fd.write(files[filename]['contents'])
        fd.close()
            

def process(top, modpath=('.',), incpath=('.',), debug=False, module_dict={}):
    if top in module_dict:
        return module_dict[top]
    lexer, codes = vLexer()
    parser = vParser()
    filename = _find_file(top, modpath=modpath)
    p, edit_plan = preproc(filename, state = {'incpath': incpath,})
    #print(p)
    modules = parser.parse(input=p, lexer=lexer, debug=debug)
    for module in modules:
        module_dict[module.name.value] = module
    for module in modules:
        name = module.name.value
        if name != top: continue
        
        for iname in module.insts:
            inst = module.insts[iname]
            if hasattr(inst, 'module'): continue
            # TODO: maybe do this lazily
            inst.module = process(iname, modpath=modpath, incpath=incpath,
                                  debug=debug, module_dict=module_dict)
            inst.module.parent = module
        module.edit_plan = edit_plan
        for code in codes.get(name, ()):
            exec(code, {'module': module,
                        'get_module': None,
                        'out': None,
                        'ast': metav.vast,
                        })
        return module
    assert False
    
    
    

if __name__ == "__main__":
    import sys
    top = sys.argv[1]
    mod = process(top, modpath=("test",), incpath=("test/include",))
    for p in mod.edit_plan:
        print(p)
    _execute_edit_plan(mod.edit_plan)
    
    
