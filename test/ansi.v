// ASCII a stupid question, get a stupid ANSI:
module ansi(input clk, rst_n, d_in,
	    output reg d_out);
   
   always @(posedge clk or negedge rst_n)
     if (!rst_n)
       d_out <= 1'b0;
     else
       d_out <= d_in;

   /*metav
    print("portstyle: "+ module.portstyle)
    */
   
endmodule // ansi
