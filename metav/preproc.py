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

def _include(m, state):
    if not state['ifdef']: return ""
    filename = m.group(1)
    for p in state['incpath']:
        p = os.path.join(p, filename)
        if os.path.isfile(p):
            return preproc(p, state)
    raise IOError("Could not find %s in include path" % (filename, ))

def _macro(m, state):
    if not state['ifdef']: return ""
    macro = m.group(1)
    #print("macro: "+macro)
    return "`macro(%s)%s`endmacro(%s)" % \
        (macro, _process(state['defines'][macro], state), macro)

def _define(m, state):
    if not state['ifdef']: return ""
    macro = m.group(1)
    value = m.group(2)
    #print("define "+macro+"="+value)
    assert macro not in state['defines']
    state['defines'][macro] = value
    return ""

def _drop(m, state):
    return ""

def _ifdef(m, state):
    var = m.group(1)
    if var not in state['defines']:
        state['ifdef'] = False
    state['in_ifdef'] += 1
    return ""
def _ifndef(m, state):
    var = m.group(1)
    if var in state['defines']:
        state['ifdef'] = False
    state['in_ifdef'] += 1
    return ""
def _else(m, state):
    state['ifdef'] = not state['ifdef']
    if state['in_ifdef'] <= 0:
        raise Exception("Spurious `else")
    return ""
def _endif(m, state):
    state['ifdef'] = True
    state['in_ifdef'] -= 1
    if state['in_ifdef'] < 0:
        raise Exception("Spurious `endif")
    return ""

regexs = (
    (r'//[^\n]*',       None),    # Line comments
    (r'/\*metav_delete:', _drop),
    (r':metav_delete\*/', _drop),
    (r'/\*metav_generated:\*/(.|\n)*?/\*:metav_generated\*/', _drop),
    (r'/\*(.|\n)*?\*/', None),    # Block comments
    (r'"(\\"|[^"])*"', None),     # Strings
    (r'`include\s+"([^"]+)"', _include),
    (r'`ifdef\s+(\S+)', _ifdef),
    (r'`ifndef\s+(\S+)', _ifndef),
    (r'`else', _else),
    (r'`endif', _endif),
    (r'`define\s+([A-Za-z0-9_]+)\s+(.*?)(?=\n|//|/\*)', _define),
    (r'`([A-Za-z_0-9]+)', _macro),
    (r'(.|\n)([^/`":]|\n)*', None), # Match the rest, as greedy as possible
    )

regexs = [(re.compile(r), a) for (r, a) in regexs]

def preproc(filename, state = {}):
    if 'in_ifdef' not in state: state['in_ifdef'] = 0
    if 'ifdef' not in state: state['ifdef'] = True
    if 'defines' not in state: state['defines'] = {}
    if 'incpath' not in state: state['incpath'] = ('.',)
    cont = open(filename).read()
    return "`file(%s)" % filename + \
        _process(cont, state) +\
        "`endfile(%s)" % filename
    
def _process(cont, state):
    lineno = 1;
    char = 0;
    skipped = 0
    ret = ""
    while cont:
        got_match = False
        for (regex, action) in regexs:
            m = regex.match(cont)
            if not m: continue
            matched = m.group(0)
            #print("%s matched %s" % (regex.pattern, repr(matched)))
            got_match = True
            end = m.end()
            assert end > 0
            if action:
                gen = action(m, state)
            else:
                if state['ifdef']: gen = matched
                else:              gen = ""
            if skipped != 0 and len(gen) > 0:
                # We continue to emit text after having skipped a section
                # emit a `pos to tell lexer how much we have skipped
                ret += "`pos(%d,%d)" % (lineno, char)
                skipped = 0;
            ret += gen
            if len(gen) != end:
                # We have removed or added text
                skipped += end - len(gen)
            char += end
            lineno += matched.count('\n')
            cont = cont[end:]
            break
        assert got_match, "One regex must match. %s... unmatched" % (repr(cont[:20]),)
    return ret

if __name__ == "__main__":
    import sys
    print(preproc(sys.argv[1]))
