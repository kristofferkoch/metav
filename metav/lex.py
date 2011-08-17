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
import ply.lex
import copy
from .literal import VerilogNumber, String
import ast

keywords = ('MODULE', 'ENDMODULE', 'INPUT', 'OUTPUT', 'REG', 'WIRE', 'INOUT',
            'ALWAYS', 'ASSIGN', 'POSEDGE', 'NEGEDGE', 'OR', 'CASE', 'CASEZ',
            'CASEX', 'ENDCASE',
            'PARAMETER', 'LOCALPARAM', 'BEGIN', 'END', 'IF', 'ELSE', 'DEFAULT')
keyword_map = {}
for r in keywords:
    keyword_map[r.lower()] = r;
symbols = {
    '(',')',';',':','#','.','?',
    '[',']',',','@','*','/','%','+:',
    '{','}','=','<=','+','-','<<','>>',
    '==', '===','!=', '!==','<','>','>=',
    '&', '&&', '|', '||', '~', '!', '^'
    }

tokens = keywords + \
    tuple(["'"+s+"'" for s in symbols]) + (
    'ID', 'NUMBER', 'STRING'
    )

def vLexer():
    ## tuple of tuples:
    # (postype, posvalue, pos, line, linepos)
    # ('file', 'test.v', 0, 1, 0)
    pos_stack = (('void', None, 0, 1, 0),)
    lex_offset = 0
    
    def build_symbolre(symbols=symbols):
        single = ''
        rest = []
        for sym in symbols:
            e = re.escape(sym)
            if len(sym) == 1:
                single += e
            else:
                rest.append('('+e+')')
        rest.sort(key=lambda x: len(x), reverse=True);
        rest.append('['+single+']')
        return '|'.join(rest)
    symbol_re = build_symbolre()

    def TOKEN(r):
        def set_doc(f):
            def new_f(t):
                nonlocal pos_stack, lex_offset
                # Do book-keeping to correct the positions
                l = pos_stack[-1]
                diff = t.lexpos - l[2] - lex_offset
                #assert diff >= 0, "diff=%d, should be >= 0" % diff
                if diff > 0:
                    pos_stack = pos_stack[:-1] + ((l[0], l[1], l[2]+diff, l[3], l[4]+diff),)
                    #print("diff: " + repr(pos_stack))
                t.pos_stack = pos_stack[1:]
                ret = f(t)
                # Count linenumbers
                v = str(t.value)
                if '\n' in v:
                    l = pos_stack[-1]
                    lineno = l[3] + v.count('\n')
                    pos = len(v) - v.rindex('\n') - 2
                    pos_stack = pos_stack[:-1] + ((l[0], l[1], l[2], lineno, pos),)
                return ret
            new_f.regex = r
            new_f.__doc__ = f.__doc__
            new_f.lineno   = f.__code__.co_firstlineno
            new_f.filename = f.__code__.co_filename
            return new_f
        return set_doc

    @TOKEN(r'`(?P<type>[a-z_0-9]+)\((?P<value>[^)]*)\)')
    def t_ANCHOR(t):
        nonlocal pos_stack, lex_offset
        type_ = t.lexer.lexmatch.group('type')
        value = t.lexer.lexmatch.group('value')
        l = pos_stack[-1]
        #print("in ANCHOR " + repr(pos_stack), type_,value)
        if type_ == "pos":
            line, pos = (int(x) for x in value.split(","))
            t.lexer.lineno = line
            if line > l[3]:
                pos_stack = pos_stack[:-1] + ((l[0], l[1], l[2], line, l[4]),)
            lex_offset = pos - t.lexpos
        elif type_ == "file":
            pos_stack += (('file', value, 0, 1, 0),)
        elif type_ == "endfile":
            assert l[0] == "file"
            assert l[1] == value
            pos_stack = pos_stack[:-1]
            if pos_stack:
                assert pos_stack[-1][0] in ("file", "void"), "endfile was %s" % repr(pos_stack[-1]) # Cannot `include with a macro
                #print("Back to file %s" % pos_stack[-1].value)
        elif type_ == "macro":
            pos_stack += (('macro', value, 0, 1, 0),)
            #print("Entering macro %s" % value)
        elif type_ == "endmacro":
            pos_stack = pos_stack[:-1]
            assert l[0] == "macro"
            assert l[1] == value
            #print("Leaving macro %s" % value)
        else:
            assert False, "Unknown anchor %s" % type_
        #assert lex_offset >= 0, "lex_offset=%d, should be >= 0" % lex_offset
        lex_offset += len(t.value)
        #print("Return ANCHOR", pos_stack)
        return None

    prev_decl = None
    block_comment = None
    prev_id = None
    cur_module = None
    @TOKEN(r'(\\\S+)|([a-zA-Z_]\w*)')
    def t_ID(t):
        nonlocal prev_decl, block_comment, prev_id, cur_module
        t.line_comment = None
        if t.value[0] == '\\':
            t.value = t.value[1:]
        t.type = keyword_map.get(t.value, 'ID')
        if t.type == 'ID':
            if not prev_decl:
                # prev_decl is set to None on newline
                # This allows us to set the comment on the first identifier
                # on the line
                prev_decl = t
            t.block_comment = block_comment
            block_comment = None
            if prev_id.type == 'MODULE':
                cur_module = t.value
            prev_id = t
        if t.type == 'ENDMODULE':
            cur_module = None
        return t

    @TOKEN(r'$\w*')
    def t_SYS_ID(t):
        t.line_comment = None
        t.block_comment = block_comment
        block_comment = None
        prev_id = t
        return t

    @TOKEN(r'([0-9]*\'([bB](?P<bin>[01_zxZX?]+)|[hH][0-9a-fA-F_zxZX?]+|[dD][0-9_]+)|[0-9]+)')
    def t_NUMBER(t):
        nonlocal pos_stack
        t.value = VerilogNumber(t)
        #t.value.pos_stack = pos_stack[1:]
        return t
    @TOKEN(r'"(\\"|[^"])*"')
    def t_STRING(t):
        t.value = String(t)
        return t

    def annotate_comment(t):
        nonlocal prev_decl, block_comment
        if prev_decl != None:
            #print("*** Annotating comment " + t.value)
            if prev_decl.lineno == t.lineno:
                #print("*** Adding a line comment to "+repr(prev_decl))
                prev_decl.line_comment = t
            else:
                block_comment = t
            prev_decl = None
        else:
            block_comment = t;

    @TOKEN(r'//[^\n]*')
    def t_LINE_COMMENT(t):
        #print("Got line comment: "+t.value)
        annotate_comment(t)

    def _get_file():
        nonlocal pos_stack
        for p in reversed(pos_stack):
            if p[0] == 'file': return p
        assert False

    codes = {}
    @TOKEN(r'/\*+\s*metav[\s\*]*?\n+(?P<white>[\t ]*)(?P<code>(.|\n)*?)\s*\*/')
    def t_METAV(t):
        nonlocal codes, cur_module
        white_prefix = t.lexer.lexmatch.group('white')
        code = white_prefix + t.lexer.lexmatch.group('code')
        lines = []
        for line in code.split('\n'):
            #print(repr(line))
            if not line.startswith(white_prefix):
                raise Exception("python code with unclean white prefix")
            lines.append(line[len(white_prefix):])
        code = '\n'.join(lines)
        #print("Got code block in "+cur_module+":\n"+code+"\n#endcode")
        filepos = _get_file()
        past = ast.parse(code, filepos[1])
        ast.increment_lineno(past, filepos[3])
        code = compile(past, filename=filepos[1], mode='exec')
        if cur_module not in codes:
            codes[cur_module] = []
        codes[cur_module].append(code)
        return None

    @TOKEN(r'/\*metav\ generated:\*/(.|\n)*?/\*end\ metav\ generated\*/')
    def t_METAV_GENERATED(t):
        #print("Got generated code. Ignoring");
        return None

    @TOKEN(r'/\*(.|\n)*?\*/')
    def t_BLOCK_COMMENT(t):
        #print("Got block comment: "+t.value + "end: "+str(linepos))
        annotate_comment(t)

    @TOKEN(symbol_re)
    def t_SYMBOL(t):
        if t.value in symbols:
            t.type = "'"+t.value+"'"
        return t

    #t_ignore = ''
    @TOKEN(r'\n+')
    def t_newline(t):
        nonlocal prev_decl
        n = len(t.value)
        t.lexer.lineno += n
        prev_decl = None
        
    @TOKEN(r'[ \t\r]+')
    def t_white(t):
        return None

    def t_error(t):
        print("Lexer error");

    return ply.lex.lex(debug=0), codes

if __name__ == "__main__":
    l, codes = vLexer()
    import preproc
    l.input(preproc.preproc("../test/simple.v"))
    tokens = list(l)
    for tok in tokens:
        print(repr(tok))
    for module in codes:
        #print(ast.dump(code, include_attributes=True))
        #print(dir(code))
        for code in codes[module]:
            exec(code)
