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

import re,os.path

def _include(m, incpath, defines, state):
    if not state['ifdef']: return ""
    filename = m.group(1)
    for p in incpath:
        p = os.path.join(p, filename)
        if os.path.isfile(p):
            return preproc(p, incpath, defines, state)
    raise IOError("Could not find %s in include path" % (filename, ))

def _macro(m, path, defines, state):
    if not state['ifdef']: return ""
    macro = m.group(1)
    #print("macro: "+macro)
    return "`macro(%s)%s`endmacro(%s)" % (macro, _process(defines[macro], path, defines, state), macro)

def _define(m, path, defines, state):
    if not state['ifdef']: return ""
    macro = m.group(1)
    value = m.group(2)
    #print("define "+macro+"="+value)
    assert macro not in defines
    defines[macro] = value
    return ""

def _drop(m, path, defines, state):
    return ""

def _ifdef(m, path, defines, state):
    var = m.group(1)
    if var not in defines:
        state['ifdef'] = False
    return ""
def _ifndef(m, path, defines, state):
    var = m.group(1)
    if var in defines:
        state['ifdef'] = False
    return ""
def _else(m, path, defines, state):
    state['ifdef'] = not state['ifdef']
    return ""
def _endif(m, path, defines, state):
    state['ifdef'] = True
    return ""

regexs = (
    (r'//[^\n]*',       None),
    (r'/\*metav_delete:', _drop),
    (r':metav_delete\*/', _drop),
    (r'/\*metav_generated:\*/(.|\n)*?/\*:metav_generated\*/', _drop),
    (r'/\*(.|\n)*?\*/', None),
    (r'"(\\"|[^"])*"', None),
    (r'`include\s+"([^"]+)"', _include),
    (r'`ifdef\s+(\S+)', _ifdef),
    (r'`ifndef\s+(\S+)', _ifndef),
    (r'`else', _else),
    (r'`endif', _endif),
    (r'`define\s+([A-Za-z0-9_]+)\s+(.*?)(?=\n|//|/\*)', _define),
    (r'`([A-Za-z_0-9]+)', _macro)
    )

regexs = [(re.compile(r), a) for (r, a) in regexs]

def preproc(filename, incpath = ('.',), defines = {}, state = {'ifdef': True}):
    cont = open(filename).read()
    return "`file(%s)" % filename + \
        _process(cont, incpath, defines, state) +\
        "`endfile(%s)" % filename
    
def _process(cont, path, defines, state):
    lineno = 1;
    char = 0;
    skipped = 0
    ret = ""
    while cont:
        for (regex, action) in regexs:
            m = regex.match(cont)
            if m:
                end = m.end()
                assert end > 0
                char += end
                if action:
                    gen = action(m, path, defines, state)
                    lineno += m.group(0).count('\n')
                else:
                    matched = m.group(0)
                    lineno += matched.count('\n')
                    if state['ifdef']: gen = matched
                    else:              gen = ""
                if skipped > 0 and len(gen) > 0:
                    ret += "`pos(%d,%d)" % (lineno, char)
                    skipped = 0;
                ret += gen
                if len(gen) < end:
                    skipped += end - len(gen)
                elif len(gen) > end:
                    ret += "`pos(%d,%d)" % (lineno, char)
                cont = cont[end:]
                break
        else:
            if state['ifdef']:
                if skipped > 0:
                    ret += "`pos(%d,%d)" % (lineno, char)
                    skipped = 0;
                ret += cont[0]
            else:
                skipped += 1
            if cont[0] == '\n':
                lineno += 1;
            char += 1;
            cont = cont[1:]
    return ret

if __name__ == "__main__":
    import sys
    print(preproc(sys.argv[1]))
