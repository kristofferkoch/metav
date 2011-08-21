module functions();

   function test;
      input a, b, c, d;
      begin
	 test = a*b + c*d;
      end
   endfunction //

   always @*
     x = test(1,2,3,4);
   
   
   /*metav
    print(module)
    */

endmodule // functions
