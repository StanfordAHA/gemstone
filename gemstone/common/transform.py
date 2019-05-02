from ..generator.from_magma import FromMagma
from ..generator.generator import Generator, PortReference
import magma
import mantle
from typing import List, Union, Iterable, Tuple
from ordered_set import OrderedSet
from collections import OrderedDict


def pass_signal_through(gen: Generator, signal):
    """Takes in an existing input of the tile and creates and output
       to pass the signal through
       returns the new output port reference
    """
    pass_through = None
    if signal in gen.ports.values():
        pass_through = signal
    elif signal in gen.ports.keys():
        pass_through = gen.ports[signal]
    assert pass_through is not None, "Cannot find " + pass_through
    # Create output port for pass through
    output_name = pass_through.qualified_name() + "_out"
    gen.add_port(output_name, magma.Out(pass_through.base_type()))
    # Actually make the pass through connection
    gen.wire(pass_through, gen.ports[output_name])
    return gen.ports[output_name]


def or_reduction(gen: Generator, sub_circuit_name: str, signal_name: str,
                 config_data_width: int,
                 sub_circuit_port_name: str = "O"):
    """Embeds @signal_name reduction network in tile by accepting a @signal_name
       input from another tile and ORing it with the origin @@signal_name
       output of this tile to create a new read_data output.

        @signal_name has to be connected to @sub_circuit_name
    """
    pass_through = gen.ports[signal_name]
    input_name = pass_through.qualified_name() + "_in"
    # Create input port for pass through @signal_name reduction
    gen.add_port(input_name, magma.In(pass_through.base_type()))
    # get the sub circuit
    sub_circuit = getattr(gen, sub_circuit_name)
    # Remove the current connection to the @signal_name output
    gen.remove_wire(sub_circuit.ports[sub_circuit_port_name], pass_through)
    read_data_reduce_or = FromMagma(mantle.DefineOr(2, config_data_width))
    read_data_reduce_or.underlying.name = f"{signal_name}_or"
    # OR previous read_data output with @signal_name input to create NEW
    # @signal_name output
    gen.wire(sub_circuit.ports[sub_circuit_port_name],
             read_data_reduce_or.ports.I0)
    gen.wire(gen.ports[input_name], read_data_reduce_or.ports.I1)
    gen.wire(read_data_reduce_or.ports.O, pass_through)

    return gen.ports[input_name]


def __get_external_ports(parent: Generator, generators: List[Generator],
                         ignored_ports: List[PortReference]):
    # we use a (name, id) pair because there may be duplicated names
    # in internal connections.
    # for instance, say we have three generators gen_1, gen_2, gen3,
    # their internal connections are
    # gen_1.O -> gen_2.I and gen_2.O -> gen_2.I
    ports = OrderedSet()
    # since generator is not hashable, we will use its id instead
    id_to_owner = {}
    for gen in generators:
        for port in gen.ports.values():
            owner_id = id(port.owner())
            port_name = port.qualified_name()
            if port in ignored_ports:
                continue
            ports.add((port_name, owner_id))
            id_to_owner[owner_id] = port.owner()

    # remove them if one of the port is connected
    for conn1, conn2 in parent.wires:
        conn1_name = conn1.qualified_name()
        conn2_name = conn2.qualified_name()
        conn1_id = id(conn1.owner())
        conn2_id = id(conn2.owner())
        conn1_entry = conn1_name, conn1_id
        conn2_entry = conn2_name, conn2_id
        if conn1_entry in ports and conn2_entry in ports:
            ports.remove(conn1_entry)
            ports.remove(conn2_entry)
    # notice that these external ports have to be unique as a group
    result = OrderedDict()
    result_ids = set()
    for port_name, owner_id in ports:
        assert port_name not in result, "External ports have to be unique"
        result[port_name] = id_to_owner[owner_id]
        result_ids.add(owner_id)

    return result, result_ids


def replace(parent: Generator, old_gen: Union[Generator, Iterable[Generator]],
            new_gen: Union[Generator, Iterable[Generator]],
            ignored_ports: Union[List[PortReference],
                                 Tuple[PortReference]] = ()):
    """
    replace the old_gen with the new generator. The interfaces of
    @old_gen has to be the same as the @new_gen while counting the internal
    connections

    :param parent: parent generator that holds the old_gen
    :param old_gen: target generators to be replaced
    :param new_gen: new generators to use
    :param ignored_ports: ports to ignore when doing replacement. it's caller's
                          responsibility to keep track of this
    :return: None
    """
    # we first make sure that the interfaces are the same
    if not isinstance(old_gen, (list, tuple)):
        old_gen = [old_gen]
    if not isinstance(new_gen, (list, tuple)):
        new_gen = [new_gen]
    # get external ports
    old_gen_ports, old_gen_ids = __get_external_ports(parent, old_gen,
                                                      ignored_ports)
    new_gen_ports, new_gen_ids = __get_external_ports(parent, new_gen,
                                                      ignored_ports)

    assert len(old_gen_ports) == len(new_gen_ports)
    # this matching algorithm is n^2
    # unless we know something about the port names (i.e. unique)
    # this is the best we can do
    for port_name, owner in old_gen_ports.items():
        assert port_name in new_gen_ports
        old_port = owner.ports[port_name]
        new_port = new_gen_ports[port_name].ports[port_name]
        assert old_port.base_type() == new_port.base_type()

    # looping through the wires in parent that need to be replaced
    wires = set()
    for conn_from, conn_to in parent.wires:
        if id(conn_from.owner()) in old_gen_ids:
            wires.add((conn_from, conn_to))
        if id(conn_to.owner()) in old_gen_ids:
            wires.add((conn_from, conn_to))

    # remove the wires
    for conn_from, conn_to in wires:
        parent.remove_wire(conn_from, conn_to)

    # adding wires back using the new generator
    for conn_from, conn_to in wires:
        if id(conn_from.owner()) in old_gen_ids:
            next_port = conn_to
            current_port = conn_from.clone()

            new_generator = new_gen_ports[conn_from.qualified_name()]
        else:
            assert id(conn_to.owner()) in old_gen_ids
            next_port = conn_from
            current_port = conn_to.clone()
            new_generator = new_gen_ports[conn_to.qualified_name()]

        # reconstructing the port based on the ops stored in the original port
        # slices
        new_port = current_port.get_port(new_generator.ports)
        parent.wire(new_port, next_port)
