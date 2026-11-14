import sys

stack = 0

Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

# STACK_FINISHED = 0b000
# AXIS_ADJUSTED = 0b11
# CONTEXT_1 = 0b001
# CONTEXT_2 = 0b010
# CONTEXT_3 = 0b110
# CONTEXT_4 = 0b100
# CONTEXT_5 = 0b101

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}

y_height = 2  # 32
y_buffer = 2
n = 4

dynamic_variables = {
    "just_removed": 0,
    "active_axis": Y_AXIS,
    "y1": 3 * y_height + y_height + y_buffer,
    "y2": -1,
    "z1": n,
    "z2": 0,
    "x": n + 2,
    "dx": n + 1,
    "dy": 0,
    "dz": 1,
    "dummy": 2,
    "first_loop": 1,
    "negative_z": 0,
}

constants = {
    # constants, don't modify until optimizing later
    "Y_HEIGHT": y_height,
    "N": n,
    "C1": 3 * y_height + y_height + y_buffer,
    "C2": y_height + y_buffer,
    "C3": n + 2,
    "C4": y_height + y_buffer - 3,
    "ZERO": 0,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "MINUS_ONE": -1,
    "MINUS_TWO": -2,
}

constant_addresses = {c: i for (i, c) in enumerate(constants)}
dynamic_variable_addresses = {c: (16 + i) for (i, c) in enumerate(dynamic_variables)}

var_addresses = dynamic_variable_addresses | constant_addresses

address_to_var = {v: k for k, v in var_addresses.items()}


def to_binary_string(num, length):
    num &= ((1 << length) - 1)
    assert num >= 0
    return ("0" * length + bin(num)[2:])[-length:]


variables = constants | dynamic_variables

for v, val in variables.items():
    print(to_binary_string(var_addresses[v], 5) + " " + to_binary_string(val, 12))

supported_branch_instructions = {
    "NONE": 0,
    "POP": 1,
    "NONZERO": 2,
    "NEGATIVE": 3,
}

code_to_branch = {v: k for (k, v) in supported_branch_instructions.items()}

supported_register_instructions = {
    "ADD": 0,
    "SUB": 1,
    "COPY": 2,
    "XOR": 3,
}
code_to_reg = {v: k for (k, v) in supported_register_instructions.items()}

supported_stack_instructions = {
    "NONE": 0,
    "TOGGLE": 1,
    "PUSH_0": 2,
    "PUSH_1": 3,
}

code_to_stack = {v: k for (k, v) in supported_stack_instructions.items()}

supported_output = {
    "pulse": 2,
    "return_toggle": 4,
    "fetch_toggle": 6,

    "return_sp": 8,
    "fetch_sp": 10,

    "return_o": 12,
    "fetch_o": 14,

    "return_ysp": 92,
    "fetch_ysp": 96,
    "return_p": 100,
    "fetch_yp": 104,
    "return_yo": 108,
    "fetch_yo": 112,
}

states = set()


def handle_output(output):
    global count
    # print(count)
    match output:
        case "pulse":
            print(f"pulse {variables["dx"]}")
        case "fetch_toggle":
            if variables['dy'] & 1 == 1:
                print("toggle y")
            if variables['dz'] & 1 == variables['negative_z'] & 1:
                print("toggle z")
            if variables['dx'] & 1 == 1:
                print("toggle x")
        case "return_toggle":  # the two toggles can be merged if the output came at the end of the state,
            # in which case active_axis would do the job
            if variables['dx'] & 1 == 1:
                print("toggle x")
            if variables['dz'] & 1 == variables['negative_z'] & 1:
                print("toggle z")
            if variables['dy'] & 1 == 1:
                print("toggle y")
        case "fetch_yp":
            print(f"install yp")
        case "fetch_sp":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"install {name}{"sp"}{sign}")
        case "fetch_ysp":
            print(f"install ysp")
        case "fetch_yo":
            print("install yo")
        case "fetch_o":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"install {name}{"o"}{sign}")
        case "return_p":
            print(f"remove yp")
        case "return_sp":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"remove {name}{"sp"}{sign}")
        case "return_ysp":
            print(f"remove ysp")
        case "return_yo":
            print(f"remove yo")
        case "return_o":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"remove {name}{"o"}{sign}")


def to_int(binary_string):
    return eval("0b" + binary_string)


def instruction_from_string(s):
    address, instruction, output = s.split(" ")
    address = to_int(address)
    B = to_int(instruction[:5][::-1])
    A = to_int(instruction[5:10][::-1])
    O = to_int(instruction[10:12])
    C = to_int(instruction[12:14])
    S = to_int(instruction[14:16])
    T = to_int(instruction[16::2])
    F = to_int(instruction[17::2])

    i = Instruction(
        code_to_stack[S],
        code_to_reg[O],
        code_to_branch[C],
        address_to_var[B],
        address_to_var[A],
        T ^ F ^ address,
        F ^ address,
        output=output if output != "None" else None,
        address=address
    )
    print(str(i))
    print(s)
    assert str(i) == s
    return i


class Instruction:
    def __init__(self,
                 stack_instruction,
                 register_instruction,
                 branch_instruction,
                 first_register_address,
                 second_register_address,
                 true_branch,
                 false_branch,
                 output=None,
                 address=None):
        assert stack_instruction in supported_stack_instructions
        assert register_instruction in supported_register_instructions
        assert branch_instruction in supported_branch_instructions
        assert output is None or output in supported_output
        self.data = (stack_instruction,
                     register_instruction,
                     branch_instruction,
                     first_register_address,
                     second_register_address,
                     true_branch,
                     false_branch,
                     output)
        # if self.data in states:
        #     print(f"duplicate state {self.data}")
        states.add(self.data)
        self.stack_instruction = stack_instruction
        self.register_instruction = register_instruction
        self.branch_instruction = branch_instruction
        self.B = first_register_address
        self.A = second_register_address
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.output = output
        self.address = address

    def get_data(self):
        return self.data

    def __call__(self, *args, **kwargs):
        global stack
        global variables
        if self.output is not None:
            handle_output(self.output)
        match self.stack_instruction:
            case "TOGGLE":
                stack ^= 1
            case "PUSH_0":
                stack <<= 1
            case "PUSH_1":
                stack <<= 1
                stack |= 1
            case "NONE":
                pass
            case _:
                assert False
        match self.register_instruction:
            case "ADD":
                operation_result = variables[self.A] + variables[self.B]
            case "SUB":
                operation_result = variables[self.A] - variables[self.B]
            case "COPY":
                operation_result = variables[self.B]
            case "XOR":
                operation_result = variables[self.A] ^ variables[self.B]
            case _:
                assert False
        match self.branch_instruction:
            case "NONE":
                variables[self.A] = operation_result
                return self.true_branch
            case "POP":
                variables[self.A] = operation_result
                bit = stack & 1
                stack >>= 1
                return self.true_branch if bit == 1 else self.false_branch
            case "NONZERO":
                return self.true_branch if operation_result != 0 else self.false_branch
            case "NEGATIVE":
                return self.true_branch if operation_result < 0 else self.false_branch
            case _:
                assert False

    def __str__(self):

        global var_addresses

        ret_val = ("000000000" + bin(self.address)[2:])[-8:] + " "
        F = ("000000000" + bin(self.false_branch ^ self.address)[2:])[-8:]
        if "b" in F:
            print(bin(self.false_branch ^ self.address))
            assert False
        T = ("000000000" + bin(self.true_branch ^ self.false_branch)[2:])[-8:]

        TF = "".join(u + v for u, v in zip(T, F))

        S = ("000000000" + bin(supported_stack_instructions[self.stack_instruction])[2:])[-2:]
        C = ("000000000" + bin(supported_branch_instructions[self.branch_instruction])[2:])[-2:]
        O = ("000000000" + bin(supported_register_instructions[self.register_instruction])[2:])[-2:]
        A = ("000000000" + bin(var_addresses[self.B])[2:])[-5:]
        B = ("000000000" + bin(var_addresses[self.A])[2:])[-5:]

        A = A[::-1]
        B = B[::-1]

        return ret_val + A + B + O + C + S + TF + " " + str(self.output)


def PUSH(c, X, output=None):
    return Instruction(stack_instruction=f"PUSH_{c}",
                       register_instruction="COPY",
                       branch_instruction="NONE",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=X,
                       output=output)


def POP(X, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="POP",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=Y,
                       output=output)


def ADD(x, y, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="ADD",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Y,
                       false_branch=Y,
                       output=output)


def SUB(x, y, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="SUB",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Y,
                       false_branch=Y,
                       output=output)


def EQUALS(x, y, IF_TRUE, IF_FALSE, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="XOR",
                       branch_instruction="NONZERO",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=IF_FALSE,
                       false_branch=IF_TRUE,
                       output=output)


def LE(x, y, IF_TRUE, IF_FALSE, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="SUB",
                       branch_instruction="NEGATIVE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=IF_FALSE,
                       false_branch=IF_TRUE,
                       output=output)


def COPY(x, y, Z, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Z,
                       false_branch=Z,
                       output=output)


def OUTPUT(X, output):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="NONE",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=X,
                       output=output)


def RETURN(X, cargo):
    return OUTPUT(X, f"return_{cargo}")


HALT = 255

instructions = {
    # begin main loop
    0: EQUALS("ONE", "first_loop", 10001, 10002),
    10001: EQUALS("C2", "y1", 138, 10003),
    10002: EQUALS("ZERO", "y1", 160, 10004),
    10003: SUB("THREE", "y1", 10005),
    10004: SUB("ONE", "y1", 10006),
    10005: ADD("ONE", "y2", 20001),
    10006: ADD("THREE", "y2", 20001),

    20001: COPY("ZERO", "z1", 20002),
    20002: COPY("N", "z2", 2),
    # begin first main z while loop
    2: EQUALS("ZERO", "z2", 0, 3),
    3: ADD("ONE", "z1", 40001),
    40001: COPY("TWO", "x", 4),
    # begin first main x while loop
    4: EQUALS("C3", "x", 136, 5),
    5: COPY("y2", "dy", 6),
    6: COPY("x", "dx", 7),
    7: COPY("z1", "dz", 8),
    8: COPY("ONE", "negative_z", 901),
    # after stack processing, update temp variables
    801: COPY("y1", "dy", 802),
    802: COPY("z2", "dz", 803),
    803: COPY("x", "dx", 804),
    804: COPY("ZERO", "negative_z", 51),
    # after second stack processing, update temp variables
    # increment x counter in x while loop
    135: ADD("ONE", "x", 4),
    # increment z counter in z while loop
    136: SUB("ONE", "z2", 2),
    # increment y counter in y while loop

    # second main loop
    138: COPY("Y_HEIGHT", "y1", 139),
    139: COPY("C4", "y2", 140),
    140: COPY("ZERO", "first_loop", 0),

    # restore the variables to their initial states
    160: COPY("ONE", "first_loop", 161),
    161: COPY("MINUS_ONE", "y2", 162),
    162: COPY("C1", "y1", HALT),

    # recursively_remove_1
    901: COPY("ZERO", "dummy", 9),
    # determine_active_axis()
    9: LE("TWO", "dy", 10, 11),
    10: COPY("THREE", "active_axis", 26),
    11: EQUALS("THREE", "active_axis", 12, 15),
    12: PUSH(1, 14),

    14: PUSH(1, 15),
    # handle z
    15: LE("TWO", "dz", 16, 17),
    16: COPY("TWO", "active_axis", 26),
    17: LE("TWO", "active_axis", 18, 21),
    18: PUSH(1, 20),

    20: PUSH(1, 21),
    # handle x
    21: LE("TWO", "dx", 22, 23),
    22: COPY("ONE", "active_axis", 26),
    23: PUSH(1, 2601),

    # 25: PUSH(1, 2601),
    2601: Instruction(stack_instruction=f"PUSH_1",
                      register_instruction="COPY",
                      branch_instruction="NONE",
                      first_register_address="ZERO",
                      second_register_address="active_axis",
                      true_branch=26,
                      false_branch=26,
                      output=None),
    # decode where we called determine_active_axis
    26: LE("TWO", "dummy", 28, 27),
    27: EQUALS("ZERO", "dummy", 29, 52),
    28: EQUALS("TWO", "dummy", 81, 112),

    # recursively_remove_1 after call to determine_active_axis
    29: EQUALS("ZERO", "active_axis", 31, 3208),
    31: COPY("ONE", "just_removed", 61, "return_toggle"),  # return from rr1

    # Call modify_active_axis with various values of dummy
    3208: COPY("MINUS_TWO", "dummy", 33),
    3209: COPY("MINUS_ONE", "dummy", 33),
    3201: COPY("ONE", "dummy", 33),
    3202: COPY("TWO", "dummy", 33),

    # modify_active_axis(dummy)
    33: EQUALS("THREE", "active_axis", 34, 35),
    34: ADD("dummy", "dy", 38),
    35: EQUALS("TWO", "active_axis", 36, 37),
    36: ADD("dummy", "dz", 38),
    37: ADD("dummy", "dx", 38),
    # decode where we called modify_active_axis
    # if true we were called in rr1
    38: EQUALS("MINUS_TWO", "dummy", 48, 39),
    # if true we were called in ri6
    39: EQUALS("TWO", "dummy", 61, 40),
    40: EQUALS("ONE", "dummy", 41, 51),
    # called with 1
    41: POP(61, 901),

    # finish recursively_remove_1
    # 47: FETCH(48),

    48: EQUALS("THREE", "active_axis", 4801, 4802),
    4801: PUSH(1, 49, "fetch_ysp"),
    4802: PUSH(1, 49, "fetch_sp"),
    49: PUSH(0, 50),
    50: PUSH(1, 51),

    # recursively install 1
    # call determine_active_axis
    51: COPY("ONE", "dummy", 9),
    52: EQUALS("ZERO", "active_axis", 54, 55),
    54: COPY("ZERO", "just_removed", 61, "fetch_toggle"),  # return from RI1
    55: PUSH(0, 56),
    56: PUSH(0, 57),
    57: PUSH(1, 3209),

    # process_stack_instruction
    61: EQUALS("ZERO", "just_removed", 62, 69),
    62: POP(63, 64),  # ___ 0

    63: POP(76, 66),  # __1 0
    64: POP(67, 68),  # __0 0

    66: POP(77, 103),  # _01 0
    67: POP(126, 108),  # _10 0
    68: POP(99, 7601),  # _00 0

    69: POP(70, 71),  # ___ 1

    70: POP(76, 73),  # __1 1
    71: POP(74, 75),  # __0 1

    73: POP(119, 96),  # _01 1
    74: POP(129, 93),  # _10 1
    75: POP(129, 7601),  # _00 1
    # 111 on stack, just_removed anything
    76: ADD("ONE", "active_axis", 61),
    7601: EQUALS("ONE", "negative_z", 801, 135),

    # rr2
    77: PUSH(0, 78),
    78: PUSH(1, 79),
    79: PUSH(0, 80),
    80: COPY("TWO", "dummy", 9),
    81: EQUALS("ZERO", "active_axis", 8301, 87),
    8301: POP(8303, 8303, "pulse"),

    8303: Instruction(stack_instruction=f"NONE",
                      register_instruction="ADD",
                      branch_instruction="POP",
                      first_register_address="ONE",
                      second_register_address="active_axis",
                      true_branch=901,
                      false_branch=901,
                      output=None),

    87: EQUALS("THREE", "active_axis", 8701, 8702),
    8701: PUSH(1, 88, "fetch_yo"),
    8702: PUSH(1, 88, "fetch_o"),
    88: PUSH(0, 89),
    89: PUSH(0, 3209),

    # rr5 is just 93

    92: PUSH(0, 3201),
    93: Instruction(stack_instruction=f"PUSH_0",
                    register_instruction="XOR",
                    branch_instruction="NONZERO",
                    first_register_address="THREE",
                    second_register_address="active_axis",
                    true_branch=9302,
                    false_branch=9301,
                    output=None),
    9301: PUSH(0, 95, "return_ysp"),
    9302: PUSH(0, 95, "return_sp"),
    95: PUSH(1, 92),

    # rr6
    96: COPY("ONE", "just_removed", 98),
    96: Instruction(stack_instruction=f"PUSH_1",
                    register_instruction="COPY",
                    branch_instruction="NONE",
                    first_register_address="ONE",
                    second_register_address="just_removed",
                    true_branch=3201,
                    false_branch=3201,
                    output=None),

    # rr3
    99: PUSH(1, 100),
    100: PUSH(1, 101),
    101: PUSH(0, 901),

    # ri2
    103: EQUALS("THREE", "active_axis", 1031, 1032),
    1031: PUSH(0, 104, "fetch_yp"),
    1032: PUSH(0, 104, "fetch_sp"),
    104: PUSH(1, 89),

    # ri3
    108: PUSH(1, 109),
    109: PUSH(0, 110),
    110: Instruction(stack_instruction=f"PUSH_1",
                     register_instruction="COPY",
                     branch_instruction="NONE",
                     first_register_address="THREE",
                     second_register_address="dummy",
                     true_branch=9,
                     false_branch=9,
                     output=None),
    # 111: COPY("THREE", "dummy", 9),
    112: EQUALS("ZERO", "active_axis", 8301, 121),

    # ri6
    119: EQUALS("THREE", "active_axis", 11901, 11902),
    11901: COPY("ZERO", "just_removed", 3202, "return_p"),
    11902: COPY("ZERO", "just_removed", 3202, "return_sp"),

    # other branch of ri3
    121: EQUALS("THREE", "active_axis", 12101, 12102),

    12101: PUSH(1, 104, "fetch_yo"),
    12102: PUSH(1, 104, "fetch_o"),
    # 122: PUSH(1, 89),
    # call modify_active_axis

    # ri4
    126: PUSH(1, 127),
    127: PUSH(0, 101),

    # ri5
    129: EQUALS("THREE", "active_axis", 12901, 12902),
    12901: RETURN(92, "yo"),
    12902: RETURN(92, "o"),

    # rr4 is ri5???

}

def opt_dce(instructions, start=0):
    visited = {start}
    queue = [start]

    while len(queue) > 0:
        address = queue.pop()
        instruction = instructions[address]
        successors = {instruction.true_branch, instruction.false_branch}

        for new_address in successors:
            if new_address == HALT or new_address in visited:
                continue

            visited.add(new_address)
            queue.append(new_address)

    changed = False

    for address in set(instructions) - visited:
        print(f"Removed dead instruction {address}")

        changed = True

        del instructions[address]

    return changed

def is_nop_register_instruction(instruction):
    return instruction.register_instruction == "COPY" and instruction.A == "ZERO" and instruction.B == "ZERO"

def merge_instructions(first_instruction, second_instruction):
    if first_instruction.stack_instruction == "NONE":
        stack_instruction = second_instruction
    elif second_instruction.stack_instruction == "NONE":
        stack_instruction = first_instruction
    else:
        return None

    if is_nop_register_instruction(first_instruction):
        register_instruction = second_instruction
    elif is_nop_register_instruction(second_instruction):
        register_instruction = first_instruction
    else:
        return None

    if first_instruction.output is None:
        output_instruction = second_instruction
    elif second_instruction.output is None:
        output_instruction = first_instruction
    else:
        return None

    return Instruction(
            stack_instruction=stack_instruction.stack_instruction,
            register_instruction=register_instruction.register_instruction,
            branch_instruction=second_instruction.branch_instruction,
            first_register_address=register_instruction.B,
            second_register_address=register_instruction.A,
            true_branch=second_instruction.true_branch,
            false_branch=second_instruction.false_branch,
            output=output_instruction.output)

def can_reorder_instructions(first_instruction, second_instruction):
    return first_instruction.branch_instruction == "NONE" and second_instruction.branch_instruction == "NONE" and (first_instruction.stack_instruction == "NONE" or second_instruction.stack_instruction == "NONE") and ((first_instruction.A != second_instruction.A and first_instruction.A != second_instruction.B and first_instruction.B != second_instruction.A) or is_nop_register_instruction(first_instruction) or is_nop_register_instruction(second_instruction))

def opt_fold_forward(instructions, start=0):
    changed = False

    for first_address, first_instruction in instructions.items():
        if first_instruction.branch_instruction != "NONE" or first_instruction.true_branch == HALT:
            continue

        second_address = first_instruction.true_branch
        second_instruction = instructions[second_address]

        if new_instruction := merge_instructions(first_instruction, second_instruction):
            print(f"Merged instruction {second_address} into {first_address}")

            changed = True

            instructions[first_address] = new_instruction
        else:
            third_address = second_address
            third_instruction = second_instruction
            visited_instructions = [third_instruction]

            while third_instruction.branch_instruction == "NONE" and third_instruction.true_branch != HALT:
                predecessors = set()

                for address, instruction in instructions.items():
                    if instruction.true_branch == third_address or instruction.false_branch == third_address:
                        predecessors.add(address)

                if len(predecessors) > 1:
                    break

                fourth_address = third_instruction.true_branch
                fourth_instruction = instructions[fourth_address]

                if fourth_instruction.branch_instruction != "NONE":
                    break

                can_reorder = True

                for instruction in visited_instructions:
                    if not can_reorder_instructions(instruction, fourth_instruction):
                        can_reorder = False

                        break

                if not can_reorder:
                    break

                if new_instruction := merge_instructions(first_instruction, fourth_instruction):
                    print(f"Merged instruction {fourth_address} into {first_address}")

                    changed = True

                    instructions[first_address] = Instruction(
                            stack_instruction=new_instruction.stack_instruction,
                            register_instruction=new_instruction.register_instruction,
                            branch_instruction=new_instruction.branch_instruction,
                            first_register_address=new_instruction.B,
                            second_register_address=new_instruction.A,
                            true_branch=second_address,
                            false_branch=second_address,
                            output=new_instruction.output)

                    instructions[third_address] = Instruction(
                            stack_instruction=third_instruction.stack_instruction,
                            register_instruction=third_instruction.register_instruction,
                            branch_instruction=third_instruction.branch_instruction,
                            first_register_address=third_instruction.B,
                            second_register_address=third_instruction.A,
                            true_branch=fourth_instruction.true_branch,
                            false_branch=fourth_instruction.false_branch,
                            output=third_instruction.output)

                    break

                third_address = fourth_address
                third_instruction = fourth_instruction

                visited_instructions.append(fourth_instruction)

    return changed

changed = True

while changed:
    changed = False
    changed |= opt_dce(instructions)
    changed |= opt_fold_forward(instructions)

# old_to_new = {255: 255}
#
# index = 0
# for k in instructions:
#     old_to_new[k] = index
#     index += 1
#
# new_instructions = {}
#

def reindex_instructions(insts, old_start, old_halt):
    old_to_new = {}
    new_to_old = {}

    for ind, inst in insts.items():
        if inst.output is not None:
            index = supported_output[inst.output]
            if index in new_to_old:
                index += 1
            assert index not in new_to_old

            old_to_new[ind] = index
            new_to_old[index] = ind

    print(old_to_new)
    print(new_to_old)

    for k in insts:
        if k not in old_to_new:
            index = 0
            while index in new_to_old:
                index += 1
            old_to_new[k] = index
            new_to_old[index] = k

    old_to_new[old_halt] = old_to_new[old_start] + 128

    new_instructions = {}
    for k, v in insts.items():
        (stack_instruction,
         register_instruction,
         branch_instruction,
         first_register_address,
         second_register_address,
         true_branch,
         false_branch,
         output) = v.get_data()
        true_branch = old_to_new[true_branch]
        false_branch = old_to_new[false_branch]
        new_instructions[old_to_new[k]] = Instruction(*(stack_instruction,
                                                        register_instruction,
                                                        branch_instruction,
                                                        first_register_address,
                                                        second_register_address,
                                                        true_branch,
                                                        false_branch,
                                                        output,
                                                        old_to_new[k]))
    return new_instructions, old_to_new[old_start], old_to_new[old_halt]


def from_observer_matrix(path):
    machine = {}
    with open(path) as f:
        for l in f.readlines():
            inst = instruction_from_string(l.strip())
            machine[inst.address] = inst
    return machine, 0, 128

count = 0


def run_instructions(start=0):
    global count

    witnessed_variables = set()
    new_instructions, new_start, new_halt = from_observer_matrix("observer_matrix.txt") #  reindex_instructions(instructions, start, HALT)
    new_code = new_start

    # print(len(variables), len(instructions))
    # print(variables)

    print("Start:", new_start, "Halt:",new_halt)
    with open("test42b.txt", "w", encoding="utf-8") as f:
        out = sys.stdout
        sys.stdout = f

        while new_code != new_halt:
            witnessed_variables.add(new_code)

            count += 1
            current_instruction = new_instructions[new_code]
            new_code = current_instruction()

            # print("Step:", count)
            # print("Instruction just executed:", current_instruction.address, current_instruction)
            # print("Instruction just executed:", current_instruction.data)
            # print("Next instruction:", new_code)
            # print("Stack:", bin(stack))
            # print("Variables:", variables)
            # print()
            # time.sleep(0.1)
        sys.stdout = out
    print(f"Total {count} steps")
    # print(len(variables), len(new_instructions), len(witnessed_variables))
    # print(variables)
    #
    # print(var_addresses)
    # for i in range(len(new_instructions)):
    #     print(new_instructions[i])


run_instructions()
