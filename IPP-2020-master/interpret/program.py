from typing import List, IO, Dict
from models import Symbol, Variable
from enums import Frames, exitCodes
from helper import exit_app
import instructions as instrs
from sys import stdin
from stats import Stats


class Program():
    """ Definice aplikace, ktera se bude provadet. """

    def __init__(self, instructions: List, data_input: IO, stats: Stats):
        # Datovy vstup pro instrukci read.
        self.input = data_input
        # Aktualni pozice v programu.
        self.instruction_pointer = 0
        self.GF: Dict[str, Symbol] = dict()                 # Globalni ramec
        self.TF: Dict[str, Symbol] = None                   # Docasny ramec.
        self.LF_Stack: List[Dict[str, Symbol]] = list()     # Lokalni ramec.
        self.data_stack: List[Symbol] = list()              # Datovy zasobnik
        self.call_stack: List[int] = list()                 # Zasobnik volani
        self.exit_code = 0                                  # Navratovy kod
        self.stats = stats                                  # Statistiky

        # <label, instructionPointerPosition>
        self.labels: Dict[str, int] = dict()
        self.instructions: List[instrs.InstructionBase] = list()

        # Detekce navesti
        for instruction in instructions:
            if type(instruction) is instrs.Label:
                if instruction.name.name in self.labels:
                    exit_app(exitCodes.SEMANTIC_ERROR,
                             'Detected label redefinition.', True)

                self.labels.update(
                    {instruction.name.name: len(self.instructions)})
            else:
                self.instructions.append(instruction)

    def run(self):
        """ Provadeni programu. """

        while len(self.instructions) > self.instruction_pointer:
            instruction = self.instructions[self.instruction_pointer]
            self.instruction_pointer += 1
            instruction.execute(self)

            if self.stats is not None:
                self.stats.increment_insts()
                self.stats.increment_vars(self.GF, self.LF_Stack, self.TF)

    def var_exists(self, var: Variable):
        """ Kontrola na existenci promenne. """

        if var.frame == Frames.GLOBAL:
            return var.value in self.GF
        elif var.frame == Frames.TEMPORARY:
            if self.TF is None:
                exit_app(exitCodes.INVALID_FRAME,
                         'Temporary frame is unitialized', True)

            return var.value in self.TF
        elif var.frame == Frames.LOCAL:
            if len(self.LF_Stack) == 0:
                exit_app(exitCodes.INVALID_FRAME,
                         'Local frame stack is empty.', True)
            return var.value in self.LF_Stack[-1]

    def var_set(self, opcode: str, var: Variable, value: Symbol,
                create: bool = False):
        """ Nastaveni hodnoty promenne. Pripadne vytvořeni. """

        if not create and not self.var_exists(var):
            exit_app(exitCodes.UNDEFINED_VARIABLE,
                     '{}\nVariable {} not exists'.format(opcode, var.value),
                     True)

        if var.frame == Frames.GLOBAL:
            self.GF[var.value] = value
        elif var.frame == Frames.LOCAL:
            self.LF_Stack[-1][var.value] = value
        elif var.frame == Frames.TEMPORARY:
            self.TF[var.value] = value

    def var_get(self, opcode: str, var: Variable) -> Symbol:
        """ Ziskani hodnoty promenne. """

        if not self.var_exists(var):
            exit_app(exitCodes.UNDEFINED_VARIABLE,
                     '{}\nVariable {} not exists'.format(opcode, var.value),
                     True)

        if var.frame == Frames.TEMPORARY:
            return self.TF[var.value]
        elif var.frame == Frames.GLOBAL:
            return self.GF[var.value]
        elif var.frame == Frames.LOCAL:
            return self.LF_Stack[-1][var.value]

    def get_symb(self, opcode: str, symb: Symbol or Variable,
                 required_value: bool = True):
        result = symb
        if type(symb) is Variable:
            result = self.var_get(opcode, symb)

        if required_value and result is None:
            exit_app(exitCodes.UNDEFINED_VALUE,
                     '{}\nSymbol or variable is undefined.'.format(opcode))

        return result

    def exit(self, code: int):
        self.instruction_pointer = len(self.instructions)
        self.exit_code = code

    def get_state(self):
        """ Ziskani stavu aplikace """

        return "\n".join([
            "Input type: {}".format(
                'stdin' if self.input == stdin else 'file'),
            "IP: {}".format(self.instruction_pointer),
            "GlobalFrame: {}".format(self.GF),
            "LocalFrame: {}".format(self.LF_Stack),
            "TemporaryFrame: {}".format(self.TF),
            "data_stack: {}".format(self.data_stack),
            "call_stack: {}".format(self.call_stack),
            "Labels: {}".format(self.labels)
        ])

    def pop_stack(self, required_count: int):
        """ Ziskani N hodnot ze zasovniku. """
        
        if len(self.data_stack) < required_count:
            exit_app(exitCodes.UNDEFINED_VALUE,
                     'Invalid count of required arguments in stack at' +
                     ' instruction {}. Count of values in data_stack: {}'
                     .format(
                         self.instructions[self.instruction_pointer].opcode,
                         len(self.data_stack)))

        stack_data = list()
        for i in range(required_count):
            stack_data.append(self.data_stack.pop())

        return stack_data
