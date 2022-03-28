import sys
import re
import xml.etree.ElementTree as ET

instructions_list = []
labels_list = []
lf_stack = []
tf_defined = 0
lf_defined = 0
value_stack = []
type_stack = []
call_stack = []


class argument:
    def __init__(self, arg_order: int, arg_type, arg_value):
        self.type = arg_type
        self.order: int = arg_order
        self.value = arg_value

    def get_frame(self):
        return re.sub(r"@.+", "", self.value)

    def get_value(self):
        if self.type == "var":
            return re.sub(r".+@", "", self.value)
        else:
            return self.value

    def get_type(self):
        return self.type


class instruction:
    def __init__(self, opcode, order, args_num):
        self.opcode = opcode
        self.args_num = args_num
        self.order = order
        self.args = []

    def add_argument(self, arg_type, arg_number, value):
        self.args.append(argument(arg_type, arg_number, value))

    def get_argument(self, order):
        for arg in self.args:
            if arg.order == order:
                return arg

    def get_opcode(self):
        return self.opcode


class variable:
    def __init__(self, var_name, var_type, var_value):
        self.name = var_name
        self.type = var_type
        self.value = var_value

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type

    def get_value(self):
        return self.value

    def edit_value(self, value, value_type):
        if value_type == "int":
            try:
                value = int(value)
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        elif value_type == "bool":
            if value != "false" and value != "true":
                print_error(WRONG_OPERAND_TYPE_ERROR)
        self.value = value
        self.type = value_type


class frame:
    def __init__(self):
        self.variables = []

    def add_var(self, var_name, var_type, var_value):
        self.variables.append(variable(var_name, var_type, var_value))

    def search_var(self, name):
        for var in self.variables:
            if var.get_name() == name:
                return var
        else:
            return None

    def edit_variables(self, array):
        self.variables = array


WRONG_ARGUMENTS_ERROR = 10
INPUT_FILE_OPENING_ERROR = 11
WRONG_XML_FORMAT_ERROR = 31
UNEXPECTED_XML_STRUCTURE_ERROR = 32
UNDEFINED_LABEL_OR_REDEFINITION_ERROR = 52
WRONG_OPERAND_TYPE_ERROR = 53
UNDEFINED_VARIABLE_ERROR = 54
UNDEFINED_FRAME_ERROR = 55
MISSING_VALUE_ERROR = 56
WRONG_OPERAND_VALUE_ERROR = 57


# funkce na vypis chybovych hlasek a ukonceni programu
def print_error(errorcode):
    if errorcode == WRONG_ARGUMENTS_ERROR:
        sys.stderr.write("Unknown argument or forbidden arguments combination!\n")
    elif errorcode == INPUT_FILE_OPENING_ERROR:
        sys.stderr.write("Couldn't open input file!\n")
    elif errorcode == WRONG_XML_FORMAT_ERROR:
        sys.stderr.write("Wrong XML format in src file!\n")
    elif errorcode == UNEXPECTED_XML_STRUCTURE_ERROR:
        sys.stderr.write("Unexpected XML structure in src file!\n")
    elif errorcode == UNDEFINED_LABEL_OR_REDEFINITION_ERROR:
        sys.stderr.write("Variable redefinition or undefined label!\n")
    elif errorcode == WRONG_OPERAND_TYPE_ERROR:
        sys.stderr.write("Wrong operand type!\n")
    elif errorcode == UNDEFINED_VARIABLE_ERROR:
        sys.stderr.write("Undefined variable!\n")
    elif errorcode == UNDEFINED_FRAME_ERROR:
        sys.stderr.write("Undefined frame!\n")
    elif errorcode == MISSING_VALUE_ERROR:
        sys.stderr.write("Missing value!")
    elif errorcode == WRONG_OPERAND_VALUE_ERROR:
        sys.stderr.write("Wrong operand type!")
    exit(errorcode)


# funkce na zkontrolovani spravnosti a jedinecnosti argumentu programu
# zaroven pri kontrole argumentu ziska cesty k zadanym souborum
def check_args_and_get_file_paths():
    source_path = input_path = ""
    source_arg = input_arg = 0
    for arg in sys.argv[1:]:
        if re.match("--input=.+", arg) and input_arg == 0:
            input_arg = 1
            input_path = arg[arg.find("=") + 1:]
        elif re.match("--source=.+", arg) and source_arg == 0:
            source_path = arg[arg.find("=") + 1:]
            source_arg = 1
        # napoveda muze byt vypsana pouze pokud je to jediny argument
        elif re.match("--help", arg) and len(sys.argv) == 0:
            continue
        else:
            print_error(WRONG_ARGUMENTS_ERROR)

    if source_arg == 0 and input_arg == 0:
        print_error(WRONG_ARGUMENTS_ERROR)
    elif source_arg == 0:
        source_path = sys.stdin
    elif input_arg == 0:
        input_path = sys.stdin
    return source_path, input_path


# funkce slouzici pro vypis napovedy
def print_help():
    print("Usage: python3 interpret.py [options]\n"
          "options:\n"
          "\t--help\n"
          "\t--source=file\n"
          "\t--input=file\n"
          "error return codes:\n"
          "\t31 - incorrect XML formatting\n"
          "\t32 - unexpected XML structure\n")


# funkce slouzici k nacteni XML
def load_xml(src_file):
    try:
        tmp_tree = ET.parse(src_file)
    except ET.ParseError:
        print_error(WRONG_XML_FORMAT_ERROR)
    else:
        tmp_root = tmp_tree.getroot()
        return tmp_tree, tmp_root


# funkce slouzici ke kontrole, zda XML ma spravnou strukturu
def check_xml(tree_root):
    if tree_root.tag != 'program':
        print_error(UNEXPECTED_XML_STRUCTURE_ERROR)


def search_instruction(order):
    if order <= 0:
        print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
    for instr in instructions_list:
        if instr.order == order:
            return instr
    else:
        return None


# funkce slouzici na ulozeni promenne do prislusneho frame-u
def save_variable(gf, tf, lf, var_frame, name):
    if var_frame == "GF":
        gf.add_var(name, "", "")
    elif var_frame == "TF":
        tf.add_var(name, "", "")
    elif var_frame == "LF":
        lf.add_var(name, "", "")


# funkce slouzici na vyhledani promenne v seznamu, pokud neexistuje, vraci None
def search_variable(gf, tf, lf, var_frame, name):
    if var_frame == "GF":
        return gf.search_var(name)
    elif var_frame == "TF":
        return tf.search_var(name)
    elif var_frame == "LF":
        return lf.search_var(name)


# funkce slouzici na ulozeni instrukci do seznamu
def save_instructions(tree_root):
    for instr in tree_root:
        # overeni, zda instrukce ma opcode i order a zda ma spravny tag
        if instr.get("opcode") is None or instr.get("order") is None or instr.tag != "instruction":
            print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
        # overeni, zda order je cislo
        try:
            int(instr.get("order"))
        except ValueError:
            print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
        # overeni, zda jiz neexistuje instrukce s danym poradim
        if search_instruction(int(instr.get("order"))) is not None:
            print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
        new_instruction = instruction(instr.get("opcode"), int(instr.get("order")), 3)
        instructions_list.append(new_instruction)
        # pokud se jedna o label, prida instrukci i na seznam labelu
        if new_instruction.opcode == "LABEL":
            labels_list.append(new_instruction)
        for arg in instr:
            # overeni, zda se jedna o validni zapis argumentu
            if re.match(r"arg\d", arg.tag):
                new_instruction.add_argument(int(re.sub(r"\D", "", arg.tag)), arg.get("type"), arg.text)
            else:
                print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
    instructions_list.sort(key=lambda x: x.order)


def execute_move(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    arg2 = instr.get_argument(2)
    if arg1.get_type() == "var":
        var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
        if var is not None:
            if arg2.get_type() != "var":
                var.edit_value(arg2.get_value(), arg2.get_type())
            else:
                var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
                if var2 is not None:
                    var.edit_value(var2.get_value(), var2.get_type())
                else:
                    print_error(UNDEFINED_VARIABLE_ERROR)
        else:
            print_error(UNDEFINED_VARIABLE_ERROR)
    else:
        print_error(WRONG_OPERAND_TYPE_ERROR)


def execute_defvar(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() == "var":
        if arg.get_frame() == "GF":
            gf.add_var(arg.get_value(), "", "")
        elif arg.get_frame() == "TF":
            tf.add_var(arg.get_value(), "", "")
        elif arg.get_frame() == "LF":
            lf.add_var(arg.get_value(), "", "")


def execute_write(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() != "var":
        if arg.get_type() == "nil":
            print("", end='')
        else:
            if arg.get_type() == "string":
                if re.search(r'\\([0-9]{3})', arg.get_value()):
                    print(re.sub(r'\\([0-9]{3})', lambda x: chr(int(x[1])), arg.get_value()), end='')
                else:
                    print(var.get_value(), end='')
            else:
                print(arg.get_value(), end='')
    else:
        var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
        if var is not None:
            if var.get_type() == "nil":
                print("", end='')
            else:
                if var.get_type() == "string":
                    if re.search(r'\\([0-9]{3})', var.get_value()):
                        print(re.sub(r'\\([0-9]{3})', lambda x: chr(int(x[1])), var.get_value()), end='')
                    else:
                        print(var.get_value(), end='')
                else:
                    print(var.get_value(), end='')
        else:
            print_error(UNDEFINED_VARIABLE_ERROR)


def execute_pushs(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() != "var":
        value_stack.append(arg.get_value())
        type_stack.append(arg.get_type())
    else:
        var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
        if var is not None:
            value_stack.append(var.get_value())
            type_stack.append(var.get_type())
        else:
            print_error(UNDEFINED_VARIABLE_ERROR)


def execute_pops(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    else:
        var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
        if var is not None:
            var.edit_value(value_stack.pop(), type_stack.pop())


def execute_int2char(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        var.edit_value(chr(arg2.get_value), "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        var.edit_value(chr(var2.get_value()), "string")


def execute_add(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(arg2.get_value()) + int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(arg2.get_value()) + int(var2.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(var2.get_value()) + int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(var2.get_value()) + int(var3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)


def execute_sub(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(arg2.get_value()) - int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(arg2.get_value()) - int(var2.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(var2.get_value()) - int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(var2.get_value()) - int(var3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)


def execute_mul(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(arg2.get_value()) * int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(arg2.get_value()) * int(var2.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(var2.get_value()) * int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(var2.get_value()) * int(var3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)


def execute_idiv(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(arg2.get_value()) // int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
            except ZeroDivisionError:
                print_error(WRONG_OPERAND_VALUE_ERROR)
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(arg2.get_value()) // int(var2.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
            except ZeroDivisionError:
                print_error(WRONG_OPERAND_VALUE_ERROR)
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            try:
                var.edit_value(int(var2.get_value()) // int(arg3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
            except ZeroDivisionError:
                print_error(WRONG_OPERAND_VALUE_ERROR)
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            try:
                var.edit_value(int(var2.get_value()) // int(var3.get_value()), "int")
            except ValueError:
                print_error(WRONG_OPERAND_TYPE_ERROR)
            except ZeroDivisionError:
                print_error(WRONG_OPERAND_VALUE_ERROR)


def execute_gt(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() > arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != arg2.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() > var2.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if var2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() > arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != var3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() > var3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_lt(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() < arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != arg2.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() < var2.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if var2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() < arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != var3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() < var3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_eq(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != arg2.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == var2.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if var2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() == arg3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != var3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() == var3.get_value():
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_read(file, gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "type":
        print_error(WRONG_ARGUMENTS_ERROR)
    line = file.readline()
    line = line.rstrip()
    if not line:
        var.edit_value("nil", "nil")
    else:
        if arg2.get_value() == "bool":
            if line == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var.edit_value(line, arg2.get_value())


def execute_and(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == "true" and arg3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == "true" and var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "bool":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg3.get_value() == "true" and var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() == "true" and var3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_or(gf, tf, lf, instr):
    def execute_and(gf, tf, lf, instr):
        arg1 = instr.get_argument(1)
        if arg1.get_type() != "var":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
        if var is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        arg2 = instr.get_argument(2)
        if arg2.get_type() != "var":
            arg3 = instr.get_argument(3)
            if arg3.get_type() != "var":
                if arg2.get_type() != "bool":
                    print_error(WRONG_OPERAND_TYPE_ERROR)
                if arg2.get_value() == "true" or arg3.get_value() == "true":
                    var.edit_value("true", "bool")
                else:
                    var.edit_value("false", "bool")
            else:
                var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
                if var2 is None:
                    print_error(UNDEFINED_VARIABLE_ERROR)
                if var2.get_type() != "bool":
                    print_error(WRONG_OPERAND_TYPE_ERROR)
                if arg2.get_value() == "true" or var2.get_value() == "true":
                    var.edit_value("true", "bool")
                else:
                    var.edit_value("false", "bool")
        else:
            var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            arg3 = instr.get_argument(3)
            if arg3.get_type() != "var":
                if arg3.get_type() != "bool":
                    print_error(WRONG_OPERAND_TYPE_ERROR)
                if arg3.get_value() == "true" or var2.get_value() == "true":
                    var.edit_value("true", "bool")
                else:
                    var.edit_value("false", "bool")
            else:
                var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
                if var3 is None:
                    print_error(UNDEFINED_VARIABLE_ERROR)
                if var3.get_type() != "bool":
                    print_error(WRONG_OPERAND_TYPE_ERROR)
                if var2.get_value() == "true" or var3.get_value() == "true":
                    var.edit_value("true", "bool")
                else:
                    var.edit_value("false", "bool")


def execute_not(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type != "bool":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if arg2.get_value == "true":
            var.edit_value("false", "bool")
        else:
            var.edit_value("true", "bool")


def execute_strlen(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        var.edit_value(len(arg2.get_value()), "int")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        var.edit_value(len(var2.get_value()), "int")


def execute_concat(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(arg2.get_value() + arg3.get_value(), "string")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(arg2.get_value() + var2.get_value(), "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var2.get_value() + arg3.get_value(), "string")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var2.get_value() + var3.get_value(), "string")


def execute_type(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        var.edit_value(arg2.get_type(), "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        var.edit_value(var2.get_type(), "string")


def execute_exit(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        if arg1.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if int(arg1.get_value()) > 49:
            print_error(WRONG_OPERAND_VALUE_ERROR)
        exit(int(arg1.get_value()))
    else:
        var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
        if var is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if int(var.get_value()) > 49:
            print_error(WRONG_OPERAND_VALUE_ERROR)
        exit(int(var.get_value()))


def execute_stri2int(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(ord(arg2.get_value()[int(arg3.get_value())]), "int")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(ord(arg2.get_value()[int(var2.get_value())]), "int")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(ord(var2.get_value()[int(arg3.get_value())]), "int")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(ord(var2.get_value()[int(var3.get_value())]), "int")


def execute_getchar(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(arg2.get_value()[int(arg3.get_value())], "string")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(arg2.get_value()[int(var2.get_value())], "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var2.get_value()[int(arg3.get_value())], "string")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var2.get_value()[int(var3.get_value())], "string")


def execute_setchar(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    if var.get_type() != "string":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var.get_value()[:arg2.get_value()] + arg3.get_value() + var.get_value()[arg2.get_value()+1:], "string")
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var2.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var.get_value()[:arg2.get_value()] + var2.get_value() + var.get_value()[arg2.get_value()+1:], "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var2.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var.get_value()[:var2.get_value()] + arg3.get_value() + var.get_value()[var2.get_value()+1:], "string")
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            if var3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var.get_value()[:var2.get_value()] + var3.get_value() + var.get_value()[var2.get_value()+1:], "string")


def execute_instructions(input_path):
    file = open(input_path)
    gf = lf = tf = frame()
    i = 0
    while i < len(instructions_list):
        instr = instructions_list[i]
        # prevedeno na uppercase z duvodu case insensitivity
        instr_opcode = instr.get_opcode().upper()
        if instr_opcode == "MOVE":
            execute_move(gf, tf, lf, instr)
        elif instr_opcode == "CREATEFRAME":
            tf_defined = 1
            tf.edit_variables([])
        elif instr_opcode == "PUSHFRAME":
            lf_stack.append(tf)
            tf_defined = 0
        elif instr_opcode == "POPFRAME":
            tf_defined = 1
            tf = lf_stack.pop()
        elif instr_opcode == "DEFVAR":
            execute_defvar(gf, tf, lf, instr)
        # elif instr_opcode == "CALL":
        #     i = execute_call(gf, tf, lf, instr())
        # elif instr_opcode == "RETURN":
        #     i = execute_return(gf, tf, lf, instr())
        elif instr_opcode == "PUSHS":
            execute_pushs(gf, tf, lf, instr)
        elif instr_opcode == "POPS":
            execute_pops(gf, tf, lf, instr)
        elif instr_opcode == "ADD":
            execute_add(gf, tf, lf, instr)
        elif instr_opcode == "SUB":
            execute_sub(gf, tf, lf, instr)
        elif instr_opcode == "MUL":
            execute_mul(gf, tf, lf, instr)
        elif instr_opcode == "IDIV":
            execute_idiv(gf, tf, lf, instr)
        elif instr_opcode == "LT":
            execute_lt(gf, tf, lf, instr)
        elif instr_opcode == "GT":
            execute_gt(gf, tf, lf, instr)
        elif instr_opcode == "EQ":
            execute_eq(gf, tf, lf, instr)
        elif instr_opcode == "AND":
            execute_and(gf, tf, lf, instr)
        elif instr_opcode == "OR":
            execute_or(gf, tf, lf, instr)
        elif instr_opcode == "NOT":
            execute_not(gf, tf, lf, instr)
        elif instr_opcode == "INT2CHAR":
            execute_int2char(gf, tf, lf, instr)
        elif instr_opcode == "STRI2INT":
            execute_stri2int(gf, tf, lf, instr)
        elif instr_opcode == "READ":
            execute_read(file, gf, tf, lf, instr)
        elif instr_opcode == "WRITE":
            execute_write(gf, tf, lf, instr)
        elif instr_opcode == "CONCAT":
            execute_concat(gf, tf, lf, instr)
        elif instr_opcode == "STRLEN":
            execute_strlen(gf, tf, lf, instr)
        elif instr_opcode == "GETCHAR":
            execute_getchar(gf, tf, lf, instr)
        elif instr_opcode == "SETCHAR":
            execute_setchar(gf, tf, lf, instr)
        elif instr_opcode == "TYPE":
            execute_type(gf, tf, lf, instr)
        # elif instr_opcode == "LABEL":
        #     execute_label(gf, tf, lf, instr)
        # elif instr_opcode == "JUMP":
        #     execute_jump(gf, tf, lf, instr)
        # elif instr_opcode == "JUMPIFEQ":
        #     i = execute_jumpifeq(gf, tf, lf, instr)
        # elif instr_opcode == "JUMPIFNEQ":
        #     i = execute_jumpifneq(gf, tf, lf, instr)
        elif instr_opcode == "EXIT":
            execute_exit(gf, tf, lf, instr)
        # elif instr_opcode == "DPRINT":
        #     execute_dprint(gf, tf, lf, instr)
        # elif instr_opcode == "BREAK":
        #     execute_break(gf, tf, lf, instr)
        else:
            print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
        i += 1


if __name__ == '__main__':
    source_file, input_file = check_args_and_get_file_paths()
    if '--help' in sys.argv:
        print_help()

    tree, root = load_xml(source_file)
    check_xml(root)
    save_instructions(root)
    execute_instructions(input_file)
