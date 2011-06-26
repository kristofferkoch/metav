`include "include.v"
`define Y 15 // single
`define X [`A:0]
`define Z 76 /* multi
	      line*/

module test(/*AUTOARG*/);
   /* Block comment 
    line 2*/
   // Here comes a def:
   input x; // this is a def
   output out;
   input  clk, rst_n;
   
   reg 	  stringreg = "hello, kitty ";
   
endmodule // test
