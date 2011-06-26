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

class Ast(object):
    pass

class Module(Ast):
    def __init__(self, name, modports, items):
        self.name = name
        self.modports = modports
        self.items = items

    def __str__(self):
        ret = "module %s" % (self.name.value,)
        if type(self.modports) == list:
            ret += ' (' + ', '.join(str(x) for x in self.modports) + ')'
        ret += ";\n\t"
        ret += '\n\t'.join(str(x) for x in self.items)
        ret += "\nendmodule"
        return ret

class Input(Ast):
    def __init__(self, range_, ids, in_portlist=False):
        self.range = range_
        self.ids = ids;
        self.in_portlist = in_portlist
    def __str__(self):
        ret = "input "
        if self.range: ret += str(self.range) + " "
        ret += ',\n\t\t'.join(x.value for x in self.ids)
        if not self.in_portlist: ret += ";"
        return ret
class Output(Ast):
    def __init__(self, range_, ids, in_portlist=False):
        self.range = range_
        self.ids = ids;
        self.in_portlist = in_portlist

    def __str__(self):
        ret = "output "
        if self.range: ret += str(self.range) + " "
        ret += ',\n\t\t'.join(x.value for x in self.ids)
        if not self.in_portlist: ret += ";"
        return ret
class Inout(Ast):
    def __init__(self, range_, ids, in_portlist=False):
        self.range = range_
        self.ids = ids;
        self.in_portlist = in_portlist

    def __str__(self):
        ret = "inout "
        if self.range: ret += str(self.range) + " "
        ret += ',\n\t\t'.join(self.ids)
        if not self.in_portlist: ret += ";"
        return ret

class Range(Ast):
    def __init__(self, msb, lsb):
        self.msb = msb
        self.lsb = lsb
    def __str__(self):
        return "["+str(self.msb)+":"+str(self.lsb)+"]"

class ContAssigns(Ast):
    def __init__(self, assigns):
        self.assigns = assigns
    def __str__(self):
        return "assign " + '\n'.join(str(x) for x in self.assigns) + ";"

class Parameter(Ast):
    def __init__(self, type_, ids):
        self.type = type_
        self.ids = ids
    def __str__(self):
        return self.type + " " + ',\n\t\t'.join(str(x) for x in self.ids) + ";";

class Wire(Ast):
    def __init__(self, range_, ids_or_assigns):
        self.range = range_
        self.ids_or_assigns = ids_or_assigns;
    def __str__(self):
        r = ""
        if self.range:
            r = str(self.range) + " "
        ret = "wire " + r +',\n\t\t'.join(str(x) for x in self.ids_or_assigns) + ";"
        return ret

class Reg(Ast):
    def __init__(self, range_, ids_or_mem):
        self.range = range_
        self.ids_or_mem = ids_or_mem
    def __str__(self):
        r = ""
        if self.range:
            r = str(self.range) + " "
        return "reg " + r + ",\n\t\t".join(x.value for x in self.ids_or_mem) + ";"

class Always(Ast):
    def __init__(self, statement):
        self.statement = statement
    def __str__(self):
        return "always " + str(self.statement)

class Edge(Ast):
    def __init__(self, polarity, signal):
        self.polarity = polarity
        self.signal = signal
    def __str__(self):
        return str(self.polarity) + " " + self.signal.value

class Statement(Ast):
    pass

class Assign(Statement):
    def __init__(self, lval, op, rval, is_statement = False):
        self.lval = lval
        self.op = op
        self.rval = rval
        self.is_statement = is_statement
    def __str__(self):
        ret = "%s %s %s" % (self.lval.value, str(self.op), str(self.rval))
        if self.is_statement:
            ret += ";"
        return ret
        
class At(Statement):
    def __init__(self, sens, statement):
        self.sens = sens
        self.statement = statement
    def __str__(self):
        sens = self.sens
        if not sens: sens = "*"
        else: sens = ' or '.join(str(x) for x in sens)
        return "@(" + sens + ") " + str(self.statement)
class If(Statement):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false
    def __str__(self):
        ret = "if ( " + str(self.cond) + " )\n\t\t\t" + str(self.true)
        if self.false:
            ret += "\n\t\telse\n\t\t\t" + str(self.false)
        return ret
class Block(Statement):
    def __init__(self, statements):
        self.statements = statements
    def __str__(self):
        return "begin\n\t\t" + '\n\t\t'.join(str(x) for x in self.statements) + "\n\tend"

class Expression(Ast):
    pass

class Id(Expression):
    def __init__(self, id_):
        self.id = id_
    def __str__(self):
        return self.id.value

class BinaryOp(Expression):
    def __init__(self, a, op, b):
        self.a = a
        self.op = op
        self.b = b
    def __str__(self):
        return '(' + ' '.join(str(x) for x in (self.a, self.op, self.b)) + ')'

class UnaryOp(Expression):
    def __init__(self, op, expr):
        self.expr = expr
        self.op = op
    def __str__(self):
        return '(' + str(self.op) + str(self.expr) + ')'

class Ternary(Expression):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false
    def __str__(self):
        return '(' + str(self.cond) + ') ? (' + str(self.true) + ')\n\t\t: (' + str(self.false) + ')'

class Repetition(Expression):
    def __init__(self, repeat, concat):
        self.repeat = repeat
        self.concat = concat
    def __str__(self):
        return '{' + str(self.repeat) + str(self.concat) + '}'

class Concatenation(Expression):
    def __init__(self, expressions):
        self.expressions = expressions
    def __str__(self):
        return '{' + ', '.join(str(x) for x in self.expressions) + '}'
