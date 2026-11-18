Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

supported_branch_instructions = {
    "NONE": 0,
    "POP": 1,
    "NONZERO": 2,
    "NEGATIVE": 3,
}

supported_register_instructions = {
    "ADD": 0,
    "SUB": 1,
    "COPY": 2,
    "XOR": 3,
}

supported_stack_instructions = {
    "NONE": 0,
    "TOGGLE": 1,
    "PUSH_0": 2,
    "PUSH_1": 3,
}

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

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}

states = set()


def to_binary_string(num, length):
    num &= ((1 << length) - 1)
    assert num >= 0
    return ("0" * length + bin(num)[2:])[-length:]


def to_int(binary_string):
    return eval("0b" + binary_string)


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

    def __call__(self, stack, variables):

        if self.output is not None:
            handle_output(self.output, variables)
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
                return self.true_branch, stack, variables
            case "POP":
                variables[self.A] = operation_result
                bit = stack & 1
                stack >>= 1
                return (self.true_branch, stack, variables) if bit == 1 else (self.false_branch, stack, variables)
            case "NONZERO":
                return (self.true_branch, stack, variables) if operation_result != 0 else (self.false_branch, stack, variables)
            case "NEGATIVE":
                return (self.true_branch, stack, variables) if operation_result < 0 else (self.false_branch, stack, variables)
            case _:
                assert False

    def __str__(self):

        return str(self.data)


def handle_output(output, variables):

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
