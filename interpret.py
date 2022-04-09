import sys
import re
import xml.etree.ElementTree as ET
import operator

instructions_list = []
labels_list = []
lf_stack = []
value_stack = []
type_stack = []
call_stack = []
tf_defined = 0


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
        elif self.type == "int":
            return int(self.value)
        else:
            return self.value

    def get_type(self):
        return self.type

    def edit_value(self, value):
        self.value = value


# trida slouzici na ukladani a praci s jednotlivymi instrukcemi
class instruction:
    def __init__(self, opcode, order, args_num):
        self.opcode = opcode
        self.args_num = args_num
        self.order = order
        self.args = []

    def add_argument(self, arg_type, arg_number, value):
        self.args.append(argument(arg_type, arg_number, value))

    # vrati argument se zadanym poradim
    def get_argument(self, order):
        for arg in self.args:
            if arg.order == order:
                return arg

    def get_opcode(self):
        return self.opcode

    def get_order(self):
        return self.order


# trida slouzici pro ukladad
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

    # upravi a zkontroluje hodnotu ulozenou v promenne
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


# trida slouzici na ukladani do ramcu a naslednou praci s nimi
class frame:
    def __init__(self):
        self.variables = []

# zkontroluje a ulozi promennou do ramce
    def add_var(self, var_name, var_type, var_value):
        # zkontroluje, zda promenna jiz v ramci neexistuje
        if self.search_var(var_name) is not None:
            print_error(UNDEFINED_LABEL_OR_REDEFINITION_ERROR)
        self.variables.append(variable(var_name, var_type, var_value))

    # vyhleda promennou v ramci, pokud neexistuje vraci None
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
WRONG_STRING_WORKING_ERROR = 58


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
        sys.stderr.write("Missing value!\n")
    elif errorcode == WRONG_OPERAND_VALUE_ERROR:
        sys.stderr.write("Wrong operand type!\n")
    elif errorcode == WRONG_STRING_WORKING_ERROR:
        sys.stderr.write("Wrong working with string!\n")
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
        elif re.match("--help", arg) and len(sys.argv) == 2:
            print_help()
        else:
            print_error(WRONG_ARGUMENTS_ERROR)
    # musi byt zadan alespon jeden argument
    if source_arg == 0 and input_arg == 0:
        print_error(WRONG_ARGUMENTS_ERROR)
    # pokud neni zadan jeden argument, bere stdin
    elif source_arg == 0:
        source_path = sys.stdin
    elif input_arg == 0:
        input_path = sys.stdin
    return source_path, input_path


# funkce slouzici pro vypis napovedy
def print_help():
    print("Použití: python3 interpret.py [parametry]\n"
          "parametry:\n"
          "\t--help\n"
          "\t--source=file\n"
          "\t--input=file\n"
          "je nutno zadat alespoň jeden z parametrů --source=file "
          "a --input=file, druhý bude načten ze standardního vstupu\n\n"
          "error return codes:\n"
          "\t31 - incorrect XML formatting\n"
          "\t32 - unexpected XML structure")
    exit(0)


# funkce slouzici k nacteni XML
def load_xml(src_file):
    try:
        tmp_tree = ET.parse(src_file)
    except ET.ParseError:
        print_error(WRONG_XML_FORMAT_ERROR)
    except FileNotFoundError:
        print_error(INPUT_FILE_OPENING_ERROR)
    else:
        tmp_root = tmp_tree.getroot()
        return tmp_tree, tmp_root


# funkce slouzici ke kontrole, zda XML ma spravnou strukturu
def check_xml(tree_root):
    if tree_root.tag != 'program':
        print_error(UNEXPECTED_XML_STRUCTURE_ERROR)

# funkce slouzici k vyhledani instrukce
def search_instruction(order):
    if order <= 0:
        print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
    for instr in instructions_list:
        if instr.order == order:
            return instr
    else:
        return None


# funkce vraci index daneho labelu v seznamu instrukci
def get_label_index(name):
    i = 0
    while i < len(instructions_list):
        instr = instructions_list[i]
        if instr.get_opcode().upper() == "LABEL" and instr.get_argument(1).get_value() == name:
            return i
        i += 1
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
        if tf_defined == 0:
            print_error(UNDEFINED_FRAME_ERROR)
        return tf.search_var(name)
    elif var_frame == "LF":
        if not lf_stack:
            print_error(UNDEFINED_FRAME_ERROR)
        return lf.search_var(name)


# funkce, ktera vrati index labelu a zaroven zkontroluje spravnost
def get_index_check_label(instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "label":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    index = get_label_index(instr.get_argument(1).get_value())
    if index is None:
        print_error(UNDEFINED_LABEL_OR_REDEFINITION_ERROR)
    return index


# funkce slouzici na kontrolu existence promenne a pripadne jejiho spravneho typu
def get_and_check_var(instr, arg_num, gf, tf, lf, check_type=0, checking_type=None):
    arg = instr.get_argument(arg_num)
    if arg.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
    if var is None:
        print_error(UNDEFINED_VARIABLE_ERROR)
    if check_type:
        if var.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        if var.get_type() != checking_type:
            print_error(WRONG_OPERAND_TYPE_ERROR)
    return var

# pomocna funkce pro stri2int, kontroluje spravnost stringu
# a pozice a do var ulozi ord
def get_ord(var, string, position):
    if position.get_type() != "int":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    if position.get_value() < 0:
        print_error(WRONG_STRING_WORKING_ERROR)
    try:
        var.edit_value(ord(string.get_value()[int(position.get_value())]), "int")
    except IndexError:
        print_error(WRONG_STRING_WORKING_ERROR)


# pomocna funkce pro aritmeticke operace, zkontroluje
# spravnost posledniho argumentu a vykona pozadovanou operaci
def check_last_arg_and_get_result(op, var, first_num, arg3, instr, gf, tf, lf):
    if arg3.get_type() != "var":
        if arg3.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        try:
            var.edit_value(op(first_num.get_value(), arg3.get_value()), "int")
        except ZeroDivisionError:
            print_error(WRONG_OPERAND_VALUE_ERROR)
    else:
        var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="int")
        try:
            var.edit_value(op(first_num.get_value(), var2.get_value()), "int")
        except ZeroDivisionError:
            print_error(WRONG_OPERAND_VALUE_ERROR)


# spolecna funkce pro vsechny aritmeticke operace,
# zkontroluje spravnost vsech argumentu a pote zavola funkci
# "check_last_arg_and_get_result", ktera vrati vysledek
def execute_arithmetic_operation(op, instr, gf, tf, lf):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        check_last_arg_and_get_result(op, var, arg2, arg3, instr, gf, tf, lf)
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="int")
        arg3 = instr.get_argument(3)
        check_last_arg_and_get_result(op, var, var2, arg3, instr, gf, tf, lf)


def check_comparing_values(op, first_value, second_value):
    if op == operator.eq:
        if first_value.get_type() != second_value.get_type() and \
                first_value.get_type() != "nil" and second_value.get_type() != "nil":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        else:
            if first_value.get_type() != second_value.get_type() or\
                    first_value.get_type() == "nil" or second_value.get_type() == "nil":
                print_error(WRONG_OPERAND_TYPE_ERROR)


def check_values_and_compare(var, first_value, arg3, op, instr, gf, tf, lf):
    if arg3.get_type() != "var":
        check_comparing_values(op, first_value, arg3)
        if op(first_value.get_value(), arg3.get_value()):
            var.edit_value("true", "bool")
        else:
            var.edit_value("false", "bool")
    else:
        var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
        if var3 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var3.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        check_comparing_values(op, first_value, var3)
        if op(first_value.get_value(), var3.get_value()):
            var.edit_value("true", "bool")
        else:
            var.edit_value("false", "bool")


def execute_comparison_operation(op, instr, gf, tf, lf):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        check_values_and_compare(var, arg2, arg3, op, instr, gf, tf, lf)
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        # jedna se o nedefinovanou promennou
        if var2.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        arg3 = instr.get_argument(3)
        check_values_and_compare(var, var2, arg3, op, instr, gf, tf, lf)


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
        for arg in instr:
            if arg.text is None:
                arg.text = ""
            # overeni, zda se jedna o validni zapis argumentu
            if re.match(r"arg\d", arg.tag):
                new_instruction.add_argument(int(re.sub(r"\D", "", arg.tag)), arg.get("type"), arg.text)
            else:
                print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
            inserted_arg = new_instruction.get_argument(int(re.sub(r"\D", "", arg.tag)))
            if inserted_arg.get_type() == "string" and re.search(r'\\([0-9]{3})', inserted_arg.get_value()):
                inserted_arg.edit_value(re.sub(r'\\([0-9]{3})', lambda x: chr(int(x[1])), inserted_arg.get_value()))
        if instr.get("opcode") == "LABEL":
            if new_instruction.get_argument(1).get_value() in labels_list:
                print_error(UNDEFINED_LABEL_OR_REDEFINITION_ERROR)
            labels_list.append(new_instruction.get_argument(1).get_value())
    instructions_list.sort(key=lambda x: x.order)


# funkce, ktera provede instrukci MOVE
def execute_move(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() == "var":
        var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
        if var is not None:
            arg2 = instr.get_argument(2)
            if arg2.get_type() != "var":
                var.edit_value(arg2.get_value(), arg2.get_type())
            else:
                var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
                if var2 is None:
                    print_error(UNDEFINED_VARIABLE_ERROR)
                # jedna se o nedefinovanou promennou
                if var2.get_type() == "":
                    print_error(MISSING_VALUE_ERROR)
                var.edit_value(var2.get_value(), var2.get_type())
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
            if tf_defined == 0:
                print_error(UNDEFINED_FRAME_ERROR)
            tf.add_var(arg.get_value(), "", "")
        elif arg.get_frame() == "LF":
            if not lf_stack:
                print_error(UNDEFINED_FRAME_ERROR)
            lf.add_var(arg.get_value(), "", "")


def execute_write(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() != "var":
        if arg.get_type() == "nil":
            print("", end='')
        else:
            print(arg.get_value(), end='')
    else:
        var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
        if var is not None:
            # jedna se o nedefinovanou promennou
            if var.get_type() == "":
                print_error(MISSING_VALUE_ERROR)
            if var.get_type() == "nil":
                print("", end='')
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
        if var is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        if var.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        value_stack.append(var.get_value())
        type_stack.append(var.get_type())


def execute_pops(gf, tf, lf, instr):
    arg = instr.get_argument(1)
    if arg.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    else:
        var = search_variable(gf, tf, lf, arg.get_frame(), arg.get_value())
        if var is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        try:
            var.edit_value(value_stack.pop(), type_stack.pop())
        except IndexError:
            print_error(MISSING_VALUE_ERROR)


def execute_int2char(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        try:
            var.edit_value(chr(arg2.get_value()), "string")
        except ValueError:
            print_error(WRONG_STRING_WORKING_ERROR)
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="int")
        try:
            var.edit_value(chr(var2.get_value()), "string")
        except ValueError:
            print_error(WRONG_STRING_WORKING_ERROR)


def execute_read(file, gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "type" or arg2.get_type() == "nil":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    line = file.readline()
    nextline = file.readline()
    line = line.rstrip().decode('utf-8')
    if not line:
        if not nextline:
            var.edit_value("nil", "nil")
        else:
            var.edit_value("", "string")
    else:
        if arg2.get_value() == "bool":
            if line.upper() == "TRUE":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        elif arg2.get_value() == "int":
            try:
                var.edit_value(int(line), arg2.get_value())
            except ValueError:
                var.edit_value("nil", "nil")
        else:
            var.edit_value(line, arg2.get_value())
    file.seek(-len(nextline), 1)


def execute_and(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "bool":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == "true" and arg3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="bool")
            if arg2.get_value() == "true" and var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="bool")
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg3.get_value() == "true" and var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="bool")
            if var2.get_value() == "true" and var3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_or(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "bool":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == "true" or arg3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="bool")
            if arg2.get_value() == "true" or var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="bool")
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "bool":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg3.get_value() == "true" or var2.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="bool")
            if var2.get_value() == "true" or var3.get_value() == "true":
                var.edit_value("true", "bool")
            else:
                var.edit_value("false", "bool")


def execute_not(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "bool":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if arg2.get_value() == "true":
            var.edit_value("false", "bool")
        else:
            var.edit_value("true", "bool")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="bool")
        if var2.get_value() == "true":
            var.edit_value("false", "bool")
        else:
            var.edit_value("true", "bool")


def execute_strlen(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        var.edit_value(len(arg2.get_value()), "int")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="string")
        var.edit_value(len(var2.get_value()), "int")


def execute_concat(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
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
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="string")
            var.edit_value(arg2.get_value() + var2.get_value(), "string")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="string")
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            var.edit_value(var2.get_value() + arg3.get_value(), "string")
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="string")
            var.edit_value(var2.get_value() + var3.get_value(), "string")


def execute_type(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        var.edit_value(arg2.get_type(), "string")
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        var.edit_value(var2.get_type(), "string")


def execute_exit(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        if arg1.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if int(arg1.get_value()) > 49 or int(arg1.get_value()) < 0:
            print_error(WRONG_OPERAND_VALUE_ERROR)
        exit(int(arg1.get_value()))
    else:
        var = get_and_check_var(instr, 1, gf, tf, lf, check_type=1, checking_type="int")
        if int(var.get_value()) > 49 or int(var.get_value()) < 0:
            print_error(WRONG_OPERAND_VALUE_ERROR)
        exit(int(var.get_value()))


def execute_dprint(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        sys.stderr.write(arg1.get_value())
    else:
        var = search_variable(gf, tf, lf, arg1.get_frame(), arg1.get_value())
        if var is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        # jedna se o nedefinovanou promennou
        if var.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        sys.stderr.write("{}".format(var.get_value()))


def execute_stri2int(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            get_ord(var, arg2, arg3)
        else:
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="int")
            get_ord(var, arg2, var2)
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="string")
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            get_ord(var, var2, arg3)
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="int")
            get_ord(var, var2, var3)


def execute_getchar(gf, tf, lf, instr):
    var = get_and_check_var(instr, 1, gf, tf, lf)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "string":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if int(arg3.get_value()) < 0:
                print_error(WRONG_STRING_WORKING_ERROR)
            try:
                var.edit_value(arg2.get_value()[int(arg3.get_value())], "string")
            except IndexError:
                print_error(WRONG_STRING_WORKING_ERROR)
        else:
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="int")
            if int(var2.get_value()) < 0:
                print_error(WRONG_STRING_WORKING_ERROR)
            try:
                var.edit_value(arg2.get_value()[int(var2.get_value())], "string")
            except IndexError:
                print_error(WRONG_STRING_WORKING_ERROR)
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="string")
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "int":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if int(arg3.get_value()) < 0:
                print_error(WRONG_STRING_WORKING_ERROR)
            try:
                var.edit_value(var2.get_value()[int(arg3.get_value())], "string")
            except IndexError:
                print_error(WRONG_STRING_WORKING_ERROR)
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="int")
            if int(var3.get_value()) < 0:
                print_error(WRONG_STRING_WORKING_ERROR)
            try:
                var.edit_value(var2.get_value()[int(var3.get_value())], "string")
            except IndexError:
                print_error(WRONG_STRING_WORKING_ERROR)


def execute_setchar(gf, tf, lf, instr):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "var":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    var = get_and_check_var(instr, 1, gf, tf, lf, check_type=1, checking_type="string")
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        if arg2.get_type() != "int":
            print_error(WRONG_OPERAND_TYPE_ERROR)
        if int(arg2.get_value()) < 0 or int(arg2.get_value()) > len(var.get_value()) - 1:
            print_error(WRONG_STRING_WORKING_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg3.get_value() == "":
                print_error(WRONG_STRING_WORKING_ERROR)
            var.edit_value(
                var.get_value()[:arg2.get_value()] + arg3.get_value()[0] + var.get_value()[arg2.get_value() + 1:],
                "string")
        else:
            var2 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="string")
            if var2.get_value() == "":
                print_error(WRONG_STRING_WORKING_ERROR)
            var.edit_value(
                var.get_value()[:arg2.get_value()] + var2.get_value()[0] + var.get_value()[arg2.get_value() + 1:],
                "string")
    else:
        var2 = get_and_check_var(instr, 2, gf, tf, lf, check_type=1, checking_type="int")
        if int(var2.get_value()) < 0 or int(var2.get_value()) > len(var.get_value()) - 1:
            print_error(WRONG_STRING_WORKING_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg3.get_type() != "string":
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg3.get_value() == "":
                print_error(WRONG_STRING_WORKING_ERROR)
            var.edit_value(
                var.get_value()[:var2.get_value()] + arg3.get_value()[0] + var.get_value()[var2.get_value() + 1:],
                "string")
        else:
            var3 = get_and_check_var(instr, 3, gf, tf, lf, check_type=1, checking_type="string")
            if var3.get_value() == "":
                print_error(WRONG_STRING_WORKING_ERROR)
            var.edit_value(
                var.get_value()[:var2.get_value()] + var3.get_value()[0] + var.get_value()[var2.get_value() + 1:],
                "string")


def execute_jump(instr):
    index = get_label_index(instr.get_argument(1).get_value())
    if index is None:
        print_error(UNDEFINED_LABEL_OR_REDEFINITION_ERROR)
    return index


def execute_jumpifeq(gf, tf, lf, instr, i):
    index = get_index_check_label(instr)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != "nil" and arg3.get_type() != "nil" and arg2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == arg3.get_value():
                return index
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            # jedna se o nedefinovanou promennou
            if var2.get_type() == "":
                print_error(MISSING_VALUE_ERROR)
            if var2.get_type() != "nil" and arg2.get_type() != "nil" and var2.get_type() != arg2.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() == var2.get_value():
                return index
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        # jedna se o nedefinovanou promennou
        if var2.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if var2.get_type() != "nil" and arg3.get_type() != "nil" and var2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() == arg3.get_value():
                return index
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            # jedna se o nedefinovanou promennou
            if var3.get_type() == "":
                print_error(MISSING_VALUE_ERROR)
            if var2.get_type() != "nil" and var3.get_type() != "nil" and var2.get_type() != var3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() == var3.get_value():
                return index
    return i


def execute_jumpifneq(gf, tf, lf, instr, i):
    index = get_index_check_label(instr)
    arg2 = instr.get_argument(2)
    if arg2.get_type() != "var":
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if arg2.get_type() != "nil" and arg3.get_type() != "nil" and arg2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() != arg3.get_value():
                return index
        else:
            var2 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var2 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            # jedna se o nedefinovanou promennou
            if var2.get_type() == "":
                print_error(MISSING_VALUE_ERROR)
            if var2.get_type() != "nil" and arg2.get_type() != "nil" and var2.get_type() != arg2.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if arg2.get_value() != var2.get_value():
                return index
    else:
        var2 = search_variable(gf, tf, lf, arg2.get_frame(), arg2.get_value())
        if var2 is None:
            print_error(UNDEFINED_VARIABLE_ERROR)
        # jedna se o nedefinovanou promennou
        if var2.get_type() == "":
            print_error(MISSING_VALUE_ERROR)
        arg3 = instr.get_argument(3)
        if arg3.get_type() != "var":
            if var2.get_type() != "nil" and arg3.get_type() != "nil" and var2.get_type() != arg3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() != arg3.get_value():
                return index
        else:
            var3 = search_variable(gf, tf, lf, arg3.get_frame(), arg3.get_value())
            if var3 is None:
                print_error(UNDEFINED_VARIABLE_ERROR)
            # jedna se o nedefinovanou promennou
            if var3.get_type() == "":
                print_error(MISSING_VALUE_ERROR)
            if var2.get_type() != "nil" and var3.get_type() != "nil" and var2.get_type() != var3.get_type():
                print_error(WRONG_OPERAND_TYPE_ERROR)
            if var2.get_value() != var3.get_value():
                return index
    return i


def execute_call(instr, i):
    arg1 = instr.get_argument(1)
    if arg1.get_type() != "label":
        print_error(WRONG_OPERAND_TYPE_ERROR)
    index = get_label_index(instr.get_argument(1).get_value())
    if index is None:
        print_error(UNDEFINED_LABEL_OR_REDEFINITION_ERROR)
    call_stack.append(i)
    return index


def execute_return():
    try:
        return call_stack.pop()
    except IndexError:
        print_error(MISSING_VALUE_ERROR)


def execute_break(gf, tf, lf):
    sys.stderr.write("Obsah GF:\n")
    sys.stderr.write("{}\n".format(gf))
    sys.stderr.write("Obsah TF:\n")
    sys.stderr.write("{}\n".format(tf))
    sys.stderr.write("Obsah LF:\n")
    sys.stderr.write("{}\n".format(lf))


def execute_pushframe(tfdefined, tf):
    if tfdefined == 0:
        print_error(UNDEFINED_FRAME_ERROR)
    lf_stack.append(tf)
    return 0


def execute_popframe():
    try:
        return lf_stack.pop(), 1
    except IndexError:
        print_error(UNDEFINED_FRAME_ERROR)


def execute_instructions(input_path):
    global tf_defined
    file = None
    try:
        file = open(input_path, 'rb')
    except FileNotFoundError:
        print_error(INPUT_FILE_OPENING_ERROR)
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
            tf = frame()
        elif instr_opcode == "PUSHFRAME":
            tf_defined = execute_pushframe(tf_defined, tf)
            if len(lf_stack) > 0:
                lf = lf_stack[len(lf_stack) - 1]
        elif instr_opcode == "POPFRAME":
            tf, tf_defined = execute_popframe()
            if len(lf_stack) > 0:
                lf = lf_stack[len(lf_stack) - 1]
        elif instr_opcode == "DEFVAR":
            execute_defvar(gf, tf, lf, instr)
        elif instr_opcode == "CALL":
            i = execute_call(instr, i)
        elif instr_opcode == "RETURN":
            i = execute_return()
        elif instr_opcode == "PUSHS":
            execute_pushs(gf, tf, lf, instr)
        elif instr_opcode == "POPS":
            execute_pops(gf, tf, lf, instr)
        elif instr_opcode == "ADD":
            execute_arithmetic_operation(operator.add, instr, gf, tf, lf)
        elif instr_opcode == "SUB":
            execute_arithmetic_operation(operator.sub, instr, gf, tf, lf)
        elif instr_opcode == "MUL":
            execute_arithmetic_operation(operator.mul, instr, gf, tf, lf)
        elif instr_opcode == "IDIV":
            execute_arithmetic_operation(operator.floordiv, instr, gf, tf, lf)
        elif instr_opcode == "LT":
            execute_comparison_operation(operator.lt, instr, gf, tf, lf)
        elif instr_opcode == "GT":
            execute_comparison_operation(operator.gt, instr, gf, tf, lf)
        elif instr_opcode == "EQ":
            execute_comparison_operation(operator.eq, instr, gf, tf, lf)
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
        elif instr_opcode == "LABEL":
            i += 1
            continue
        elif instr_opcode == "JUMP":
            i = execute_jump(instr)
        elif instr_opcode == "JUMPIFEQ":
            i = execute_jumpifeq(gf, tf, lf, instr, i)
        elif instr_opcode == "JUMPIFNEQ":
            i = execute_jumpifneq(gf, tf, lf, instr, i)
        elif instr_opcode == "EXIT":
            execute_exit(gf, tf, lf, instr)
        elif instr_opcode == "DPRINT":
            execute_dprint(gf, tf, lf, instr)
        elif instr_opcode == "BREAK":
            execute_break(gf, tf, lf)
        else:
            print_error(UNEXPECTED_XML_STRUCTURE_ERROR)
        i += 1


if __name__ == '__main__':
    source_file, input_file = check_args_and_get_file_paths()
    tree, root = load_xml(source_file)
    check_xml(root)
    save_instructions(root)
    execute_instructions(input_file)
