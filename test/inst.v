module inst;
   parameter X = 5, Y = X-2;
   
   ansi #(.X(X),.Y(Y)) U_ANSI(/*AUTOINST*/
	       // Outputs
	       .d_out			(d_out),
	       // Inputs
	       .clk			(clk[0]),
	       .rst_n			(rst_n[4+:1]),
	       .d_in			(d_in));

   //x U_ERR(.x(x));
   
   /*metav
    #print(globals())
    for iname in module.insts:
      print("In module "+iname)
      print(module.insts[iname].module.ids)
      assert(module.insts[iname].module.parent == module)
    */
endmodule // inst
