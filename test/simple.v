module simple(/*AUTOARG*/
   // Outputs
   o,
   // Inputs
   clk, rst_n, a, b
   ); //line
   parameter IN_SIZE = 4; // Line comment applied to IN_SIZE
   localparam IN_MSB = IN_SIZE - 1, // applied to IN_MSB, as first identifier on line
     OUT_SIZE = IN_SIZE + 1,
     OUT_MSB = OUT_SIZE - 1;
   
   input clk, rst_n;
   input [IN_MSB:0] a, b;
   output [OUT_MSB:0] o;

   reg [OUT_MSB:0]     d;
   
   wire 	       rst = !rst_n;
   
   assign o = 2*a + -b ? fortyten : d;

   always @(posedge clk or negedge rst_n)
     if (!rst_n)
       d <= {OUT_SIZE{1'b0}};
     else
       d <= o;
   always @* begin
      hello = world;
      all = work + and | no * play == makes ^ !jack & a % dull / boy;
   end
   /*metav
    "Docstring goes here. Note the indentation."
    x = "hello world"
    print(x.capitalize())
    print(module)
    for id in module.ids:
       print(id+":\t"+repr(module.ids[id]))
    */
   /*metav generated:*/
   assign ignored = "This code is ignored by the lexer";
   syntax errors are ignored;
   Lexer errors are also ignored: ¤;
   /*end metav generated*/
endmodule
