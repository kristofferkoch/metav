module compact
  #(parameter size = 8,
              msb = size - 1)
  (input clk, rst_n,
   input [msb:0] d_in,
   output reg [msb:0] d_out);

   parameter [7:0] sized_param = 5;
   
   always @(posedge clk or negedge rst_n)
     if (!rst_n)
       d_out <= {size{1'b0}};
     else
       d_out <= d_in;
		
endmodule