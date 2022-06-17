#!/usr/bin/env python3

commands = [
    ("dup", " [n]", "Duplicate the top of the stack n times (default n=1)"),
    ("swap", "", "Swap the top two items"),
    ("pick", " n", "Place a copy of the n-th item on the top"),
    ("help", "", "Print this help"),
    ("drop", "", "Drop the top element"),
    ("clear", "", "Drop all elements"),
    ("get_var", "", "Get the value of a variable; the identifier is the top element"),
    ("set_var", "", "Set the value of a variable; the identifier is the top element, the value is the 2nd element",),
    ("[todo]hxd", "", None),
    ("debug_on", "", "Enable debug-mode (only available in development-mode)"),
    ("debug_off", "", "Disable debug-mode (only available in development-mode)"),
    ("vars", "", "Print all the variables (only available in debug-mode)"),
    ("add", "", "Add the top two elements"),
    ("sub", "", "Subtract the top two elements"),
    ("div", "", "Divide the top two elements"),
    ("mul", "", "Multiply the top two elements"),
    ("and", "", "Bitwise-And of the top two elements"),
    ("or", "", "Bitwise-Or of the top two elements"),
    ("xor", "", "Bitwise-Xor of the top two elements"),
    ("quit", " (or <EOF>)", "Quit"),
    ("random", "", "Push a random integer"),
    ("time", "", "Push the Unix time, as an integer"),
    ("time_to_str", "", "Convert the Unix time on top of the stack to a string"),
    ("dec", "", "Print integers on the stack in decimal"),
    ("hex", "", "Print integers on the stack in hexadecimal"),
    ("oct", "", "Print integers on the stack in octal"),
    ("next_base", "", "Switch to the next base; that is, cycle among dec/hex/oct modes",),
    ("int_to_str", "", "Convert the integer on top of the stack to a string"),
    ("str_to_int", "", "Convert the string on top of the stack to an integer"),
    ("eval", "", "Execute the command corresponding to the integer on top of the stack",),
    ("ps_on", "", "Automatically print the stack content (default)"),
    ("ps_off", "", "Do not automatically print the stack content"),
    ("ps_status", "", "Return the status of automatic stack printing"),
    ("ints_to_id", "", "Convert four integers to an identifier"),
    ("ints_to_str", "", "Convert four integers to a string"),
    ("str_to_ints", "", "Convert a string into four integers"),
    ("id_to_ints", "", "Convert an identifier into four integers"),
    ("ver", "", "Print version/build information"),
]


def to_int(s):
    i = 0
    for c in s:
        i <<= 5
        i |= ord(c) & 31
    return i


commands = [(c[0], to_int(c[0]), c[1], c[2]) for c in commands]
commands.sort(key=lambda x: x[1])

print("static void cmd_help()\n{\n\tprintf(")
for c in sorted(commands, key=lambda c: c[0]):
    if c[3] is None:
        continue
    cmd = c[0].upper() + c[2]
    print(
        '\t YEL "'
        + (cmd + " ")
        + '" reset "'
        + "." * (20 - len(cmd))
        + " "
        + c[3]
        + '\\n"'
    )
print('\t"\\nCommands must begin with an uppercase letter, but are otherwise case-insensitive.\\n"')
print('\t"Identifiers start with a lowecase letter, and are case-sensitive.\\n"')
print('\t"Integer literals can be decimal, octal (prefix: \\"0\\") and hexadecimal (prefix: \\"0x\\").\\n"')
print('\t"String literals can be enclosed in either single or double quotes.\\n"')
print('\t"Arithmetic/bitwise operations can be abbreviated with +, -, and so on.\\n"')
print('"\\n"')
print("\t);\n}\n")

# print(commands)

all_paths = []


def visit(i, j, path):
    if j - i < 1:
        return "0"
    mid = (i + j) // 2
    left = visit(i, mid, path + "l")
    right = visit(mid + 1, j, path + "r")
    me = commands[mid]
    my_name = me[0].replace("[", "").replace("]", "")
    print(f"cmd_tree_node node_{my_name} = {{ {me[1]}, cmd_{my_name}, {left}, {right} }}; /* {path} */")
    all_paths.append(f'\t"{my_name}" : "{path}",')
    return f"&node_{my_name}"


print(f'cmd_tree_node *cmd_tree_root = {visit(0, len(commands), "")};')

with open("cmd_paths.py", "w") as f:
    print("cmd_paths = {", file=f)
    print("\n".join(all_paths), file=f)
    print("}\n", file=f)
