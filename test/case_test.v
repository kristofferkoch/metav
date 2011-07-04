module case_test;

   always @*
     casez(sel)
       2'b00: x = 1'b0;
       2'b01: x = 1'b1;
       2'b1?:;
       default: x = 1'bz;
     endcase

   /*metav
    print(module);
    */
endmodule // case_test
