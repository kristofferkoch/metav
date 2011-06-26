`include "include.v"
`define Y 15 // single
`define X [`A:0]
`define Z 76 /* multi
	      line*/

module test(/*AUTOARG*/
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
   input  clk, rst_n;
   
   reg 	  [8*80:0] stringreg;
   always @*
     stringreg = "hello, world /*";
   
endmodule // test
