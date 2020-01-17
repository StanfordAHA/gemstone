import magma
import warnings
from ..generator.generator import Generator
import os

# Use kwargs left, right, top, bottom to match other blocks
# with correct side of primary block
# Allowed kwargs : left, right, top, bottom

def __get_external_connections(pin):
    ext_conns = []
    for conn in pin._connections:
        if (conn.owner() not in (pin.owner().children())) and (conn.owner() != pin.owner()):
            ext_conns.append(conn)
    return ext_conns

def __reorder_pins(pin_dict, side_1, side_2):
    s1_pins = pin_dict[side_1]
    s2_pins = pin_dict[side_2]
    s2_pin_names = list(map(lambda pin_obj: pin_obj.qualified_name(), s2_pins))
    for i, pin in enumerate(s1_pins):
        ext_conns = __get_external_connections(pin)
        if ext_conns[0].qualified_name() in s2_pin_names:
            curr_idx = s2_pin_names.index(ext_conns[0].qualified_name())
            s2_pin_names.insert(i, s2_pin_names.pop(curr_idx))
            s2_pins.insert(i, s2_pins.pop(curr_idx))
        else:
            warnings.warn(f"{side_1} side pin {pin.qualified_name()} not found \
                            in {side_2} side connections. Abutment may not \
                            be possible")
    return pin_dict
            

def assign_abutted_pins(primary: Generator, **kwargs):
    # Make sure kwargs are valid
    for side in kwargs.keys():
        if side not in ['left', 'right', 'top', 'bottom']:
            raise Exception('kwarg key must be left, right, top, or bottom')

    pin_objs = {'left': [], 'right': [], 'top': [], 'bottom': [], 'other': []}   

    for port in primary.ports.values():
        # Remove any internal connections
        conns = __get_external_connections(port)
        if len(conns) == 1:
            for side, inst in kwargs.items():
                if conns[0].owner() == inst:
                    pin_objs[side].append(port)
                    break
        elif len(conns) == 0:
            pin_objs['other'].append(port)
        else:
            raise Exception('cannot abut port with fanout connection')

    # Make L/R, T/B ordering consistent
    pin_objs = __reorder_pins(pin_objs, 'left', 'right') 
    pin_objs = __reorder_pins(pin_objs, 'top', 'bottom') 

    # Spit out the pin names for each side 
    for side, pin_list in pin_objs.items():
        filename = f"pinning_results/{side}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            for pin in pin_list:
                f.write(f"{pin.qualified_name()}\n")
        f.close()

