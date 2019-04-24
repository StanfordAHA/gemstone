# Gemstone

Gemstone is a next-generation hardware generator infrastructure. It is intended to be a step forward from verilog or text-based generators. The main idea is to model hardware components in software and expose clear and well thought-out API's to modify hardware components (ala object oriented programming in software). We also draw from compiler design by introducing the notion of passes, which can be composed to perform structured transformations of a hardware design. Asa corollary of the object-oriented model, our system also enables early consideration of aspects *beyond* logical (RTL) design (e.g. physical design collateral, verification).

Gemstone has 2 major aspects: First is the core generator infrastructure which designers can leverage to build generators. Second, it is a philosophy/set of design principles and guidelines that enables productive generator design.

## Gemstone Generator Infrastructure System Design
The generator infrastructure in Gemstone can be seen as a dynamic layer on top of a structural RTL description language. In particular, Gemstone is built around Magma (cite). Magma uses python classes to describe hardware circuit definitions. The base class (interface) for all Gemstone generators is the `Generator` class. The `Generator` class has the following core member functions:
- `add_port(self, name, type)`: This function adds a port to the staged circuit modeled by this class. The argument `type` is expected as a directed Magma type, e.g. `magma.In(magma.Bits(16))`.
- `wire(self, port0, port1)`: This function wires together two generator ports. The ports can either be inputs/outputs of `self`, or inputs/outputs of a sub-instance of this generator (with the exception of wiring constants). The typing rules of Magma apply to the `wire` function; **however, these type checks are performed at elaboration time**. Wires are **not** directional; i.e. `wire(a, b)` is equivalent to `wire(b, a)`.
- `remove_wire(self, port0, port1)`: If `wire(self, port0, port1)` was called, then calling `unwire` with the same ports (or with the ports flipped) removes the connection between the ports. Assuming the original call to `wire` does not have any side effects (which it inherently does not), then calling `unwire` with the same ports will basically place the system in a state as though the original `wire` call was never made.
- `children(self)`: This function returns all sub-generators instanced in the generator as an ordered set. These generators are collected by inspecting all the wires in the parent generator (created by calls to `wire()`). For each port in each wire, we add the originating generator to the ordered set.
- `circuit(self)`: This function elaborates the generator and returns a magma circuit. There are two high level cases:
  * The `circuit` function is not overriden by the child class. In this case the default logic to construct the magma circuit is as follows. First, every port added through `add_port()` is added to the interface of the magma circuit. Then, instances placed inside this generator are collected by a call to `self.children()`. Each of these instances is placed inside the magma circuit defined. Finally, each call to `wire` is translated to a call to `magma.wire()` directly. In this way, each generator class in Gemstone can be seen as a staged magma circuit.
  * The `circuit` function is overriden by the child class. In this case, the child class can perform custom code to generate the magma circuits. This is the path we use for wrapping verilog, magma, and genesis code.

In addition to those methods, all child classes of `Generator` can access:
- The `ports` member variable which is a dictionary of ports added through `add_port()`.
- The `wires` member variable which is a list of tuples of ports connected through `wire()`.

## Pass Infrastructure
Using both the generic API's exposed by the `Generator` base class, as well as custom API's exposed by individual components, designers can write passes that transform the generators. Currently gemstone does not impose any specific definition or restrictions for passes; in fact almost any kind of transformation is possible given the flexibility of python. However, Gemstone carries with it the following set of guidelines and philosophy:
- As much as possible, transformations should be well defined, abstracted away, and implemented as API's on component classes. For example, if on a specific component a common operation is to add a set of ports, rather than requiring the user to always make a series of calls to `add_port()`, there should be a single function exposed which abstracts away the `add_port()` call.
- Similarly, passes should be as reusable and generic as possible. For example, if a common operation that needs to happen is to take a specific input port of a generator and add an output port and pass-through that input, that operation should be abstracted over the generator and port name. Furthermore, if this operation needs to be performed hierarchically (i.e. on all descendants), the pass should leverage recursion and use the `children()` method.

### Familes of Passes (TODO)
We imagine a few important paradigms of passes that would come as part of the generator infrastructure:
- Replacement: a replacement pass would iterate the graph (again using the `children()` method) and replace instances satisfying some condition (the most prevelant condition being that an instance is that of a specific class) with another instance with the same interface. For example, if we may use a standard library implementation of a common module (e.g. mux, register) that should be replaced with a technology specific implementation.
- Wrapping: a wrapping pass would iterate the graph and wrap each generator satisfying some condition using another common generator.
- Insertion: an insertion pass would iterate over a set of wires and replace the wire with a new instance (of some generator) that would would sit between the previous source and destination ports of the original wire.

