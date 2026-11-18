import sys
from enum import Enum

# All arms should go x direction, then z, then y out from active machine.
Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}


class StackInstructions(Enum):
    STACK_FINISHED = 0b000
    AXIS_ADJUSTED = 0b111
    CONTEXT_1 = 0b001
    CONTEXT_2 = 0b010
    CONTEXT_3 = 0b011
    CONTEXT_4 = 0b100
    CONTEXT_5 = 0b101


def push_to_stack(code, bits):
    assert bits in {3}
    global stack
    stack <<= bits
    if isinstance(code, Enum):
        code = code.value
    assert code & ((1 << bits) - 1) == code
    assert bits != 4
    stack ^= code


def pop_from_stack(bits):
    assert bits in {3}
    global stack
    code = stack & ((1 << bits) - 1)
    stack >>= bits
    return code


def determine_active_axis():
    global dx
    global dy
    global dz
    global active_axis
    assert active_axis != NO_AXIS
    if dy > 1:
        assert active_axis == Y_AXIS
        active_axis = Y_AXIS
        return
    if active_axis == Y_AXIS:
        # push_to_stack(Y_AXIS, 2)
        push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
    if dz > 1:
        active_axis = Z_AXIS
        return
    if active_axis > 1:
        # push_to_stack(Z_AXIS, 2)
        push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
    if dx > 1:
        active_axis = X_AXIS
        return
    assert active_axis == X_AXIS
    # push_to_stack(X_AXIS, 2)
    push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
    active_axis = NO_AXIS
    # print(f"Determined active axis {active_axis}")


def modify_active_axis(modification):
    global dx
    global dy
    global dz
    global active_axis
    if active_axis == Y_AXIS:
        dy += modification
    elif active_axis == Z_AXIS:
        dz += modification
    elif active_axis == X_AXIS:
        dx += modification
    else:
        print("Tried to modify no axis ")
        assert False


def fetch_from_store(cargo):
    global active_axis
    global negative_z
    if active_axis != Y_AXIS and cargo == "p":
        cargo = "sp"
    sign = ""
    if active_axis == Z_AXIS:
        sign = "-" if negative_z else "+"
    print(f"install {_name_map[active_axis]}{cargo}{sign}")


def return_to_store(cargo):
    global active_axis
    if active_axis != Y_AXIS and cargo == "p":
        cargo = "sp"
    sign = ""
    if active_axis == Z_AXIS:
        sign = "-" if negative_z else "+"
    print(f"remove {_name_map[active_axis]}{cargo}{sign}")


def recursively_install_1():
    global dx
    global dy
    global dz
    global negative_z
    global active_axis
    global just_removed

    determine_active_axis()
    if active_axis == NO_AXIS:
        if dy == 1:
            print("toggle y")
        if dz == negative_z:
            print("toggle z")
        if dx == 1:
            print("toggle x")
        just_removed = 0
    else:
        push_to_stack(StackInstructions.CONTEXT_1.value, 3)
        modify_active_axis(-1)
        recursively_install_1()


def recursively_install_2():
    # Context 2 for install
    fetch_from_store("p")
    push_to_stack(StackInstructions.CONTEXT_2.value, 3)
    modify_active_axis(-1)
    recursively_install_1()


def recursively_install_3():
    # Context 3 for install
    push_to_stack(StackInstructions.CONTEXT_5.value, 3)
    determine_active_axis()
    global active_axis
    if active_axis == NO_AXIS:
        print(f"pulse {dx}")
        assert pop_from_stack(3) == StackInstructions.AXIS_ADJUSTED.value
        active_axis += 1
        assert active_axis != NO_AXIS
        recursively_remove_1()  # can maybe be a goto into ri5
    else:
        fetch_from_store("o")
        push_to_stack(StackInstructions.CONTEXT_3.value, 3)
        modify_active_axis(-1)
        recursively_install_1()


def recursively_install_4():
    # Context 4 for remove
    push_to_stack(StackInstructions.CONTEXT_4.value, 3)
    recursively_remove_1()


def recursively_install_5():
    # Context 5 for remove
    return_to_store("o")
    modify_active_axis(1)
    # push_to_stack(StackInstructions.CONTEXT_5, 4)
    recursively_remove_1()


def recursively_install_6():
    global just_removed
    return_to_store("p")
    just_removed = 0
    modify_active_axis(2)


def recursively_remove_1():
    global dx
    global dy
    global dz
    global negative_z
    global active_axis
    global just_removed
    determine_active_axis()
    if active_axis == NO_AXIS:
        if dx == 1:
            print("toggle x")
        if dz == negative_z:
            print("toggle z")
        if dy == 1:
            print("toggle y")
        just_removed = 1
    else:
        fetch_from_store("sp")
        push_to_stack(StackInstructions.CONTEXT_5.value, 3)
        modify_active_axis(-2)
        recursively_install_1()


def recursively_remove_2():
    global just_removed
    global active_axis
    push_to_stack(StackInstructions.CONTEXT_2.value, 3)
    determine_active_axis()
    if active_axis == NO_AXIS:
        print(f"pulse {dx}")
        assert pop_from_stack(3) == StackInstructions.AXIS_ADJUSTED.value
        active_axis += 1
        assert active_axis == X_AXIS  # we are inside the 2x2x2 cube, so whatever piston we just pulsed is X-facing
        recursively_remove_1()
    else:
        fetch_from_store("o")
        push_to_stack(StackInstructions.CONTEXT_4.value, 3)
        modify_active_axis(-1)
        recursively_install_1()


def recursively_remove_3():
    push_to_stack(StackInstructions.CONTEXT_3.value, 3)
    recursively_remove_1()


def recursively_remove_4():
    return_to_store("o")
    modify_active_axis(1)
    recursively_remove_1()


def recursively_remove_5():
    return_to_store("sp")
    push_to_stack(StackInstructions.CONTEXT_1.value, 3)
    modify_active_axis(1)
    recursively_remove_1()


def recursively_remove_6():
    global just_removed
    just_removed = 1
    modify_active_axis(1)


def process_stack_instruction():
    # print(bin(stack))
    global just_removed
    global active_axis
    global dx
    global dy
    global dz
    global negative_z

    instruction = pop_from_stack(3)
    if instruction == StackInstructions.AXIS_ADJUSTED.value:
        active_axis += 1
        return

    # STACK_FINISHED = 0b000
    # AXIS_ADJUSTED = 0b111
    # CONTEXT_1 = 0b001
    # CONTEXT_2 = 0b010
    # CONTEXT_3 = 0b011
    # CONTEXT_4 = 0b100
    # CONTEXT_5 = 0b101
    match instruction, just_removed:
        case 0b101, 0:
            recursively_remove_2()
        case 0b100, 0:
            recursively_remove_3()
        case 0b011, 1:
            recursively_remove_4()
        case 0b010, 1:
            recursively_remove_5()
        case 0b001, 1:
            recursively_remove_6()

        case 0b001, 0:
            recursively_install_2()
        case 0b010, 0:
            recursively_install_3()
        case 0b011, 0:
            recursively_install_4()
        case 0b100, 1:
            recursively_install_5()
        case 0b101, 1:
            recursively_install_6()

        case _, _:
            print(f"DEFAULT {instruction} {just_removed}")
    return


# y_height = 21  # 32
# y_buffer = 1
# n = 164
# m = 134
y_height = 2
y_buffer = 1
n = 3
m = 5
stack = 0
just_removed = 0
active_axis = Y_AXIS
# first_loop = 1
dx = 0
dy = 0
dz = 0
negative_z = 0


def main_loop():
    global first_loop
    global dx
    global dy
    global dz
    global negative_z
    y1 = 3 * y_height + y_height + y_buffer if first_loop == 1 else y_height
    y2 = -1 if first_loop == 1 else y_height + y_buffer - 3
    while y1 != (y_height + y_buffer if first_loop == 1 else 0):
        y1 -= 3 if first_loop == 1 else 1
        y2 += 1 if first_loop == 1 else 3
        z1 = 0
        z2 = n
        while z2 != 0:
            z1 += 1
            x = 2
            while x != m + 2:
                dx = x
                dy = y2
                dz = z1
                negative_z = 1

                recursively_remove_1()
                while stack & 0b111 != 0:
                    process_stack_instruction()

                dx = x
                dy = y1
                dz = z2
                negative_z = 0
                recursively_install_1()
                while stack & 0b111 != 0:
                    process_stack_instruction()
                x += 1
            z2 -= 1


normal_out = sys.stdout
with open("test_mixed_widths_a.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    main_loop()
    first_loop = 0
    main_loop()

sys.stdout = normal_out

# print(dx, dy, dz, x, y, z, bin(stack), negative_z, just_installed)
