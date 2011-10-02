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

"""Objects for constructing a Verilog Abstract Syntax Tree (vast)"""

import metav.literal
import ast

def _get_end(i):
    "Given a pos_stack, calculate the position + length of identifier"
    last = i.pos_stack[-1]
    off = len(str(i.value))
    return i.pos_stack[:1] + \
        ((last[0], last[1], last[2] + off, last[3], last[4] + off),)

class Ast(object):
    """Superclass to all nodes in the syntax tree"""
    def extend_pos(self, end):
        "Update the position of the AST element by extending the end"
        self.pos = (self.pos[0], _get_end(end))
    def delete_child(self, child):
        "Delete a child from the AST. To be called from child in child.delete()"
        # To be overridden if it makes sense
        raise NotImplementedError
    def _get_edit_plan(self):
        "Search for edit plan in self and parents"
        if hasattr(self, 'edit_plan'):
            return self.edit_plan
        return self.parent._get_edit_plan()

    def _make_edit_plan(self):
        if not hasattr(self, 'edit_plan'):
            self.edit_plan = self._get_edit_plan()

    def delete(self):
        self._make_edit_plan()
        if not getattr(self, 'is_root_node', False):
            self.parent.delete_child(self)
        self.parent = None
        self.edit_plan.append(('remove',) + self.pos)

class Module(Ast):
    """Module is the root node for the AST's
    
    A Module instance has some useful attributes:
     * name:  The module name identifier. An instance of Id
     * items: The items of the module body
     * insts: A dict(module name -> ModuleInsts) with instanciated
              modules. ModuleInsts.module might be populated with
              the AST for the instanciated modules
     * ids: A dict(identifier name -> set(Decl)) of declarations
            found in the module. Ports and parameters are found here.
    """
    def __init__(self, module, name, modparams, modports, items, endmodule):
        self.pos = (module.pos_stack, _get_end(endmodule))
        self.append_pos = endmodule.pos_stack
        self.is_root_node = True
        assert isinstance(name, Id)
        self.name = name
        self.block_comment = name.block_comment
        self.portstyle = None
        self.modparams = modparams
        self.modports = modports    
        self.items = items
        self._build_ids()
        self.metav = [m for m in self.items if isinstance(m, Metav)]

        self.insts = dict((i.module_name.value, i) for i in self.items
                          if type(i) == ModuleInsts)

    def execute_metav(self, get_module, includes):
        for m in self.metav:
            exec(m.code, {'module':     self,
                          'get_module': get_module,
                          'ast':        metav.vast,
                          'includes':   includes,
                          })

    def _build_ids(self):
        self.ids = {}
        self._extract_modparams()
        self._extract_modports()
        self._extract_declarations()
        # Identify "output reg" declarations, and index them as
        # one output declaration and one reg declaration
        self._extract_output_reg()


    def _extract_declarations(self):
        for i in self.items:
            assert isinstance(i, Ast), "'%r' is not Ast" % i
            i.parent = self
            if hasattr(i, 'ids'):          ids = i.ids
            elif hasattr(i, 'ids_or_mem'): ids = i.ids_or_mem
            elif type(i) == Wire:          ids = i.ids_or_assigns
            elif type(i) == Parameter:     ids = i.assigns
            else:                          continue
            if isinstance(i, Port):
                if self.portstyle not in (None, "regular"):
                    raise Exception("Not coherent portstyle at %r" % i)
                self.portstyle = "regular"
            for id_or_assign in ids:
                if type(id_or_assign) == Assign:
                    self.ids.setdefault(id_or_assign.lval.value, set()).add(
                        self.Decl(i, id_or_assign))
                else:
                    self.ids.setdefault(id_or_assign.value, set()).add(
                        self.Decl(i, id_or_assign))
        
    def _extract_modports(self):
        if not self.modports or not isinstance(self.modports[0], Port):
            return
        self.portstyle = "ansi"
        for p in self.modports:
            assert isinstance(p, Port)
            p.parent = self
            for id_ in p.ids:
                assert isinstance(id_, Id)
                self.ids.setdefault(id_.value, set()).add(self.Decl(p, id_))
        

    def _extract_modparams(self):
        if not self.modparams:
            return
        for p in self.modparams:
            assert isinstance(p, Parameter)
            p.parent = self
            for assign in p.assigns:
                assert isinstance(assign, Assign)
                assert isinstance(assign.lval, Id)
                self.ids.setdefault(assign.lval.value, set()).add(
                    self.Decl(p, assign))


    def _extract_output_reg(self):
        # Some output declarations have "reg" as well
        # Add this as an explicit reg declaration for normalization purposes
        for id_ in self.ids:
            to_add = set()
            for decl in self.ids[id_]:
                if decl.type != 'port' or decl.subtype != 'output': continue
                o = decl.ast
                assert decl.id.value == id_
                if o.is_reg:
                    regdecl = self.Decl(Reg([decl.id], o.range),
                                        decl.id)
                    to_add.add(regdecl)
            self.ids[id_].update(to_add)
        
    class Decl(object):
        def __init__(self, ast, id_):
            self.ast = ast
            if isinstance(ast, Port):
                self.type = "port"
                self.subtype = ast.type
            elif type(ast) == Parameter:
                self.type = "parameter"
                self.subtype = ast.type
            elif type(ast) == Reg:
                self.type = "reg"
                self.subtype = "mem" if type(id_) == MemReg else "reg"
            elif type(ast) == Wire:
                self.type = 'wire'
            elif isinstance(ast, Genvars):
                self.type = "genvar"
            else:
                assert False, "Unknown declaration '%r'" % ast
            self.id = id_
            self.range = ast.range
        def __str__(self):
            r = ''
            if self.range: r = str(self.range) + ' '
            t = self.type
            if hasattr(self, 'subtype'): t = self.subtype
            def s(x):
                if type(x) == MemReg: return str(x)
                if type(x) == Assign: return x.lval.value + ' = ' + str(x.rval)
                return x.value
            return '<' + t + ' ' + r + s(self.id)+'>'
        def __repr__(self):
            return "Module.Decl("+str(self)+")"
        
    def __str__(self):
        def mystr(x):
            if hasattr(x, 'value'):
                return x.value
            return str(x)
        ret = "module %s " % (self.name.value,)
        if self.modparams:
            ret += "#(parameter " + \
                ',\n\t'.join(str(x) for x in self.modparams) + ")\n\t"
        if type(self.modports) == list:
            ret += '(' + ', '.join(mystr(x) for x in self.modports) + ')'
        ret += ";\n\t"
        ret += '\n\t'.join(str(x) for x in self.items)
        ret += "\nendmodule"
        return ret

    def add_item(self, item):
        assert isinstance(item, Ast)
        self._make_edit_plan()
        item.parent = self
        self.items.append(item)
        instruction = ('insert', self.append_pos,  item)
        item.instruction = instruction
        self.edit_plan.append(instruction)
        self._build_ids()
    def add_port(self, port):
        assert isinstance(port, Port)
        self._make_edit_plan()
        if self.portstyle == "regular":
            pass
        elif self.portstyle = "ansi":
            pass
        else:
            assert False, "Unknown portstyle %r" % self.portstyle
        raise NotImplementedError
    def delete_port(self, name):
        self._make_edit_plan()
        raise NotImplementedError

    def delete_child(self, child):
        # First, check if it is a module item
        for n, item in enumerate(self.items):
            if item is child:
                del self.items[n]
                self._build_ids()
                return

        # If it is not a module item, check if it is a modport
        for n, modport in enumerate(self.modports):
            if modport is child:
                del self.modports[n]
                self._build_ids()
                return

        # If not item or modport, maybe modparam?
        for n, modparam in enumerate(self.modparams):
            if modparam is child:
                del self.modparams[n]
                self._build_ids()
                return

        assert False, "Could not find child "+repr(child)
    
class Metav(Ast):
    def __init__(self, from_lex):
        source, filename, first_line = from_lex
        parsed_ast = ast.parse(source, filename)
        ast.increment_lineno(parsed_ast, first_line)
        code = compile(parsed_ast, filename=filename, mode='exec')
        self.source = source
        self.code = code
    def __str__(self):
        return "/*metav\n%s\n\t*/" % self.source

class Port(Ast):
    def __init__(self, ids, range=None):
        if type(ids) is not list:
            ids = [ids]
        self.ids = ids
        self.range = range
        if self.range:
            self.range.parent = self
        self.range = range
        for i in ids:
            i.parent = self
        self.in_portlist = False

    def parse_info(self, kw, in_portlist=False):
        last = self.ids[-1]
        self.pos = (kw.pos_stack, last.pos[1])
        assert self.type == kw.value
        self.in_portlist = in_portlist
    def append(self, id_):
        self.ids.append(id_)
        id_.parent = self
        self.pos = (self.pos[0], id_.pos[1])
    def __str__(self):
        ret = self.type + " "
        if self.range: ret += str(self.range) + " "
        ret += ',\n\t\t'.join(x.value for x in self.ids)
        if not self.in_portlist: ret += ";"
        return ret


class Input(Port):
    type = "input"
class Output(Port):
    type = "output"
    def __init__(self, ids, range=None, reg=None):
        Port.__init__(self, ids, range=range)
        self.reg_kw = reg
        self.is_reg = getattr(reg, 'value', None) == "reg"
class Inout(Port):
    type = "inout"

class Range(Ast):
    def __init__(self, msb, lsb):
        assert isinstance(msb, Expression)
        assert isinstance(lsb, Expression)
        self.msb = msb
        self.lsb = lsb
        msb.parent = self
        lsb.parent = self
    def parse_info(self, left, right):
        self.pos = (left.pos_stack, _get_end(right))
        
    def __str__(self):
        return "["+str(self.msb)+":"+str(self.lsb)+"]"

class ContAssigns(Ast):
    def __init__(self, assigns):
        self.assigns = assigns
        for a in assigns:
            a.parent = self
    def parse_info(self, kw):
        last = self.assigns[-1]
        self.pos = (kw.pos_stack, last.pos[1])
        
    def __str__(self, ntabs = 0):
        return "assign\n" + '\n'.join(x.__str__(ntabs + 1) for x in self.assigns) + ";"

class Parameter(Ast):
    def __init__(self, assigns, type="parameter", range=None):
        self.type = type
        self.range = range
        if self.range:
            self.range.parent = self
            assert isinstance(self.range, Range)
        type_ = __builtins__['type']
        if type_(assigns) is not list:
            assigns = [assigns]
        self.assigns = assigns
        for a in assigns:
            a.parent = self

    def parse_info(self, type_kw):
        self.pos = (type_kw.pos_stack, self.assigns[-1].pos[1])
        self.type = type_kw.value
        
    def append(self, assign):
        self.assigns.append(assign)
        assign.parent = self
        self.pos = (self.pos[0], assign.pos[1])
    def __str__(self):
        return self.type + " " + \
            ',\n\t\t'.join(str(x) for x in self.assigns) + ";"

class Wire(Ast):
    def __init__(self, ids_or_assigns, range=None):
        self.range = range
        if self.range:
            self.range.parent = self
            assert isinstance(range, Range)
        self.ids_or_assigns = ids_or_assigns
        for i in ids_or_assigns:
            i.parent = self
    def parse_info(self, kw):
        last = self.ids_or_assigns[-1]
        self.pos = (kw.pos_stack, last.pos[1])
        
    def __str__(self):
        r = ""
        if self.range:
            r = str(self.range) + " "
        ret = "wire " + r + \
            ',\n\t\t'.join(str(x) for x in self.ids_or_assigns) + ";"
        return ret

class Reg(Ast):
    def __init__(self, ids_or_mem, range=None):
        self.range = range
        if self.range:
            assert isinstance(range, Range)
            self.range.parent = self
        self.ids_or_mem = ids_or_mem
        for i in ids_or_mem:
            i.parent = self

    def parse_info(self, kw):
        last = self.ids_or_mem[-1]
        self.pos = (kw.pos_stack, last.pos[1])
        
    def __str__(self):
        r = ""
        if self.range:
            r = str(self.range) + " "
        def s(x):
            if type(x) == MemReg: return str(x)
            else: return x.value
        return "reg " + r + ",\n\t\t".join(s(x) for x in self.ids_or_mem) + ";"

class MemReg(Ast):
    def __init__(self, id_, range_):
        assert isinstance(id_, Id)
        if hasattr(id_, 'pos'):
            self.pos = (id_.pos[0], range_.pos[1])
        self.id = id_
        self.id.parent = self
        self.range = range_
        self.range.parent = self
        self.value = id_.value
        
    def __str__(self):
        return self.value + " "+str(self.range)

class Always(Ast):
    def __init__(self, statement):
        self.statement = statement
        self.statement.parent = self
    def parse_info(self, kw):
        self.pos = (kw.pos_stack, self.statement.pos[1])
        
    def __str__(self):
        return "always\n" + self.statement.__str__(2)

class Edge(Ast):
    def __init__(self, polarity, signal):
        if hasattr(polarity, 'pos_stack'):
            self.pos = (polarity.pos_stack, signal.pos[1])
            self.polarity = polarity.value
        else:
            self.polarity = polarity
        self.signal = signal
        self.signal.parent = self
    def __str__(self):
        return str(self.polarity) + " " + self.signal.value

class ModuleInsts(Ast):
    def __init__(self, module_name, param_overrides, insts):
        if hasattr(module_name, "pos"):
            self.pos = (module_name.pos[0], insts[-1].pos[1])
        assert isinstance(module_name, Id)
        self.module_name = module_name
        self.block_comment = module_name.block_comment
        module_name.parent = self
        self.param_overrides = param_overrides
        for p in param_overrides:
            p.parent = self
        self.insts = insts
        for i in insts: i.parent = self
        self.module = None

    def get_module(self):
        if self.module:
            return self.module
        ret = self._get_module(self.module_name.value)
        assert isinstance(self.parent, Module)
        ret.parent = self.parent
        self.module = ret;
        return ret

    def __str__(self, ntabs = 0):
        ret = "\t" * ntabs + self.module_name.value + " "
        if self.param_overrides:
            ret += "#(" + \
                ',\n\t\t\t'.join(str(x) for x in self.param_overrides) + \
                ")\n\t\t"
        ret += ', '.join(str(x) for x in self.insts)
        ret += ";"
        return ret

class ModuleInst(Ast):
    def __init__(self, inst_name, connections):
        self.inst_name = inst_name
        self.inst_name.parent = self
        self.connections = connections
        for c in connections:
            c.parent = self
    def parse_info(self, right):
        self.pos = (self.inst_name.pos[0], _get_end(right))
        
    def __str__(self):
        return self.inst_name.value + \
            ' (' + ',\n\t\t\t'.join(str(x) for x in self.connections) + ")"

class Connection(Ast):
    def __init__(self, id_, expr):
        self.id = id_
        self.id.parent = self
        self.expr = expr
        self.expr.parent = self
    def parse_info(self, dot, right):
        self.pos = (dot.pos_stack, _get_end(right))
        
    def __str__(self):
        return "."+self.id.value+'('+str(self.expr)+')'

class FunctionDeclaration(Ast):
    def __init__(self, automatic, range_opt, name, declarations, statement):
        assert isinstance(automatic, bool)
        assert isinstance(range_opt, (type(None), Range))
        assert isinstance(name, Id)
        assert isinstance(declarations, list)
        assert isinstance(declarations[0], Ast)
        assert isinstance(statement, Statement)
        self.automatic = automatic
        self.range_opt = range_opt
        self.name = name
        self.declarations = declarations
        self.statement = statement
        if range_opt:
            range_opt.parent = self
        name.parent = self
        for d in declarations:
            d.parent = self
        statement.parent = self
    def parse_info(self, function, endfunction):
        self.pos = (function.pos_stack, _get_end(endfunction))
    def __str__(self):
        auto = "automatic " if self.automatic else ""
        range = str(self.range_opt) + " " if self.range_opt else ""
        return "function " + auto + range + str(self.name) + ";\n\t\t" \
            + '\n\t\t'.join(str(x) for x in self.declarations) \
            + "\n" + self.statement.__str__(2) \
            + "\n\tendfunction"

class Statement(Ast):
    pass

class Case(Statement):
    def __init__(self, expr, items, type="case"):
        self.expr = expr
        self.items = items
        self.type = type
        assert type in ("case", "casez", "casex")
    def parse_info(self, kw, endcase):
        self.pos = (kw.pos_stack, endcase.pos_stack)
        self.type = kw.value
        
    def __str__(self, ntabs=0):
        ret = "\t" * ntabs + self.type + " ( " + str(self.expr) + " )\n"
        ret += "\n".join(x.__str__(ntabs+1) for x in self.items) + "\n";
        ret += "\t" * ntabs + "endcase"
        return ret

class CaseItem(Ast):
    def __init__(self, expressions, statement):
        if type(expressions) in (list, tuple):
            pos0 = expressions[0].pos[0]
            self.expressions = expressions
        else:
            # default case:
            pos0 = expressions.pos_stack
            self.expressions = None
        if isinstance(statement, Statement):
            self.statement = statement
            self.pos = (pos0, statement.pos[1])
        else:
            self.statement = None
            self.pos = (pos0, statement.pos_stack)
    def __str__(self, ntabs=0):
        ret = "\t" * ntabs
        if self.expressions:
            ret += ', '.join(str(x) for x in self.expressions) + " : "
        else:
            ret += 'default : '
        if self.statement:
            ret += "\n" + self.statement.__str__(ntabs + 1)
        else:
            ret += ";"
        return ret

class Assign(Statement):
    def __init__(self, lval, op, rval, is_statement = False):
        if hasattr(lval, 'pos'):
            self.pos = (lval.pos[0], rval.pos[1])
        self.lval = lval
        self.lval.parent = self
        self.op = op
        self.rval = rval
        if type(rval) != str:
            self.rval.parent = self
        self.is_statement = is_statement
    def __str__(self, ntabs=0):
        ret = "%s%s %s %s" % ("\t"*ntabs, self.lval.value, str(self.op), str(self.rval))
        if self.is_statement:
            ret += ";"
        return ret
        
class At(Statement):
    def __init__(self, sens, statement):
        self.sens = sens
        if sens:
            for s in sens: s.parent = self
        self.statement = statement
        self.statement.parent = self
    def parse_info(self, at):
        self.pos = (at.pos_stack, self.statement.pos[1])
    def __str__(self, ntabs=0):
        sens = self.sens
        if not sens: sens = "*"
        else: sens = ' or '.join(str(x) for x in sens)
        return "\t" * ntabs + "@(" + sens + ")\n" + self.statement.__str__(ntabs + 1)

class If(Statement):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.cond.parent = self
        self.true = true
        self.true.parent = self
        self.false = false
        if self.false:
            self.false.parent = self
    def parse_info(self, kw):
        self.pos = (kw.pos_stack,
                    self.false.pos[1] if self.false else self.true.pos[1])
        
    def __str__(self, ntabs=0):
        ret = "\t" * ntabs + "if ( " + str(self.cond) + " )\n" + self.true.__str__(ntabs + 1)
        if self.false:
            ret += "\n" + "\t" * ntabs + "else\n" + self.false.__str__(ntabs + 1)
        return ret

class For(Statement):
    def __init__(self, init, cond, incr, statement):
        self.init = init
        init.parent = self
        self.cond = cond
        cond.parent = self
        self.incr = incr
        incr.parent = self
        self.statement = statement
        statement.parent = self
    def parse_info(self, for_):
        self.pos = (for_.pos_stack, self.statement.pos[1])
    def __str__(self, ntabs = 0):
        return "\t" * ntabs + "for (" + str(self.init) + "; " + \
            str(self.cond) + "; " + str(self.incr) + ")\n" + \
            self.statement.__str__(ntabs + 1)

class While(Statement):
    def __init__(self, cond, statement):
        self.cond = cond
        cond.parent = self
        self.statement = statement
        statement.parent = self
    def parse_info(self, while_):
        self.pos = (while_.pos_stack, self.statement.pos[1])
    def __str__(self, ntabs = 0):
        return "\t"*ntabs + "while (" + str(self.cond) + ")\n" + \
            self.statement.__str__(ntabs + 1)

class Block(Statement):
    def __init__(self, name, statements):
        self.name = name
        self.statements = statements
    def parse_info(self, begin, end):
        self.pos = (begin.pos_stack, _get_end(end))
        
    def __str__(self, ntabs=0):
        return "\t" * ntabs + "begin\n" + \
            '\n'.join(x.__str__(ntabs + 1) for x in self.statements) + "\n" + \
            "\t" * ntabs + "end"

class TaskCall(Statement):
    def __init__(self, name, arguments):
        assert isinstance(name, Id)
        self.name = name
        self.arguments = arguments
    def parse_info(self, kw, semi):
        self.pos = (kw.pos_stack, _get_end(semi))
    def __str__(self, ntabs=0):
        return "\t" * ntabs + str(self.name) + '(' + ', '.join(str(x) for x in self.arguments) + ');'


class Expression(Ast):
    pass

class FunctionCall(Expression):
    def __init__(self, name, arguments):
        assert isinstance(name, Id)
        self.name = name
        for a in arguments:
            assert isinstance(a, Expression)
            a.parent = self
        self.arguments = arguments
    def parse_info(self, endparan):
        self.pos = (self.name.pos[0], _get_end(endparan))
    def __str__(self):
        return str(self.name) + '(' + ', '.join(str(x) for x in self.arguments) + ')'

class Id(Expression):
    def __init__(self, id_):
        if hasattr(id_, 'pos_stack'):
            self.pos = (id_.pos_stack, _get_end(id_))
            self.value = id_.value
            self.block_comment = getattr(id_.block_comment, "value", None)
            self.line_comment = getattr(id_.line_comment, "value", None)
        else:
            assert isinstance(id_, str)
            self.value = id_
    def __str__(self):
        # TODO: output escaped ids correctly
        return self.value


class PartSelect(Expression):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        if hasattr(self.id, 'pos'):
            self.pos = (self.id.pos[0], kwargs['end'].pos_stack)
        self.type = kwargs['type']
        if self.type == "single":
            self.expr = kwargs["expr"]
            self.expr.parent = self
            self.msb = self.expr
            self.lsb = self.expr
            self.size = metav.literal.VerilogNumber("1")
            self.size.parent = self
        elif self.type == "range":
            self.msb = kwargs["msb"]
            self.msb.parent = self
            self.lsb = kwargs["lsb"]
            self.lsb.parent = self
            self.size = BinaryOp(self.msb,'-',self.lsb)
        elif self.type == "plus":
            self.lsb = kwargs["lsb"]
            self.lsb.parent = self
            self.size = kwargs["size"]
            self.size.parent = self
            self.msb = BinaryOp(self.lsb,'+',self.size)
            self.msb.parent = self
        else:
            assert False
    def __str__(self):
        ret = self.id.value + "["
        if self.type == "single":
            ret += str(self.expr)
        elif self.type == "range":
            ret += str(self.msb)+":"+str(self.lsb)
        elif self.type == "plus":
            ret += str(self.lsb)+"+:"+str(self.size)
        ret += "]"
        return ret

class BinaryOp(Expression):
    def __init__(self, a, op, b):
        if hasattr(a, 'pos'):
            self.pos = (a.pos[0], b.pos[1])
        self.a = a
        self.a.parent = self
        self.op = op
        self.b = b
        self.b.parent = self
    def __str__(self):
        return '(' + ' '.join(str(x) for x in (self.a, self.op, self.b)) + ')'

class UnaryOp(Expression):
    def __init__(self, op, expr):
        if hasattr(op, 'pos_stack'):
            self.pos = (op.pos_stack, expr.pos[1])
        self.expr = expr
        self.expr.parent = self
        self.op = op.value
    def __str__(self):
        return '(' + str(self.op) + str(self.expr) + ')'

class Ternary(Expression):
    def __init__(self, cond, true, false):
        if hasattr(cond, 'pos'):
            self.pos = (cond.pos[0], false.pos[1])
        self.cond = cond
        self.cond.parent = self
        self.true = true
        self.true.parent = self
        self.false = false
        self.false.parent = self
    def __str__(self):
        return '(' + str(self.cond) + ') ? (' + \
            str(self.true) + ')\n\t\t: (' + str(self.false) + ')'

class Repetition(Expression):
    def __init__(self, repeat, concat):
        self.repeat = repeat
        self.repeat.parent = self
        self.concat = concat
        self.concat.parent = self
    def parse_info(self, left, right):
        self.pos = (left.pos_stack, _get_end(right))
    def __str__(self):
        return '{' + str(self.repeat) + str(self.concat) + '}'

class Concatenation(Expression):
    def __init__(self, expressions):
        self.expressions = expressions
        for e in expressions:
            e.parent = self
    def parse_info(self, left, right):
        self.pos = (left.pos_stack, _get_end(right))
        
    def __str__(self):
        return '{' + ', '.join(str(x) for x in self.expressions) + '}'


class Genvars(Ast):
    def __init__(self, ids):
        self.ids = ids
        self.range = None
    def parse_info(self, genvar):
        self.pos = (genvar.pos_stack, self.ids[-1].pos[1])
    def __str__(self):
        return "genvar " + ', '.join(str(x) for x in self.ids) + ";"

class Generate(Ast):
    def __init__(self, item):
        self.item = item
        item.parent = self
    def parse_info(self, generate, endgenerate):
        self.pos = (generate.pos_stack, _get_end(endgenerate))
    def __str__(self):
        return "generate\n"+self.item.__str__(2) + "\n\tendgenerate"

class GenerateBlock(Ast):
    def __init__(self, name, items):
        self.name = name
        self.items = items
        name.parent = self
        for i in items:
            i.parent = self
    def parse_info(self, begin, end):
        self.pos = (begin.pos_stack, _get_end(end))
    def __str__(self, ntabs = 0):
        return "\t" * ntabs + "begin : "+str(self.name)+"\n"+\
            '\n'.join(x.__str__(ntabs + 1) for x in self.items) + "\n" +\
            "\t" * ntabs + "end"

class GenerateIf(Ast):
    def __init__(self, expression, true, false):
        self.expression = expression
        expression.parent = self
        self.true = true
        if true:
            true.parent = self
            self.last = true
        self.false = false
        if false:
            false.parent = self
            self.last = false
    def parse_info(self, if_):
        self.pos = (if_.pos_stack, self.last.pos[1])

class GenerateFor(Ast):
    def __init__(self, init, cond, incr, item):
        self.init = init
        self.cond = cond
        self.incr = incr
        self.item = item
        init.parent = self
        cond.parent = self
        incr.parent = self
        item.parent = self
    def parse_info(self, for_):
        self.pos = (for_.pos_stack, self.item.pos[1])
    def __str__(self, ntabs = 0):
        return "\t" * ntabs +\
            "for ("+str(self.init)+"; "+str(self.cond)+"; "+str(self.incr)+")\n" \
            + self.item.__str__(ntabs + 1)

class GenerateCaseItem(Ast):
    def __init__(self, expressions, item):
        self.expressions = expressions
        self.item = item
        item.parent = self
        if expressions:
            for e in expressions:
                e.parent = self
            self.pos = (expressions[0].pos[0], item.pos[1])
    def parse_info(self, default):
        self.pos = (default.pos_stack, self.item.pos[1])
    def __str__(self, ntabs = 0):
        if self.expressions:
            return "\t" * ntabs + ', '.join(str(x) for x in self.expressions) + " :\n" +\
                self.item.__str__(ntabs + 1)
        else:
            return "\t" * ntabs + "default :\n" + self.item.__str__(ntabs + 1)

class GenerateCase(Ast):
    def __init__(self, expression, case_items):
        self.expression = expression
        expression.parent = self
        self.case_items = case_items
        for i in case_items:
            i.parent = self
    def parse_info(self, case, endcase):
        self.pos = (case.pos_stack, _get_end(endcase))
    def __str__(self, ntabs=0):
        return "\t" * ntabs + "case ("+str(self.expression)+")\n" +\
            "\n".join(x.__str__(ntabs + 1) for x in self.case_items)+"\n"+\
            "\t" * ntabs + "endcase"

# Objects for emitting only:
class Force(Assign):
    def __init__(self, lval, rval):
        assert isinstance(lval, (Id, Concatenation, PartSelect))
        assert isinstance(rval, Expression)
        self.lval = lval
        self.rval = rval
    def __str__(self):
        return "force " + str(self.lval) + " = " + str(self.rval) + ";"

class Release(Statement):
    def __init__(self, lval):
        assert isinstance(lval, (Id, Concatenation, PartSelect))
        self.lval = lval
    def __str__(self):
        return "release " + str(self.lval) + ";"

class Delay(Statement):
    def __init__(self, delay_expr, statement):
        assert isinstance(delay_expr, Expression)
        assert isinstance(statement, Statement) or statement == None
        self.delay_expr = delay_expr
        self.statement = statement
    def __str__(self):
        ret = "#" + str(self.delay_expr)
        if self.statement:
            return ret + " " + str(self.statement)
        return ret + ";"
