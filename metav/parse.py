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

@G("module : MODULE id module_params_opt list_of_ports_opt ';' module_items ENDMODULE")
def p_module(p):
    p[0] = ast.Module(p[2], p[3], p[4], p[6])

@G("id : ID")
def p_id(p):
    p[0] = p.slice[1]

@G("""module_params_opt : empty
                        | module_params""")
def p_module_params_opt(p):
    p[0] = p[1]

@G("module_params : '#' '(' PARAMETER id_assigns ')'")
def p_module_params(p):
    p[0] = p[4]

@G("""list_of_ports_opt : empty
                        | '(' list_of_ids ')'
                        | '(' modports_opt ')'""")
def p_list_of_ports_opt(p):
    if p[1]:
        p[0] = p[2]
    else:
        p[0] = p[1]

@G("""modports_opt : empty
                   | modports""")
def p_modports_opt(p):
    p[0] = p[1]

@G("""modports : modport
               | modports ',' modport
               | modports ',' id""")
def p_modports(p):
    if len(p) > 2:
        if hasattr(p[3], 'value'):
            p[1][-1].ids.append(p[3])
            p[0] = p[1]
        else:
            p[1].append(p[3])
            p[0] = p[1]
    else:
        p[0] = [p[1]]

@G("modport : INPUT range_opt id")
def p_modport_input(p):
    p[0] = ast.Input(p[2], [p[3]], True)
@G("modport : OUTPUT reg_opt range_opt id")
def p_modport_output(p):
    p[0] = ast.Output(p[2], p[3], [p[4]], True)
@G("modport : INOUT range_opt id""")
def p_modport_inout(p):
    p[0] = ast.Inout(p[2], [p[3]], True)

@G("""reg_opt : empty
              | REG""")
def p_reg_opt(p):
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

@G("""list_of_ids : id
                  | id ',' list_of_ids""")
def p_list_of_ids(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("output_decl : OUTPUT reg_opt range_opt list_of_ids")
def p_output_decl(p):
    p[0] = ast.Output(p[2], p[3], p[4])

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

@G("""parameter_decl : PARAMETER range_opt id_assigns
                     | LOCALPARAM range_opt id_assigns""")
def p_parameter_decl(p):
    p[0] = ast.Parameter(p[1], p[2], p[3])

@G("""id_assigns : id_assign
                 | id_assign ',' id_assigns""")
def p_id_assigns(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("id_assign : id '=' expression")
def p_id_assign(p):
    p[0] = ast.Assign(p[1], p[2], p[3])

@G("""wire_decl : WIRE range_opt list_of_ids
                | WIRE range_opt id_assigns""")
def p_wire_decl(p):
    p[0] = ast.Wire(p[2], p[3])

@G("reg_decl : REG range_opt reg_ids")
def p_reg_decl(p):
    p[0] = ast.Reg(p[2], p[3])

@G("""reg_ids : reg_id ',' reg_ids
              | reg_id""")
def p_reg_ids(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]];

@G("reg_id : id range_opt")
def p_reg_id(p):
    if p[2]:
        p[0] = ast.MemReg(p[1], p[2])
    else:
        p[0] = p[1]

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

@G("""non_blocking_assign : id '<=' expression
                          | part_select '<=' expression
                          | concatenation '<=' expression""")
def p_non_blocking_assign(p):
    p[0] = ast.Assign(p[1], p[2], p[3])

@G("module_instantiation : id parameter_override_opt instantiations")
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

@G("connection : '.' id '(' expression ')'")
def p_connection(p):
    pass

@G("""instantiations : instantiation ',' instantiations
                     | instantiation""")
def p_instantiations(p):
    pass

@G("instantiation : id '(' connections ')'")
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
    p[0].is_statement = True

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

@G("""sensitivity : id
                  | POSEDGE id
                  | NEGEDGE id""")
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
                 | binary_op
                 | unary_op
                 | ternary_op
                 | concatenation
                 | repetition
                 | part_select""")
def p_expression(p):
    p[0] = p[1]
@G("""expression : '(' expression ')'""")
def p_expression_paran(p):
    p[0] = p[2]
@G("""expression : id""")
def p_expression_id(p):
    p[0] = ast.Id(p[1])


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

@G("""part_select : id '[' expression ']'
                  | id '[' expression ':' expression ']'
                  | id '[' expression '+:' expression ']'""")
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
    
    import sys
    p = preproc(sys.argv[1], incpath=("../test/include",))
    print(p)
    r = parser.parse(input=p, lexer=lexer, debug=0)
    for m in r:
        print(m)
