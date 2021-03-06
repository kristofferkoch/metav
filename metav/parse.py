import ply.yacc
from ply.yacc import GRAMMAR as G
from .lex import tokens
import metav.vast as ast

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
    p[0] = ast.Module(p.slice[1], p[2], p[3], p[4], p[6], p.slice[7])

@G("""id : ID
         | SYS_ID""")
def p_id(p):
    p[0] = ast.Id(p.slice[1])

@G("""module_params_opt : empty
                        | module_params""")
def p_module_params_opt(p):
    p[0] = p[1]

@G("module_params : '#' '(' param_modports ')'")
def p_module_params(p):
    p[0] = p[3]

@G("param_modports : param_modport")
def p_param_modport_single(p):
    p[0] = [p[1]]
@G("param_modports : param_modports ',' param_modport")
def p_param_modport_new(p):
    p[0] = p[1]
    p[1].append(p[3])
@G("param_modports : param_modports ',' id_assign""")
def p_param_modports_newport(p):
    p[0] = p[1]
    p[1][-1].append(p[3])

@G("param_modport : PARAMETER range_opt id_assign")
def p_param_modport(p):
    p[0] = ast.Parameter(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

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
            p[1][-1].append(p[3])
            p[0] = p[1]
        else:
            p[1].append(p[3])
            p[0] = p[1]
    else:
        p[0] = [p[1]]

@G("modport : INPUT range_opt id")
def p_modport_input(p):
    p[0] = ast.Input(p[3], p[2])
    p[0].parse_info(p.slice[1], in_portlist=True)
@G("modport : OUTPUT reg_opt range_opt id")
def p_modport_output(p):
    p[0] = ast.Output(p[4], range=p[3], reg=p[2])
    p[0].parse_info(p.slice[1])
@G("modport : INOUT range_opt id""")
def p_modport_inout(p):
    p[0] = ast.Inout(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

@G("""reg_opt : empty
              | REG""")
def p_reg_opt(p):
    if p[1]:
        p[0] = p.slice[1]
    else:
        p[0] = None

@G("input_decl : INPUT range_opt list_of_ids")
def p_input_decl(p):
    p[0] = ast.Input(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

@G("""range_opt : range
                | empty""")
def p_range_opt(p):
    p[0] = p[1]

@G("range : '[' expression ':' expression ']'")
def p_range(p):
    p[0] = ast.Range(p[2], p[4])
    p[0].parse_info(p.slice[1], p.slice[5])

@G("""list_of_ids : id
                  | id ',' list_of_ids""")
def p_list_of_ids(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("output_decl : OUTPUT reg_opt range_opt list_of_ids")
def p_output_decl(p):
    p[0] = ast.Output(p[4], range=p[3], reg=p[2])
    p[0].parse_info(p.slice[1])

@G("inout_decl : INOUT range_opt list_of_ids")
def p_inout_decl(p):
    p[0] = ast.Inout(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

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
                  | genvar_decl ';'
                  | continous_assign ';'
                  | module_instantiation ';'
                  | always_block
                  | function_declaration
                  | metav
                  | generate""")
def p_module_item(p):
    p[0] = p[1]
    if len(p) > 2:
        p[0].extend_pos(p.slice[2])

@G("genvar_decl : GENVAR list_of_ids")
def p_genvar_decl(p):
    p[0] = ast.Genvars(p[2])
    p[0].parse_info(p.slice[1])

@G("generate : GENERATE generate_item ENDGENERATE")
def p_generate(p):
    p[0] = ast.Generate(p[2])
    p[0].parse_info(p.slice[1], p.slice[3])

@G("""generate_item : generate_for
                    | generate_if
                    | generate_case
                    | generate_block
                    | module_item""")
def p_generate_item(p):
    p[0] = p[1]

@G("generate_for : FOR '(' assign ';' expression ';' assign ')' generate_item")
def p_generate_for(p):
    p[0] = ast.GenerateFor(p[3], p[5], p[7], p[9]);
    p[0].parse_info(p.slice[1])

@G("""generate_if : IF '(' expression ')' generate_item ELSE generate_item
                  | IF '(' expression ')' generate_item %prec LOWER_THAN_ELSE""")
def p_generate_if(p):
    if len(p) > 6:
        p[0] = ast.GenerateIf(p[3], p[5], p[7])
    else:
        p[0] = ast.GenerateIf(p[3], p[5], None)
    p[0].parse_info(p.slice[1])

@G("generate_case : CASE '(' expression ')' generate_case_items ENDCASE")
def p_generate_case(p):
    p[0] = ast.GenerateCase(p[3], p[5])
    p[0].parse_info(p.slice[1], p.slice[6])

@G("""generate_case_items : empty
                          | generate_case_item generate_case_items""")
def p_generate_case_items(p):
    if p[1]:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

@G("""generate_case_item : DEFAULT ':' generate_item
                         | DEFAULT generate_item""")
def p_generate_case_item_default(p):
    p[0] = ast.GenerateCaseItem(None, p[len(p)-1])
    p[0].parse_info(p.slice[1])

@G("generate_case_item : expressions ':' generate_item")
def p_generate_case_item(p):
    p[0] = ast.GenerateCaseItem(p[1], p[3])

@G("generate_block : BEGIN ':' id generate_items END")
def p_generate_block(p):
    p[0] = ast.GenerateBlock(p[3], p[4])
    p[0].parse_info(p.slice[1], p.slice[5])

@G("""generate_items : empty
                     | generate_item generate_items""")
def p_generate_items(p):
    if p[1]:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

@G("metav : METAV")
def p_metav(p):
    p[0] = ast.Metav(p[1])

@G("""function_declaration : FUNCTION automatic_opt range_opt id ';' function_item_declarations statement ENDFUNCTION""")
def p_function_declaration(p):
    p[0] = ast.FunctionDeclaration(p[2], p[3], p[4], p[6], p[7])
    p[0].parse_info(p.slice[1], p.slice[8])

@G("automatic_opt : empty")
def p_automatic_empty(p):
    p[0] = False
@G("automatic_opt : AUTOMATIC")
def p_automatic_yes(p):
    p[0] = True

@G("""function_item_declarations : function_item_declaration
                                 | function_item_declaration function_item_declarations""")
def p_function_item_declarations(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

@G("""function_item_declaration : input_decl ';'
                                | parameter_decl ';'
                                | reg_decl ';'""")
def p_function_item_declaration(p):
    p[0] = p[1]
    p[0].extend_pos(p.slice[2])

@G("""parameter_decl : PARAMETER range_opt id_assigns
                     | LOCALPARAM range_opt id_assigns""")
def p_parameter_decl(p):
    p[0] = ast.Parameter(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

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
    p[0] = ast.Wire(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

@G("reg_decl : REG range_opt reg_ids")
def p_reg_decl(p):
    p[0] = ast.Reg(p[3], range=p[2])
    p[0].parse_info(p.slice[1])

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
    p[0].parse_info(p.slice[1])

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
        p[0] = ast.Assign(p[1], p[2], p[3])
    else:
        p[0] = p[1]

@G("""non_blocking_assign : id '<=' expression
                          | part_select '<=' expression
                          | concatenation '<=' expression""")
def p_non_blocking_assign(p):
    p[0] = ast.Assign(p[1], p[2], p[3])

@G("module_instantiation : id parameter_override_opt instantiations")
def p_module_instantiation(p):
    p[0] = ast.ModuleInsts(p[1], p[2], p[3])

@G("""parameter_override_opt : empty
                             | '#' '(' connections ')'""")
def p_parameter_override_opt(p):
    if len(p) > 2:
        p[0] = p[3]
    else:
        p[0] = []

@G("connections_opt : empty")
def p_connections_opt_empty(p):
    p[0] = []
@G("connections_opt : connections")
def p_connections_opt_some(p):
    p[0] = p[1]

@G("""connections : connection ',' connections
                  | connection""")
def p_connections(p):
    if len(p) > 2:
        p[3].insert(0, p[1])
        p[0] = p[3]
    else:
        p[0] = [p[1]]

@G("connection : '.' id '(' expression ')'")
def p_connection(p):
    p[0] = ast.Connection(p[2], p[4])
    p[0].parse_info(p.slice[1], p.slice[5])


@G("""instantiations : instantiation ',' instantiations
                     | instantiation""")
def p_instantiations(p):
    if len(p) > 2:
        p[3].insert(0, p[1])
        p[0] = p[3]
    else:
        p[0] = [p[1]]

@G("instantiation : id '(' connections_opt ')'")
def p_instantiation(p):
    p[0] = ast.ModuleInst(p[1], p[3])
    p[0].parse_info(p.slice[4])

@G("always_block : ALWAYS statement")
def p_always_block(p):
    p[0] = ast.Always(p[2])
    p[0].parse_info(p.slice[1])

@G("statement : BEGIN block_name_opt statements END")
def p_statement_block(p):
    p[0] = ast.Block(p[2], p[3])
    p[0].parse_info(p.slice[1], p.slice[4])
@G("""statement : IF '(' expression ')' statement_opt %prec LOWER_THAN_ELSE
                | IF '(' expression ')' statement_opt ELSE statement_opt""")
def p_statement_if(p):
    p[0] = ast.If(p[3], p[5], p[7] if len(p)>=8 else None)
    p[0].parse_info(p.slice[1])
@G("statement : FOR '(' assign ';' expression ';' assign ')' statement_opt")
def p_statement_for(p):
    p[0] = ast.For(p[3], p[5], p[7], p[9])
    p[0].parse_info(p.slice[1])
@G("statement : WHILE '(' expression ')' statement_opt")
def p_statement_while(p):
    p[0] = ast.While(p[3], p[5])
    p[0].parse_info(p.slice[1])
@G("""statement : '@' '*' statement_opt
                | '@' '(' '*' ')' statement_opt""")
def p_statement_comb(p):
    p[0] = ast.At(None, p[len(p)-1])
    p[0].parse_info(p.slice[1])
@G("statement : '@' '(' sensitivity_list ')' statement_opt")
def p_statement_sens(p):
    p[0] = ast.At(p[3], p[5])
    p[0].parse_info(p.slice[1])
@G("""statement : assign ';'
                | non_blocking_assign ';'""")
def p_statement_assign(p):
    p[0] = p[1]
    p[0].is_statement = True
    p[0].extend_pos(p.slice[2])

@G("""statement : CASE '(' expression ')' case_items ENDCASE
                | CASEZ '(' expression ')' case_items ENDCASE
                | CASEX '(' expression ')' case_items ENDCASE""")
def p_statement_case(p):
    p[0] = ast.Case(p[3], p[5])
    p[0].parse_info(p.slice[1], p.slice[6])

@G("statement : id arglist_opt ';'")
def p_statement_task_call(p):
    p[0] = ast.TaskCall(p[1], p[2])
    p[0].parse_info(p.slice[1], p.slice[3])

@G("""arglist_opt : empty
                  | '(' ')'
                  | '(' expressions ')'""")
def p_arglist_opt(p):
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = []

@G("""statements : statement statements
                 | empty""")
def p_statements(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

@G("statement_opt : statement")
def p_statement_opt(p):
    p[0] = p[1];
@G("statement_opt : ';'")
def p_statement_opt_null(p):
    p[0] = p.slice[1]

@G("""block_name_opt : empty
                     | block_name""")
def p_block_name_opt(p):
    p[0] = p[1]

@G("block_name : ':' id")
def p_block_name(p):
    p[0] = p[1]

@G("""sensitivity_list : sensitivity OR sensitivity_list
                       | sensitivity""")
def p_sensitivity_list(p):
    if len(p) > 2:
        p[3].insert(0, p[1])
        p[0] = p[3]
    else:
        p[0] = [p[1]]

@G("""sensitivity : id
                  | POSEDGE id
                  | NEGEDGE id""")
def p_sensitivity(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.Edge(p.slice[1], p[2])

@G("""case_items : case_item case_items
                 | case_item""")
def p_case_items(p):
    if len(p) > 2:
        p[0] = p[2]
        p[2].insert(0, p[1])
    else:
        p[0] = [p[1]]

@G("""case_item : DEFAULT ':' statement_opt
                | DEFAULT statement_opt""")
def p_case_item_default(p):
    p[0] = ast.CaseItem(p.slice[1], p[len(p)-1])
@G("case_item : expressions ':' statement_opt")
def p_case_item(p):
    p[0] = ast.CaseItem(p[1], p[3])

@G("""expression : NUMBER
                 | REAL
                 | STRING
                 | binary_op
                 | unary_op
                 | ternary_op
                 | concatenation
                 | repetition
                 | part_select
                 | function_call""")
def p_expression(p):
    p[0] = p[1]
@G("""expression : '(' expression ')'""")
def p_expression_paran(p):
    p[0] = p[2]
@G("""expression : id""")
def p_expression_id(p):
    p[0] = p[1]

@G("function_call : id '(' expressions ')'")
def p_function_call(p):
    p[0] = ast.FunctionCall(p[1], p[3])
    p[0].parse_info(p.slice[4])


@G("concatenation : '{' expressions '}'")
def p_concatenation(p):
    p[0] = ast.Concatenation(p[2])
    p[0].parse_info(p.slice[1], p.slice[3])

@G("repetition : '{' expression concatenation '}'")
def p_repetition(p):
    p[0] = ast.Repetition(p[2], p[3])
    p[0].parse_info(p.slice[1], p.slice[4])

@G("""expressions : expression ',' expressions
                  | expression""")
def p_expressions(p):
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

@G("part_select : id '[' expression ']'")
def p_part_select_single(p):
    p[0] = ast.PartSelect(type="single", id=p[1], expr=p[3], end=p.slice[4])
@G("part_select : id '[' expression ':' expression ']'")
def p_part_select_range(p):
    p[0] = ast.PartSelect(type="range", id=p[1], msb=p[3], lsb=p[5], end=p.slice[6])
@G("part_select : id '[' expression '+:' expression ']'")
def p_part_select_plus(p):
    p[0] = ast.PartSelect(type="plus", id=p[1], lsb=p[3], size=p[5], end = p.slice[6])

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
    p[0] = ast.UnaryOp(p.slice[1], p[2])

@G("ternary_op : expression '?' expression ':' expression %prec TERNARY")
def p_ternary_op(p):
    p[0] = ast.Ternary(p[1], p[3], p[5])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")
    print(p)

def vParser():
    return ply.yacc.yacc()

if __name__ == "__main__":
    from preproc import preproc
    from lex import vLexer
    lexer, codes = vLexer()
    parser = vParser()
    
    import sys
    p = preproc(sys.argv[1], incpath=("../test/include",))
    print(p)
    r = parser.parse(input=p, lexer=lexer, debug=0)
    for m in r:
        print(m)
