
module gentest();
   genvar i;
   
   generate
      for (i = 0; i < 10; i = i + 1) begin:loop
	 case(i)
	   default: simple U_SIMPLE();
	   1 :      ansi U_ANSI();
	 endcase
      end
   endgenerate

   /*metav
    print(module)
    */
endmodule