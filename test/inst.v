module inst;
   parameter X = 5, Y = X-2;
   
   ansi #(.X(X),.Y(Y)) U_ANSI(/*AUTOINST*/
	       // Outputs
	       .d_out			(d_out),
	       // Inputs
	       .clk			(clk[0]),
	       .rst_n			(rst_n[4+:1]),
	       .d_in			(d_in));
   
endmodule // inst
