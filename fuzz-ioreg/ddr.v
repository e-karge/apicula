// IOLOGIC primitives for comparing the IOLOGIC input wires with the vendor
module top(input clk, input fclk, output o_oddr, inout b_oddr, output o_oser4, input i_iddr, output x);
    reg [31:0] n = 0;
    always @(posedge clk) n <= {n[30:0], ~(n[31] ^ n[21] ^ n[1] ^ n[0])};
    ODDR od0(.D0(n[0]), .D1(n[1]), .TX(1'b0), .CLK(clk), .Q0(o_oddr), .Q1());
    wire q0, q1, bi;
    ODDR od1(.D0(n[2]), .D1(n[3]), .TX(n[4]), .CLK(clk), .Q0(q0), .Q1(q1));
    IOBUF bb(.I(q0), .OEN(q1), .O(bi), .IO(b_oddr));
    OSER4 os(.D0(n[5]), .D1(n[6]), .D2(n[7]), .D3(n[8]), .TX0(1'b0), .TX1(1'b0), .PCLK(clk), .FCLK(fclk), .RESET(1'b0), .Q0(o_oser4), .Q1());
    wire [1:0] iq;
    IDDR id(.D(i_iddr), .CLK(clk), .Q0(iq[0]), .Q1(iq[1]));
    assign x = iq[0] ^ iq[1] ^ bi;
endmodule
