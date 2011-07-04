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

import metav.literal

def _get_end(i):
    l = i.pos_stack[-1]
    off = len(str(i.value))
    return i.pos_stack[:1] + ((l[0], l[1], l[2] + off, l[3], l[4] + off),)

class Ast(object):
    def extend_pos(self, end):
        self.pos = (self.pos[0], end)
    
class Module(Ast):
    def __init__(self, module, name, modparams, modports, items, endmodule):
        self.pos = (module.pos_stack, _get_end(endmodule))
        assert isinstance(name, Id)
        self.name = name
        assert modparams == None or isinstance(modparams[0], Parameter)
        self.modparams = modparams
        assert modports == None or len(modports) == 0 or \
            isinstance(modports[0], Port) or isinstance(modport[0], Id)
        self.modports = modports
        assert len(items) == 0 or isinstance(items[0], Ast)
        self.items = items

        self.ids = {}
        if modparams:
            for p in modparams:
                assert isinstance(p, Parameter)
                p.parent = self
                for assign in p.assigns:
                    assert isinstance(assign, Assign)
                    assert isinstance(assign.lval, Id)
                    self.ids.setdefault(assign.lval.value, set()).add(
                        self.Decl(p, assign))
        if modports and hasattr(modports[0], 'ids'):
            for p in modports:
                assert isinstance(p, Port)
                p.parent = self
                for id_ in p.ids:
                    assert isinstance(id_, Id)
                    self.ids.setdefault(id_.value, set()).add(self.Decl(p, id_))
                
        for i in items:
            assert isinstance(i, Ast)
            i.parent = self
            if hasattr(i, 'ids'):          ids = i.ids
            elif hasattr(i, 'ids_or_mem'): ids = i.ids_or_mem
            elif type(i) == Wire:          ids = i.ids_or_assigns
            elif type(i) == Parameter:     ids = i.assigns
            else:                          continue
            for id_or_assign in ids:
                if type(id_or_assign) == Assign:
                    self.ids.setdefault(id_or_assign.lval.value, set()).add(
                        self.Decl(i, id_or_assign))
                else:
                    self.ids.setdefault(id_or_assign.value, set()).add(
                        self.Decl(i, id_or_assign))

        self._extract_output_reg()

        self.insts = dict((i.module_name.value, i) for i in self.items
                          if type(i) == ModuleInsts)
        print("module " + self.name.value)
        for id in self.ids:
            print(id+":\t"+repr(self.ids[id]))
        self.to_add = []

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
                    regdecl = self.Decl(Reg(o.reg_kw, o.range, [decl.id], decl.id),
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
            else:
                print(str(ast))
                assert(False)
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
        def __repr__(self): return "Module.Decl("+str(self)+")"
        
    def __str__(self):
        def mystr(x):
            if hasattr(x, 'value'):
                return x.value
            return str(x)
        ret = "module %s " % (self.name.value,)
        if self.modparams:
            ret += "#(parameter " + ',\n\t'.join(str(x) for x in self.modparams) + ")\n\t"
        if type(self.modports) == list:
            ret += '(' + ', '.join(mystr(x) for x in self.modports) + ')'
        ret += ";\n\t"
        ret += '\n\t'.join(str(x) for x in self.items)
        ret += "\nendmodule"
        return ret
    def add_item(self, item):
        self.to_add.append(item)

class Port(Ast):
    def __init__(self, kw, range_, ids, last, in_portlist=False):
        self.pos = (kw.pos_stack, last.pos[1])
        self.type = kw.value
        self.range = range_
        if self.range:
            self.range.parent = self
        self.ids = ids;
        for i in ids: i.parent = self
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
    pass
class Output(Port):
    def __init__(self, kw, reg, range_, ids, last, in_portlist=False):
        Port.__init__(self, kw, range_, ids, last, in_portlist)
        self.reg_kw = reg
        self.is_reg = bool(reg.value)
class Inout(Port):
    pass

class Range(Ast):
    def __init__(self, left, msb, lsb, right):
        self.pos = (left.pos_stack, _get_end(right))
        self.msb = msb
        self.lsb = lsb
        msb.parent = self
        lsb.parent = self
    def __str__(self):
        return "["+str(self.msb)+":"+str(self.lsb)+"]"

class ContAssigns(Ast):
    def __init__(self, kw, assigns, last):
        self.pos = (kw.pos_stack, last.pos[1])
        self.assigns = assigns
        for a in assigns: a.parent = self
    def __str__(self):
        return "assign " + '\n'.join(str(x) for x in self.assigns) + ";"

class Parameter(Ast):
    def __init__(self, type_, range_, assigns):
        self.pos = (type_.pos_stack, assigns[-1].pos[1])
        self.type = type_.value
        self.range = range_
        if self.range:
            self.range.parent = self
        self.assigns = assigns
        for a in assigns: a.parent = self
    def append(self, assign):
        self.assigns.append(assign)
        assign.parent = self
        self.pos = (self.pos[0], assign.pos[1])
    def __str__(self):
        return self.type + " " + ',\n\t\t'.join(str(x) for x in self.assigns) + ";";

class Wire(Ast):
    def __init__(self, kw, range_, ids_or_assigns, last):
        self.pos = (kw.pos_stack, last.pos[1])
        self.range = range_
        if self.range:
            self.range.parent = self
        self.ids_or_assigns = ids_or_assigns;
        for i in ids_or_assigns: i.parent = self
    def __str__(self):
        r = ""
        if self.range:
            r = str(self.range) + " "
        ret = "wire " + r +',\n\t\t'.join(str(x) for x in self.ids_or_assigns) + ";"
        return ret

class Reg(Ast):
    def __init__(self, kw, range_, ids_or_mem, last):
        self.pos = (kw.pos_stack, last.pos[1])
        self.range = range_
        if self.range:
            self.range.parent = self
        self.ids_or_mem = ids_or_mem
        for i in ids_or_mem: i.parent = self
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
        self.pos = (id_.pos_stack, range_.pos[1])
        self.id = id_.value
        self.id.parent = self
        self.range = range_
        self.range.parent = self
        self.value = id_.value
    def __str__(self):
        return self.value + " "+str(self.range)

class Always(Ast):
    def __init__(self, kw, statement):
        self.pos = (kw.pos_stack, statement.pos[1])
        self.statement = statement
        self.statement.parent = self
    def __str__(self):
        return "always " + str(self.statement)

class Edge(Ast):
    def __init__(self, polarity, signal):
        self.pos = (polarity.pos_stack, signal.pos[1])
        self.polarity = polarity.value
        self.signal = signal
        self.signal.parent = self
    def __str__(self):
        return str(self.polarity) + " " + self.signal.value

class ModuleInsts(Ast):
    def __init__(self, module_name, param_overrides, insts):
        self.pos = (module_name.pos[0], insts[-1].pos[1])
        self.module_name = module_name
        module_name.parent = self
        self.param_overrides = param_overrides
        for p in param_overrides:
            p.parent = self
        self.insts = insts
        for i in insts: i.parent = self
    def __str__(self):
        ret = self.module_name.value + " "
        if self.param_overrides:
            ret += "#(" + ',\n\t\t\t'.join(str(x) for x in self.param_overrides) + ")\n\t\t"
        ret += ', '.join(str(x) for x in self.insts)
        ret += ";"
        return ret

class ModuleInst(Ast):
    def __init__(self, inst_name, connections, right):
        self.pos = (inst_name.pos[0], right.pos_stack)
        self.inst_name = inst_name
        self.inst_name.parent = self
        self.connections = connections
        for c in connections: c.parent = self
    def __str__(self):
        return self.inst_name.value + ' (' + ',\n\t\t\t'.join(str(x) for x in self.connections) + ")"

class Connection(Ast):
    def __init__(self, dot, id_, expr, right):
        self.pos = (dot.pos_stack, right.pos_stack)
        self.id = id_
        self.id.parent = self
        self.expr = expr
        self.expr.parent = self
    def __str__(self):
        return "."+self.id.value+'('+str(self.expr)+')'

class Statement(Ast):
    pass

class Case(Statement):
    def __init__(self, kw, expr, items, end):
        self.pos = (kw.pos_stack, end.pos_stack)
        self.type = kw.value
        self.expr = expr
        self.items = items
    def __str__(self):
        ret = self.type+"(%s)\n\t\t" % str(self.expr)
        ret += '\n\t\t'.join(str(x) for x in self.items)
        ret += "\n\tendcase"
        return ret

class CaseItem(Ast):
    def __init__(self, expressions, statement):
        if type(expressions) in (list, tuple):
            pos0 = expressions[0].pos[0]
            self.expressions = expressions
        else:
            pos0 = expressions.pos_stack
            self.expressions = None
        if isinstance(statement, Statement):
            self.statement = statement
            self.pos = (pos0, statement.pos[1])
        else:
            self.statement = None
            self.pos = (pos0, statement.pos_stack)
    def __str__(self):
        if self.expressions:
            ret = ', '.join(str(x) for x in self.expressions) + " : "
        else:
            ret = 'default : '
        if self.statement:
            ret += str(self.statement)
        else:
            ret += ";"
        return ret

class Assign(Statement):
    def __init__(self, lval, op, rval, is_statement = False):
        self.pos = (lval.pos[0], rval.pos[1])
        self.lval = lval
        self.lval.parent = self
        self.op = op
        self.rval = rval
        if type(rval) != str:
            self.rval.parent = self
        self.is_statement = is_statement
    def __str__(self):
        ret = "%s %s %s" % (self.lval.value, str(self.op), str(self.rval))
        if self.is_statement:
            ret += ";"
        return ret
        
class At(Statement):
    def __init__(self, at, sens, statement):
        self.pos = (at.pos_stack, statement.pos[1])
        self.sens = sens
        if sens:
            for s in sens: s.parent = self
        self.statement = statement
        self.statement.parent = self
    def __str__(self):
        sens = self.sens
        if not sens: sens = "*"
        else: sens = ' or '.join(str(x) for x in sens)
        return "@(" + sens + ") " + str(self.statement)
class If(Statement):
    def __init__(self, kw, cond, true, false):
        self.pos = (kw.pos_stack, false.pos[1] if false else true.pos[1])
        self.cond = cond
        self.cond.parent = self
        self.true = true
        self.true.parent = self
        self.false = false
        self.false.parent = self
    def __str__(self):
        ret = "if ( " + str(self.cond) + " )\n\t\t\t" + str(self.true)
        if self.false:
            ret += "\n\t\telse\n\t\t\t" + str(self.false)
        return ret
class Block(Statement):
    def __init__(self, begin, name, statements, end):
        self.pos = (begin.pos_stack, _get_end(end))
        self.name = name
        self.statements = statements
    def __str__(self):
        return "begin\n\t\t" + '\n\t\t'.join(str(x) for x in self.statements) + "\n\tend"

class Expression(Ast):
    pass

class Id(Expression):
    def __init__(self, id_):
        self.pos = (id_.pos_stack, _get_end(id_))
        self.value = id_.value
    def __str__(self):
        return self.value


class PartSelect(Expression):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
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
        self.pos = (op.pos_stack, expr.pos[1])
        self.expr = expr
        self.expr.parent = self
        self.op = op.value
    def __str__(self):
        return '(' + str(self.op) + str(self.expr) + ')'

class Ternary(Expression):
    def __init__(self, cond, true, false):
        self.pos = (cond.pos[0], false.pos[1])
        self.cond = cond
        self.cond.parent = self
        self.true = true
        self.true.parent = self
        self.false = false
        self.false.parent = self
    def __str__(self):
        return '(' + str(self.cond) + ') ? (' + str(self.true) + ')\n\t\t: (' + str(self.false) + ')'

class Repetition(Expression):
    def __init__(self, left, repeat, concat, right):
        self.pos = (left.pos_stack, _get_end(right))
        self.repeat = repeat
        self.repeat.parent = self
        self.concat = concat
        self.concat.parent = self
    def __str__(self):
        return '{' + str(self.repeat) + str(self.concat) + '}'

class Concatenation(Expression):
    def __init__(self, left, expressions, right):
        self.pos = (left.pos_stack, _get_end(right))
        self.expressions = expressions
        for e in expressions: e.parent = self
    def __str__(self):
        return '{' + ', '.join(str(x) for x in self.expressions) + '}'

