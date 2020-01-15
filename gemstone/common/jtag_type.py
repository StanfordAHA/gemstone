import magma


JTAGType = magma.Product.from_fields("JTAG", dict(
    tdi=magma.In(magma.Bit),
    tdo=magma.Out(magma.Bit),
    tms=magma.In(magma.Bit),
    tck=magma.In(magma.Clock),
    trst_n=magma.In(magma.AsyncReset)
))
