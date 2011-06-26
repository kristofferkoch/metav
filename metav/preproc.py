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

def _include(m, path, defines):
    filename = m.group(1)
    return preproc(filename, path, defines)

def _macro(m, path, defines):
    macro = m.group(1)
    #print("macro: "+macro)
    return "`macro(%s)%s`endmacro(%s)" % (macro, _process(defines[macro], path, defines), macro)

def _define(m, path, defines):
    macro = m.group(1)
    value = m.group(2)
    #print("define "+macro+"="+value)
    assert macro not in defines
    defines[macro] = value
    return ""

regexs = (
    (r'//[^\n]*',       None),
    (r'/\*(.|\n)*?\*/', None),
    (r'"(\\"|[^"])*"', None),
    (r'`include\s+"([^"]+)"', _include),
    (r'`define\s+([A-Za-z0-9_]+)\s+(.*?)(?=\n|//|/\*)', _define),
    (r'`([A-Za-z_0-9]+)', _macro)
    )

regexs = [(re.compile(r), a) for (r, a) in regexs]

def preproc(filename, path = ('.',), defines = {}):
    cont = open(filename).read()
    return "`file(%s)" % filename + \
        _process(cont, path, defines) +\
        "`endfile(%s)" % filename
    
def _process(cont, path, defines):
    lineno = 1;
    char = 0;
    ret = ""
    while cont:
        for (regex, action) in regexs:
            m = regex.match(cont)
            if m:
                end = m.end()
                assert end > 0
                char += end
                if action:
                    gen = action(m, path, defines)
                    lineno += m.group(0).count('\n')
                    ret += gen
                    if len(gen) != end:
                        ret += "`pos(%d,%d)" % (lineno, char)
                else:
                    matched = m.group(0)
                    lineno += matched.count('\n')
                    ret += matched
                cont = cont[end:]
                break
        else:
            if cont[0] == '\n':
                lineno += 1;
            ret += cont[0]
            cont = cont[1:]
            char += 1;
    return ret

if __name__ == "__main__":
    import sys
    print(preproc(sys.argv[1]))
