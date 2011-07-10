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

def _include(m, state, filestate):
    if not state['ifdef']: return ""
    filename = m.group(1)
    for p in state['incpath']:
        p = os.path.join(p, filename)
        if os.path.isfile(p):
            ret, edit_plan = preproc(p, state)
            filestate['edit_plan'] += edit_plan
            return ret
    raise IOError("Could not find %s in include path" % (filename, ))

def _macro(m, state, filestate):
    if not state['ifdef']: return ""
    macro = m.group(1)
    #print("macro: "+macro)
    if macro in state['defines']:
        macrostate = {
            'filename': filestate['filename']+'%'+macro,
            'char': 0,
            'lineno': 1,
            }
        ret = _process(state['defines'][macro], state, macrostate)
        return "`macro(%s)%s`endmacro(%s)" % \
            (macro, ret, macro)
    else:
        return ""

def _define(m, state, filestate):
    if not state['ifdef']: return ""
    macro = m.group(1)
    value = m.group(2)
    #print("define "+macro+"="+value)
    assert macro not in state['defines']
    state['defines'][macro] = value
    return ""

def _drop(m, state, filestate):
    size = len(m.group(0))
    begin = ('file', filestate['filename'], filestate['char'], filestate['lineno'])
    end   = ('file', filestate['filename'], filestate['char'] + size)
    filestate['edit_plan'].append(('delete', ((begin,), (end,))))
    return ""

def _ifdef(m, state, filestate):
    var = m.group(1)
    if var not in state['defines']:
        state['ifdef'] = False
    state['in_ifdef'] += 1
    return ""
def _ifndef(m, state, filestate):
    var = m.group(1)
    if var in state['defines']:
        state['ifdef'] = False
    state['in_ifdef'] += 1
    return ""
def _else(m, state, filestate):
    state['ifdef'] = not state['ifdef']
    if state['in_ifdef'] <= 0:
        raise Exception("Spurious `else")
    return ""
def _endif(m, state, filestate):
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

regexs = [(re.compile('^'+r), a) for (r, a) in regexs]

def preproc(filename, state = {}):
    if 'in_ifdef' not in state: state['in_ifdef'] = 0
    if 'ifdef' not in state: state['ifdef'] = True
    if 'defines' not in state: state['defines'] = {}
    if 'incpath' not in state: state['incpath'] = ('.',)
    filestate = {
        'filename': filename,
        'lineno': 1,
        'char': 0,
        'edit_plan': [],
        }
    cont = open(filename).read()
    return ("`file(%s)" % filename +
            _process(cont, state, filestate) +
            "`endfile(%s)" % filename,
            filestate['edit_plan'])
    
def _process(cont, state, filestate):
    ret = ""
    skipped = 0
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
                gen = action(m, state, filestate)
            else:
                if state['ifdef']: gen = matched
                else:              gen = ""
            if skipped != 0 and len(gen) > 0:
                # We continue to emit text after having skipped a section
                # emit a `pos to tell lexer how much we have skipped
                ret += "`pos(%d,%d)" % (filestate['lineno'], filestate['char'])
                skipped = 0;
            ret += gen
            if len(gen) != end:
                # We have removed or added text
                skipped += end - len(gen)
            filestate['char']   += end
            filestate['lineno'] += matched.count('\n')
            cont = cont[end:]
            break
        assert got_match, "One regex must match. %s... unmatched" % (repr(cont[:20]),)

    return ret

if __name__ == "__main__":
    import sys
    print(preproc(sys.argv[1]))
