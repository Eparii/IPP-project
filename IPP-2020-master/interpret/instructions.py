from typing import List
from enums import ArgumentTypes, exitCodes, DataTypes
from helper import exit_app, validate_math_symbols, validate_comparable_symbols
from program import Program
from models import InstructionArgument, Symbol, Label as LabelModel
from sys import stdin, stderr


class InstructionBase():
    """ Bazova trida pro kazdou instrukci. """

    expected_args = []

    def __init__(self, args: List[InstructionArgument], opcode: str):
        if len(self.expected_args) != len(args):
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Invalid count of arguments at opcode {}'.format(opcode),
                     True)

        self.opcode = opcode
        self.args = args

    def execute(self, program: Program):
        raise NotImplementedError


# 6.4.1 Prace s ramci, volani funkci
class Move(InstructionBase):
    """ Vlozeni konstanty do promenne. """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('MOVE', self.args[1], False)
        program.var_set('MOVE', self.args[0], symb)


class Createframe(InstructionBase):
    """ Vytvoreni noveho docastneho ramce """

    def execute(self, program: Program):
        program.TF = dict()


class Pushframe(InstructionBase):
    """ Presun docasneho ramce na vrchol zasobniku ramcu. """

    def execute(self, program: Program):
        if program.TF is None:
            exit_app(exitCodes.INVALID_FRAME,
                     'PUSHFRAME\nInvalid access to undefined temporary frame.',
                     True)

        program.LF_Stack.append(program.TF)
        program.TF = None


class Popframe(InstructionBase):
    """ Presun ramce z vrcholu zasoniku ramcu do lokalniho ramce. """

    def execute(self, program: Program):
        if len(program.LF_Stack) == 0:
            exit_app(exitCodes.INVALID_FRAME,
                     'POPFRAME\nNo available local frame.', True)

        program.TF = program.LF_Stack.pop()


class Defvar(InstructionBase):
    """ Definice promenne. """

    expected_args = [ArgumentTypes.VARIABLE]

    def execute(self, program: Program):
        arg = self.args[0]

        if program.var_exists(arg):
            exit_app(exitCodes.SEMANTIC_ERROR,
                     'DEFVAR\nVariable {} now exists. Cannot redefine.', True)

        program.var_set('DEFVAR', arg, None, True)


class Return(InstructionBase):
    """ Instrukce pro skok na pozici definovanou na vrcholu zasobniku volani """

    def execute(self, program: Program):
        if len(program.call_stack) == 0:
            exit_app(exitCodes.UNDEFINED_VALUE,
                     'RETURN\nEmpty call stack.', True)
        program.instruction_pointer = program.call_stack.pop()


# Prace s datovym zasobnikem
class PushS(InstructionBase):
    """ Ulozeni hodnoty (nebo obsahu promenne) na vrchol datoveho zasobniku. """

    expected_args = [ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('PUSHS', self.args[0])
        program.data_stack.append(symb)


class PopS(InstructionBase):
    """ Ziskani hodnoty z vrcholu datoveho zasobniku a ulozeni do promenne """

    expected_args = [ArgumentTypes.VARIABLE]

    def execute(self, program: Program):
        if len(program.data_stack) == 0:
            exit_app(exitCodes.UNDEFINED_VALUE,
                     'POPS\nInstruction {}. Data Stack is empty.'.format(
                         self.opcode), True)

        program.var_set('POPS', self.args[0], program.pop_stack(1)[0])


# 6.4.3 Aritmeticke, relacni, booleovske a konverzni instrukce
class MathInstructionBase(InstructionBase):
    """
    Bazova trida pro vsechny matematicke instrukce.
    Zakladni verze pouzivajici operandy.
    """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL,
                     ArgumentTypes.SYMBOL]

    def compute(self, symb1: Symbol, symb2: Symbol):
        raise NotImplementedError

    def execute(self, program: Program):
        symb1 = program.get_symb(self.opcode, self.args[1])
        symb2 = program.get_symb(self.opcode, self.args[2])

        validate_math_symbols(self.opcode, symb1, symb2)

        result = self.compute(symb1, symb2)
        program.var_set(self.opcode, self.args[0], result)


class StackMathInstructionBase(InstructionBase):
    """
    Bazova trida pro vsechny matematicke instrukce.
    Rozsirena verze pouzivajici zasobnik.
    """

    expected_args = []

    def compute(self, symb1: Symbol, symb2: Symbol):
        raise NotImplementedError

    def execute(self, program: Program):
        symbols = program.pop_stack(2)

        validate_math_symbols(self.opcode, symbols[1], symbols[0])

        result = self.compute(symbols[1], symbols[0])
        program.data_stack.append(result)


class Add(MathInstructionBase):
    """ Scitani (Zakladni varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value + symb2.value)


class Sub(MathInstructionBase):
    """ Odcitani (Zakldani varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value - symb2.value)


class Mul(MathInstructionBase):
    """ Nasobeni (Zakladni varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value * symb2.value)


class IDiv(MathInstructionBase):
    """ Celociselne deleni (Zakladani varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        if symb2.value == 0:
            exit_app(exitCodes.INVALID_OPERAND_VALUE,
                     'Detected zero division.', True)

        return Symbol(DataTypes.INT, symb1.value // symb2.value)


class ComparableInstruction(InstructionBase):
    """
    Bazova trida pro porovnavaci instrukce.
    Zakladni verze pozivajici operandy.
    """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL,
                     ArgumentTypes.SYMBOL]

    allowedTypes = [DataTypes.INT, DataTypes.BOOL,
                    DataTypes.STRING, DataTypes.FLOAT]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        raise NotImplementedError

    def execute(self, program: Program):
        symb1 = program.get_symb(self.opcode, self.args[1])
        symb2 = program.get_symb(self.opcode, self.args[2])

        validate_comparable_symbols(self.opcode, symb1,
                                    symb2, self.allowedTypes)

        result = Symbol(DataTypes.BOOL, self.compare(symb1, symb2))
        program.var_set(self.opcode, self.args[0], result)


class StackComparableInstruction(InstructionBase):
    """
    Bazova trida pro porovnavaci instrukce.
    Rozsirena verze pouzivajici zasobnik.
    """

    expected_args = []

    allowedTypes = [DataTypes.INT, DataTypes.BOOL,
                    DataTypes.STRING, DataTypes.FLOAT]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        raise NotImplementedError

    def execute(self, program: Program):
        symbols = program.pop_stack(2)

        validate_comparable_symbols(self.opcode, symbols[1],
                                    symbols[0], self.allowedTypes)

        result = Symbol(DataTypes.BOOL, self.compare(symbols[1], symbols[0]))
        program.data_stack.append(result)


class Lt(ComparableInstruction):
    """ Mensi (<) """

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value < symb2.value


class Gt(ComparableInstruction):
    """ Vetsi (>) """

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value > symb2.value


class Eq(ComparableInstruction):
    """ Rovno (==) """

    allowedTypes = [DataTypes.INT, DataTypes.BOOL,
                    DataTypes.STRING, DataTypes.NIL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.equals(symb2)


class And(ComparableInstruction):
    """ A (&&) """

    allowedTypes = [DataTypes.BOOL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value and symb2.value


class Or(ComparableInstruction):
    """ Nebo (||) """

    allowedTypes = [DataTypes.BOOL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value or symb2.value


class Not(InstructionBase):
    """ Negace (!) """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('NOT', self.args[1])

        if not symb.is_bool():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'NOT\nInvalid data type. Expected: bool. Have: ({})'
                     .format(symb.data_type.value), True)

        result = Symbol(DataTypes.BOOL, not symb.value)
        program.var_set('NOT', self.args[0], result)


class Int2Char(InstructionBase):
    """ Převod čísla na znak. """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        var = self.args[0]
        symb = program.get_symb('INT2CHAR', self.args[1])

        if not symb.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHARS\nInvalid data type. Expected: int', True)

        try:
            char = chr(symb.value)
            program.var_set('INT2CHAR', var, Symbol(DataTypes.STRING, char))
        except Exception:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'INT2CHAR\nInvalid int to char conversion value. {}'
                     .format(symb.value))


class Stri2Int(InstructionBase):
    """ Prevod znaku na urcite pozici na cislo """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        string = program.get_symb('STRI2INT', self.args[1])
        index = program.get_symb('STRI2INT', self.args[2])

        if string is None or not string.is_string() or index is None or not index.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'STRI2INT\nInvalid data type. Expected: string and int.' +
                     ' Have: {} and {}'.format(string.data_type.value,
                                               index.data_type.value), True)

        try:
            ordinary = ord(string.value[index.value])
            program.var_set('STRI2INT', self.args[0], Symbol(DataTypes.INT,
                                                             ordinary))
        except IndexError:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'String is out of range.', True)


# 6.4.4 Vstupne-vystupni instrukce
class Read(InstructionBase):
    """
    Cteni dat ze standardniho vstupu, nebo ze souboru, ktery byl zadan
    pomoci parametru --input
    """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.TYPE]

    def execute(self, program: Program):
        try:
            if program.input == stdin:
                line = input().rstrip()
            else:
                line = program.input.readline().rstrip()
        except Exception:
            line = None

        arg_type = self.args[1]

        if line is None:
            program.var_set('READ', self.args[0], Symbol(DataTypes.NIL, None))
        elif arg_type.type is bool:
            program.var_set('READ', self.args[0],
                            Symbol(DataTypes.BOOL, line.lower() == 'true'))
        elif arg_type.type is str:
            program.var_set('READ', self.args[0], Symbol(DataTypes.STRING,
                                                         line))
        elif arg_type.type is int:
            try:
                temp_val = int(line)
                if str(temp_val) != line:
                    program.var_set(
                        'READ', self.args[0], Symbol(DataTypes.NIL, None))
                else:
                    program.var_set('READ', self.args[0], Symbol(
                        DataTypes.INT, temp_val))
            except ValueError:
                program.var_set(
                    'READ', self.args[0], Symbol(DataTypes.NIL, None))
        elif arg_type.type is float:
            try:
                try:
                    float_value = float(line)
                except ValueError:
                    float_value = float.fromhex(line)
            except Exception:
                program.var_set(
                    'READ', self.args[0], Symbol(DataTypes.NIL, None))
            else:
                program.var_set('READ', self.args[0], Symbol(
                    DataTypes.FLOAT, float_value))


class Write(InstructionBase):
    """ Instrukce pro vypis symbolu na standardni vystup. """

    expected_args = [ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('WRITE', self.args[0])

        if symb.is_nil():
            print('', end='')
        elif symb.is_bool():
            print(str(symb.value).lower(), end='')
        elif symb.is_float():
            print(symb.value.hex(), end='')
        else:
            print(symb.value, end='')


# 6.4.5 Prace s retezci
class Concat(InstructionBase):
    """ Konkatenace dvou retezcu. """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb1 = program.get_symb('CONCAT', self.args[1])

        if not symb1.is_string():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'CONCAT\nInvalid type at second operand.', True)

        symb2 = program.get_symb('CONCAT', self.args[2])

        if not symb2.is_string():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'CONCAT\nInvalid type at third operand.', True)

        result = Symbol(DataTypes.STRING, symb1.value + symb2.value)
        program.var_set('CONCAT', self.args[0], result)


class Strlen(InstructionBase):
    """ Zjisteni delky retezce. """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        string = program.get_symb('STRLEN', self.args[1])

        if not string.is_string():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'STRLEN\nExpected string', True)

        string_length = Symbol(DataTypes.INT, len(string.value))
        program.var_set('STRLEN', self.args[0], string_length)


class Getchar(InstructionBase):
    """ Ziskani znaku z retezce na urcite pozici """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        string = program.get_symb('GETCHAR', self.args[1])
        index = program.get_symb('GETCHAR', self.args[2])

        if not string.is_string() or not index.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'GETCHAR\nExpected string and int', True)

        try:
            result = Symbol(DataTypes.STRING, string.value[index.value])
            program.var_set('GETCHAR', self.args[0], result)
        except IndexError:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'GETCHAR\nIndex out of range.', True)


class Setchar(InstructionBase):
    """ Uprava znaku na urcite pozici """

    expected_args = [ArgumentTypes.VARIABLE,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        variable = program.var_get('SETCHAR', self.args[0])
        index = program.get_symb('SETCHAR', self.args[1])
        toModify = program.get_symb('SETCHAR', self.args[2])

        if variable is None:
            exit_app(exitCodes.UNDEFINED_VALUE,
                     'SETCHAR\nUndefined variable.', True)

        if not index.is_int() or not variable.is_string() or\
                not toModify.is_string():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'SETCHAR\nExpected: string variable, int, string', True)

        if len(toModify.value) == 0 or index.value >= len(variable.value):
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'SETCHAR\nZero length of to modify characters.', True)

        try:
            result = "{}{}{}".format(variable.value[:index.value],
                                     toModify.value[0],
                                     variable.value[index.value + 1:])
            program.var_set('SETCHAR', self.args[0],
                            Symbol(DataTypes.STRING, result))
        except IndexError:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'SETCHAR\nIndex is out of range.', True)


# 6.4.6 Prace s typy
class Type(InstructionBase):
    """ Zjisteni datoveho typu. """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('TYPE', self.args[1], False)

        if symb is None:
            program.var_set('TYPE', self.args[0], Symbol(DataTypes.STRING, ''))
        else:
            program.var_set('TYPE', self.args[0], Symbol(
                DataTypes.STRING, symb.data_type.value))


# 6.4.7 Instrukce pro rizeni toku programu
class Label(InstructionBase):
    """ Navesti """

    expected_args = [ArgumentTypes.LABEL]

    def __init__(self, args: List, opcode: str):
        InstructionBase.__init__(self, args, opcode)
        self.name = args[0]


class Jump(InstructionBase):
    """ Skok na návěští. """

    expected_args = [ArgumentTypes.LABEL]

    def execute(self, program: Program):
        label: LabelModel = self.args[0]
        if label.name not in program.labels:
            exit_app(exitCodes.SEMANTIC_ERROR,
                     'Undefined label to jump. ({})'.format(label.name), True)

        program.instruction_pointer = program.labels[label.name]


class Call(Jump):
    """ Uložení aktuální pozice do zásobníku volání a skok na návěští """

    def execute(self, program: Program):
        program.call_stack.append(program.instruction_pointer)
        Jump.execute(self, program)


class Jumpifeq(Jump):
    """ Skok na návěští, pokud budou 2 hodnoty stejné. """

    expected_args = [ArgumentTypes.LABEL,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb1 = program.get_symb('JUMPIFEQ', self.args[1])
        symb2 = program.get_symb('JUMPIFEQ', self.args[2])

        if symb2.equal_type(symb1.data_type) or symb1.is_nil() or\
                symb2.is_nil():
            if symb2.equals_value(symb1):
                Jump.execute(self, program)
        else:
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'JUMPIFEQ\nOperands must have same type.', True)


class Jumpifneq(Jump):
    """ Skok na návěští, pokud 2 hodnoty nebudou stejné """

    expected_args = [ArgumentTypes.LABEL,
                     ArgumentTypes.SYMBOL, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb1 = program.get_symb('JUMPNIFEQ', self.args[1])
        symb2 = program.get_symb('JUMPNIFEQ', self.args[2])

        if symb2.equal_type(symb1.data_type) or symb1.is_nil() or\
                symb2.is_nil():
            if not symb2.equals_value(symb1):
                Jump.execute(self, program)
        else:
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'JUMPIFEQ\nOperands must have same type.', True)


class Exit(InstructionBase):
    """ Předčasné ukončení programu s návratovým kódem. """

    expected_args = [ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('EXIT', self.args[0], True)

        if not symb.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'EXIT\nInvalid exit code', True)
        elif symb.value < 0 or symb.value > 49:
            exit_app(exitCodes.INVALID_OPERAND_VALUE,
                     'EXIT\nInvalid exit code. Allowed range is <0; 49>.',
                     True)
        else:
            program.exit(symb.value)


# 6.4.8 Ladici instrukce
class DPrint(InstructionBase):
    """ Vypis symbolu na standardni chybovy vystup. """

    expected_args = [ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('DPRINT', self.args[0])
        print(symb.value, file=stderr)


class Break(InstructionBase):
    """ Vypis aktualniho stavu programu. """

    def execute(self, program: Program):
        print(program.get_state(), file=stderr)


# Rozsireni FLOAT
class Int2Float(InstructionBase):
    """ Prevod celociselne hodnoty na cislo s plovouci desetinnou carkou """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('INT2FLOAT', self.args[1])

        if not symb.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHAR\nInvalid data type' +
                     ' Expected INT in second parameter.')

        symbol = Symbol(DataTypes.FLOAT, float(symb.value))
        program.var_set('INT2FLOAT', self.args[0], symbol)


class Float2Int(InstructionBase):
    """ Prevod cisla s desetinnou carkou na cele cislo. """

    expected_args = [ArgumentTypes.VARIABLE, ArgumentTypes.SYMBOL]

    def execute(self, program: Program):
        symb = program.get_symb('FLOAT2INT', self.args[1])

        if not symb.is_float():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHAR\nInvalid data type' +
                     ' Expected FLOAT in second parameter.')

        symbol = Symbol(DataTypes.INT, int(symb.value))
        program.var_set('FLOAT2INT', self.args[0], symbol)


class Div(MathInstructionBase):
    """ Deleni s plovouci desetinnou carkou. """

    def compute(self, symb1: Symbol, symb2: Symbol):
        if symb2.value == 0.0:
            exit_app(exitCodes.INVALID_OPERAND_VALUE,
                     'DIV\nDetected zero division.', True)

        return Symbol(DataTypes.FLOAT, symb1.value / symb2.value)


# Rozsireni STACK
class Clears(InstructionBase):
    """ Smazani vsech dat v datovem zasobniku """

    expected_args = []

    def execute(self, program: Program):
        program.data_stack = list()


class Adds(StackMathInstructionBase):
    """ Scitani (Zasobnikova varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value + symb2.value)


class Subs(StackMathInstructionBase):
    """ Odcitani (Zasobnikova varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value - symb2.value)


class Muls(StackMathInstructionBase):
    """ Nasobeni (Zasobnikova varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value * symb2.value)


class IDivs(StackMathInstructionBase):
    """ Celociselne deleni (Zasobnikova varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value // symb2.value)


# FLOAT + STACK
class Divs(StackMathInstructionBase):
    """ Deleni s plovouci desetinnou carkou (Zasobnikova varianta) """

    def compute(self, symb1: Symbol, symb2: Symbol):
        return Symbol(symb1.data_type, symb1.value / symb2.value)


class Lts(StackComparableInstruction):
    """ Mensi (<) (Zasobnikova varianta) """

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value < symb2.value


class Gts(StackComparableInstruction):
    """ Vetsi (>) (Zasobnikova varianta) """

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value > symb2.value


class Eqs(StackComparableInstruction):
    """ Rovno (==) (Zasobnikova varianta) """

    allowedTypes = [DataTypes.INT, DataTypes.BOOL,
                    DataTypes.STRING, DataTypes.NIL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.equals(symb2)


class Ands(StackComparableInstruction):
    """ A (&&) (Zasobnikova varianta) """

    allowedTypes = [DataTypes.BOOL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value and symb2.value


class Ors(StackComparableInstruction):
    """ Nebo (||) (Zasobnikova varianta) """

    allowedTypes = [DataTypes.BOOL]

    def compare(self, symb1: Symbol, symb2: Symbol) -> bool:
        return symb1.value or symb2.value


class Nots(InstructionBase):
    """ Negace (!) (Zasobnikova varianta) """

    expected_args = []

    def execute(self, program: Program):
        symb = program.pop_stack(1)[0]

        if not symb.is_bool():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'NOT\nInvalid data type. Expected: bool. Have: ({})'
                     .format(symb.data_type.value), True)

        result = Symbol(DataTypes.BOOL, not symb.value)
        program.data_stack.append(result)


class Int2Chars(InstructionBase):
    """ Převod čísla na znak. (Zasobnikova varianta) """

    expected_args = []

    def execute(self, program: Program):
        symb = program.pop_stack(1)[0]

        if not symb.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHARS\nInvalid data type. Expected: int', True)

        try:
            char = chr(symb.value)
        except Exception:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'INT2CHARS\nInvalid int to char conversion value. {}'
                     .format(symb.value))
        else:
            program.data_stack.append(Symbol(DataTypes.STRING, char))


class Stri2Ints(InstructionBase):
    """ Prevod znaku na urcite pozici na cislo (Zasobnikova varianta) """

    expected_args = []

    def execute(self, program: Program):
        symbols = program.pop_stack(2)
        index = symbols[0]
        string = symbols[1]

        if not string.is_string() or not index.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'STRI2INTS\nInvalid data type. Expected: string and int.'
                     + ' Have: {} and {}'.format(string.data_type.value,
                                                 index.data_type.value), True)

        try:
            ordinary = ord(string.value[index.value])
        except IndexError:
            exit_app(exitCodes.INVALID_STRING_OPERATION,
                     'String is out of range.', True)
        else:
            program.data_stack.append(Symbol(DataTypes.INT, ordinary))


class Jumpifeqs(Jump):
    """ Skok na návěští, pokud budou 2 hodnoty stejné. (Zasobnikova varianta) """

    expected_args = [ArgumentTypes.LABEL]

    def execute(self, program: Program):
        symbols = program.pop_stack(2)

        symb2 = symbols[0]
        symb1 = symbols[1]

        if symb2.equal_type(symb1.data_type) or symb1.is_nil() or\
                symb2.is_nil():
            if symb2.equals_value(symb1):
                Jump.execute(self, program)
        else:
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'JUMPIFEQS\nOperands must have same type.', True)


class Jumpifneqs(Jump):
    """ Skok na návěští, pokud nebudou 2 hodnoty stejné. (Zasobnikova varianta) """

    expected_args = [ArgumentTypes.LABEL]

    def execute(self, program: Program):
        symbols = program.pop_stack(2)

        symb2 = symbols[0]
        symb1 = symbols[1]

        if symb2.equal_type(symb1.data_type) or symb1.is_nil() or\
                symb2.is_nil():
            if not symb2.equals_value(symb1):
                Jump.execute(self, program)
        else:
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'JUMPIFEQS\nOperands must have same type.', True)


class Int2Floats(InstructionBase):
    """ Prevod celociselne hodnoty na cislo s plovouci desetinnou carkou. (Zasobnikova varianta) """

    expected_args = []

    def execute(self, program: Program):
        symb = program.pop_stack(1)[0]

        if not symb.is_int():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHAR\nInvalid data type' +
                     ' Expected INT in second parameter.')

        symbol = Symbol(DataTypes.FLOAT, float(symb.value))
        program.data_stack.append(symbol)


class Float2Ints(InstructionBase):
    """ Prevod cisla s desetinnou carkou na cele cislo. (Zasobnikova varianta) """

    expected_args = []

    def execute(self, program: Program):
        symb = program.pop_stack(1)[0]

        if not symb.is_float():
            exit_app(exitCodes.INVALID_DATA_TYPE,
                     'INT2CHAR\nInvalid data type' +
                     ' Expected FLOAT in second parameter.')

        symbol = Symbol(DataTypes.INT, int(symb.value))
        program.data_stack.append(symbol)


OPCODE_TO_CLASS_MAP = {
    # 6.4.1 Prace s ramci, volani funkci
    "MOVE": Move,
    "CREATEFRAME": Createframe,
    "PUSHFRAME": Pushframe,
    "POPFRAME": Popframe,
    "DEFVAR": Defvar,
    "CALL": Call,
    "RETURN": Return,

    # Prace s datvym zasobnikem
    "PUSHS": PushS,
    "POPS": PopS,

    # 6.4.3 Aritmeticke, relacni, booleovske a konverzni instrukce
    "ADD": Add,
    "SUB": Sub,
    "MUL": Mul,
    "IDIV": IDiv,
    "LT": Lt,
    "GT": Gt,
    "EQ": Eq,
    "AND": And,
    "OR": Or,
    "NOT": Not,
    "INT2CHAR": Int2Char,
    "STRI2INT": Stri2Int,

    # 6.4.4 Vstupne vystupni instrukce
    "READ": Read,
    "WRITE": Write,

    # 6.4.5 Prace s retezci
    "CONCAT": Concat,
    "STRLEN": Strlen,
    "GETCHAR": Getchar,
    "SETCHAR": Setchar,

    # 6.4.6 Prace s typy
    "TYPE": Type,

    # 6.4.7 Instrukce pro rizeni toku programu
    "LABEL": Label,
    "JUMP": Jump,
    "JUMPIFEQ": Jumpifeq,
    "JUMPIFNEQ": Jumpifneq,
    "EXIT": Exit,

    # 6.4.8 Ladici instrukce
    "DPRINT": DPrint,
    "BREAK": Break,

    # Rozsireni FLOAT
    "INT2FLOAT": Int2Float,
    "FLOAT2INT": Float2Int,
    "DIV": Div,

    # Rozsireni STACK
    "CLEARS": Clears,
    "ADDS": Adds,
    "SUBS": Subs,
    "MULS": Muls,
    "IDIVS": IDivs,
    "DIVS": Divs,
    "LTS": Lts,
    "GTS": Gts,
    "EQS": Eqs,
    "ANDS": Ands,
    "ORS": Ors,
    "NOTS": Nots,
    "INT2CHARS": Int2Chars,
    "STRI2INTS": Stri2Ints,
    "JUMPIFNEQS": Jumpifneqs,
    "JUMPIFEQS": Jumpifeqs,
    "INT2FLOATS": Int2Floats,
    "FLOAT2INTS": Float2Ints
}
