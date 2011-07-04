`include "include.v"
`define Y 15 // single
`define X [`A:0]
`define Z 76 /* multi
	      line*/

module preproc(/*AUTOARG*/
   // Outputs
   out,
   // Inputs
   x, clk, rst_n
   );
`include "params.v"
   /* Block comment 
    line 2*/
   // Here comes a def:
   input x; // this is a def
   output `X out;
   /*metav_delete:input  clk, rst_n;:metav_delete*/
   
   reg 	  [8*80:0] stringreg;
   always @*
     stringreg = "hello, world /*";
   /*metav
    print(module)
    */
   /*metav_generated:*/
   wire 	   should_be_removed;
   /*:metav_generated*/
`ifdef NOT_DEF
   syntax_error;
`else
   assign foo = bar;
`endif
endmodule
