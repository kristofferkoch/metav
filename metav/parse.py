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

import ply.yacc
from ply.yacc import GRAMMAR as G
from lex import tokens
import vast as ast

@G('''source : empty
             | module source''')
def p_source(p):
    if p[1]:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []
@G('empty :')
def p_empty(p):
    p[0] = None

@G("module : MODULE ID list_of_modports_opt ';' module_items ENDMODULE")
def p_module(p):
    p[0] = ast.Module(p[2], p[3], p[5])

@G("""list_of_modports_opt : empty
                           | list_of_modports""")
def p_list_of_modports_opt(p):
    p[0] = p[1]

@G("list_of_modports : '(' modports_opt ')'")
def p_list_of_modports(p):
    p[0] = p[2]

@G("""modports_opt : empty
                   | modports""")
def p_modports_opt(p):
    p[0] = p[1]

@G("""modports : modport
               | modport ',' modports""")
def p_modports(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("""modport : ID
              | input_decl
              | output_decl
              | inout_decl""")
def p_modport(p):
    p[0] = p[1]

@G("input_decl : INPUT range_opt list_of_ids")
def p_input_decl(p):
    p[0] = ast.Input(p[2], p[3])

@G("""range_opt : range
                | empty""")
def p_range_opt(p):
    p[0] = p[1]

@G("range : '[' expression ':' expression ']'")
def p_range(p):
    p[0] = ast.Range(p[2], p[4])

@G("""list_of_ids : ID
                  | ID ',' list_of_ids""")
def p_list_of_ids(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("output_decl : OUTPUT range_opt list_of_ids")
def p_output_decl(p):
    p[0] = ast.Output(p[2], p[3])

@G("inout_decl : INOUT range_opt list_of_ids")
def p_inout_decl(p):
    p[0] = ast.Inout(p[2], p[3])

@G("""module_items : module_item module_items
                   | empty""")
def p_module_items(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

@G("""module_item : parameter_decl ';'
                  | input_decl ';'
                  | output_decl ';'
                  | inout_decl ';'
                  | wire_decl ';'
                  | reg_decl ';'
                  | continous_assign ';'
                  | module_instantiation ';'
                  | always_block""")
def p_module_item(p):
    p[0] = p[1]

@G("""parameter_decl : PARAMETER id_assigns
                     | LOCALPARAM id_assigns""")
def p_parameter_decl(p):
    p[0] = ast.Parameter(p[1], p[2])

@G("""id_assigns : id_assign
                 | id_assign ',' id_assigns""")
def p_id_assigns(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("id_assign : ID '=' expression")
def p_id_assign(p):
    p[0] = ast.Assign(p[1], p[2], p[3])

@G("""wire_decl : WIRE range_opt list_of_ids
                | WIRE range_opt id_assigns""")
def p_wire_decl(p):
    p[0] = ast.Wire(p[2], p[3])

@G("reg_decl : REG range_opt reg_ids")
def p_reg_decl(p):
    pass

@G("""reg_ids : reg_id ',' reg_ids
              | reg_id""")
def p_reg_ids(p):
    pass

@G("reg_id : ID range_opt")
def p_reg_id(p):
    pass

@G("continous_assign : ASSIGN assigns")
def p_continous_assign(p):
    p[0] = ast.ContAssigns(p[2])

@G("""assigns : assign ',' assigns
              | assign""")
def p_assigns(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("""assign : id_assign
             | part_select '=' expression
             | concatenation '=' expression""")
def p_assign(p):
    if len(p) > 2:
        pass
    else:
        p[0] = p[1]

@G("""non_blocking_assign : ID '<=' expression
                          | part_select '<=' expression
                          | concatenation '<=' expression""")
def p_non_blocking_assign(p):
    p[0] = ast.Assign(p[1], p[2], p[3])

@G("module_instantiation : ID parameter_override_opt instantiations")
def p_module_instantiation(p):
    pass

@G("""parameter_override_opt : empty
                             | '#' '(' connections ')'""")
def p_parameter_override_opt(p):
    pass

@G("""connections : connection ',' connections
                  | connection""")
def p_connections(p):
    pass

@G("connection : '.' ID '(' expression ')'")
def p_connection(p):
    pass

@G("""instantiations : instantiation ',' instantiations
                     | instantiation""")
def p_instantiations(p):
    pass

@G("instantiation : ID '(' connections ')'")
def p_instantiation(p):
    pass

@G("always_block : ALWAYS statement")
def p_always_block(p):
    p[0] = ast.Always(p[2])

@G("statement : BEGIN statements END")
def p_statement_block(p):
    p[0] = ast.Block(p[2])
@G("""statement : IF '(' expression ')' statement_opt %prec LOWER_THAN_ELSE
                | IF '(' expression ')' statement_opt ELSE statement_opt""")
def p_statement_if(p):
    p[0] = ast.If(p[3], p[5], p[7] if len(p)>=8 else None)
@G("""statement : '@' '*' statement_opt
                | '@' '(' '*' ')' statement_opt""")
def p_statement_comb(p):
    p[0] = ast.At(None, p[len(p)-1])
@G("statement : '@' '(' sensitivity_list ')' statement_opt")
def p_statement_sens(p):
    p[0] = ast.At(p[3], p[5])
@G("""statement : assign ';'
                | non_blocking_assign ';'""")
def p_statement_assign(p):
    p[0] = p[1]

@G("""statement : CASE '(' expression ')' case_items ENDCASE
                | CASEZ '(' expression ')' case_items ENDCASE""")
def p_statement(p):
    pass

@G("""statements : statement statements
                 | empty""")
def p_statements(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

@G("""statement_opt : statement
                    | ';'""")
def p_statement_opt(p):
    p[0] = p[1]

@G("""sensitivity_list : sensitivity OR sensitivity_list
                       | sensitivity""")
def p_sensitivity_list(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("""sensitivity : ID
                  | POSEDGE ID
                  | NEGEDGE ID""")
def p_sensitivity(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Edge(p[1], p[2])

@G("""case_items : case_item case_items
                 | case_item""")
def p_case_items(p):
    pass

@G("""case_item : DEFAULT ':' statement_opt
                | DEFAULT statement_opt
                | expressions ':' statement_opt""")
def p_case_item(p):
    pass

@G("""expression : NUMBER
                 | STRING
                 | ID
                 | binary_op
                 | unary_op
                 | ternary_op
                 | concatenation
                 | repetition
                 | part_select
                 | '(' expression ')'""")
def p_expression(p):
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = p[1]

@G("concatenation : '{' expressions '}'")
def p_concatenation(p):
    p[0] = ast.Concatenation(p[2])

@G("repetition : '{' expression concatenation '}'")
def p_repetition(p):
    p[0] = ast.Repetition(p[2], p[3])


@G("""expressions : expression ',' expressions
                  | expression""")
def p_expressions(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

@G("""part_select : ID '[' expression ']'
                  | ID '[' expression ':' expression ']'
                  | ID '[' expression '+:' expression ']'""")
def p_part_select(p):
    pass

precedence = (
    ('nonassoc', 'LOWER_THAN_ELSE'),
    ('nonassoc', 'ELSE'),
    ('left', 'TERNARY'),
    ('left', "'||'"),
    ('left', "'&&'"),
    ('left', "'|'"),
    ('left', "'^'"),
    ('left', "'&'"),
    ('left', "'=='", "'==='", "'!='", "'!=='"),
    ('left', "'<'", "'>'", "'<='", "'>='"),
    ('left', "'<<'", "'>>'"),
    ('left', "'+'", "'-'"),
    ('left', "'*'", "'/'", "'%'"),
    ('right', 'UNARY')
    )

@G("""binary_op : expression '+' expression
                | expression '-' expression
                | expression '*' expression
                | expression '/' expression
                | expression '%' expression
                | expression '<<' expression
                | expression '>>' expression
                | expression '<' expression
                | expression '>' expression
                | expression '>=' expression
                | expression '<=' expression
                | expression '==' expression
                | expression '===' expression
                | expression '!=' expression
                | expression '!==' expression
                | expression '&' expression
                | expression '^' expression
                | expression '|' expression
                | expression '&&' expression
                | expression '||' expression""")
def p_binary_op(p):
    p[0] = ast.BinaryOp(p[1], p[2], p[3])

@G("""unary_op : '!' expression %prec UNARY
               | '~' expression %prec UNARY
               | '-' expression %prec UNARY
               | '+' expression %prec UNARY
               | '|' expression %prec UNARY
               | '&' expression %prec UNARY
               | '^' expression %prec UNARY""")
def p_unary_op(p):
    p[0] = ast.UnaryOp(p[1], p[2])

@G("ternary_op : expression '?' expression ':' expression %prec TERNARY")
def p_ternary_op(p):
    p[0] = ast.Ternary(p[1], p[3], p[5])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")
    print(p)

if __name__ == "__main__":
    from preproc import preproc
    from lex import vLexer
    lexer, codes = vLexer()
    parser = ply.yacc.yacc()
    
    p = preproc("../test/simple.v")
    print(p)
    r = parser.parse(input=p, lexer=lexer, debug=0)
    for m in r:
        print(m)
