import sys

y_height = 21
y_buffer = 1
x_machine_width = 134
z_machine_width = 164
z_jump_size = z_machine_width


# All arms should go x direction, then z, then y out from active machine.
def move(v1, v2):
    dx1, dy1, dz1 = v1
    dx2, dy2, dz2 = v2
    remove(dx1, 1 - dz1, dy1, "special", negative_z=True)
    install(dx2, dz2, dy2, "special", negative_z=False)


def install(dx, dz, dy, cargo, negative_z):
    if dy > 1:
        install(dx, dz, dy - 1, cargo, negative_z)
        install(dx, dz, dy - 2, "yp", negative_z)
        pulse(dx, dz, dy - 2, negative_z)
        remove(dx, dz, dy - 2, "yp", negative_z)
    elif dz > 1:
        z_direction = "-" if negative_z else "+"
        install(dx, dz - 1, dy, cargo, negative_z)
        install(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
        pulse(dx, dz - 2, dy, negative_z)
        remove(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
    elif dx > 1:
        install(dx - 1, dz, dy, cargo, negative_z)
        install(dx - 2, dz, dy, f"xsp", negative_z)
        pulse(dx - 2, dz, dy, negative_z)
        remove(dx - 2, dz, dy, f"xsp", negative_z)
    else:
        if cargo != "special":
            print(f"install {cargo}")
        if dy == 1:
            print("toggle y")
        if (dz if negative_z else 1 - dz) == 1:
            print("toggle z")
        if dx == 1:
            print("toggle x")


def remove(dx, dz, dy, cargo, negative_z):
    if dy > 1:
        install(dx, dz, dy - 2, "ysp", negative_z)
        pulse(dx, dz, dy - 2, negative_z)
        remove(dx, dz, dy - 2, "ysp", negative_z)
        remove(dx, dz, dy - 1, cargo, negative_z)
    elif dz > 1:
        z_direction = "-" if negative_z else "+"
        install(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
        pulse(dx, dz - 2, dy, negative_z)
        remove(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
        remove(dx, dz - 1, dy, cargo, negative_z)
    elif dx > 1:
        install(dx - 2, dz, dy, "xsp", negative_z)
        pulse(dx - 2, dz, dy, negative_z)
        remove(dx - 2, dz, dy, "xsp", negative_z)
        remove(dx - 1, dz, dy, cargo, negative_z)
    else:
        if dx == 1:
            print("toggle x")
        if (dz if negative_z else 1 - dz) == 1:
            print("toggle z")
        if dy == 1:
            print("toggle y")
        if cargo != "special":
            print(f"remove {cargo}")


def pulse(dx, dz, dy, negative_z):
    if dy > 1:
        install(dx, dz, dy - 1, "yo", negative_z)
        remove(dx, dz, dy - 1, "yo", negative_z)
    elif dz > 1:
        z_direction = "-" if negative_z else "+"
        install(dx, dz - 1, dy, f"zo{z_direction}", negative_z)
        remove(dx, dz - 1, dy, f"zo{z_direction}", negative_z)
    elif dx > 1:
        install(dx - 1, dz, dy, "xo", negative_z)
        remove(dx - 1, dz, dy, "xo", negative_z)
    else:
        print(f"pulse {dx}")


with open("test_mixed_widths.txt", "w", encoding="utf-8") as fl:
    sys.stdout = fl
    for y in range(y_height):
        for z in range(0, -z_machine_width, -1):
            for x in range(2, x_machine_width + 2):
                move((x, y, z), (x, 3 * (y_height - y - 1) + y_height + y_buffer, z + z_jump_size))
    for y in range(y_height - 1, -1, -1):
        for z in range(0, -z_machine_width, -1):
            for x in range(2, x_machine_width + 2):
                move((x, 3 * (y_height - y - 1) + y_height + y_buffer, z), (x, y, z + z_jump_size))
