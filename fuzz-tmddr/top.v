// ODDR tristate (TX -> Q1 -> OEN) into IOBUF and ELVDS_IOBUF; controls: IOBUF
// with OEN from the fabric, ODDR into OBUF
module top(input clk, inout io_t, inout io_d, inout io_db, inout io_f, output o_q, output x);
    reg [30:0] n = 0;
    always @(posedge clk) n <= {n[29:0], ~(n[30] ^ n[27])};
    wire q_t, t_t, i_t;
    ODDR oddr_t(.D0(n[0]), .D1(n[1]), .TX(n[2]), .CLK(clk), .Q0(q_t), .Q1(t_t));
    IOBUF buf_t(.I(q_t), .OEN(t_t), .O(i_t), .IO(io_t));
    wire q_d, t_d, i_d;
    ODDR oddr_d(.D0(n[3]), .D1(n[4]), .TX(n[5]), .CLK(clk), .Q0(q_d), .Q1(t_d));
    ELVDS_IOBUF buf_d(.I(q_d), .OEN(t_d), .O(i_d), .IO(io_d), .IOB(io_db));
    wire i_f;
    IOBUF buf_f(.I(n[6]), .OEN(n[7]), .O(i_f), .IO(io_f));
    ODDR oddr_q(.D0(n[8]), .D1(n[9]), .TX(1'b0), .CLK(clk), .Q0(o_q), .Q1());
    reg r = 0;
    always @(posedge clk) r <= i_t ^ i_d ^ i_f;
    assign x = r;
endmodule
