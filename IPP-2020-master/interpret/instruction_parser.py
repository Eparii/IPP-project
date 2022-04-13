from typing import IO, Dict, List
import instructions
from xml.etree.ElementTree import parse as parse_xml, ParseError, Element
from helper import exit_app
from enums import exitCodes, ArgumentTypes, Frames, DataTypes
import re
from models import (InstructionArgument, Symbol, Variable, Type, Label)


class InstructionsParser():
    """ Trida k nacitani a deserializaci vstupnich XML dat do internich struktur. """

    @staticmethod
    def parse_file(file: IO) -> Dict[int, instructions.InstructionBase]:
        """ Nacteni XML dat z datoveho proudu a zpracovani. 

        Perameters
        ----------
        file: IO
            Vstupni datovy proud.

        Returns
        -------
        Dict[int, instructions.InstructionBase]
            Serazeny slovnik, kde klicem bude obsah XML atributu order.
        """
        try:
            xml_data = parse_xml(file).getroot()
            return InstructionsParser.parse(xml_data)
        except ParseError:
            exit_app(exitCodes.INVALID_XML_FORMAT, 'Invalid XML format.', True)

    @staticmethod
    def parse(xml_data: Element) -> Dict[int, instructions.InstructionBase]:
        """ Nacitani XML dat a jejich rozbiti do struktur.

        Parameters
        ----------
        xml_data: Element
            Korenovy XML prvek.
        Returns
        -------
        Dict[int, instructions.InstructionBase]
            Serazeny slovnik, kde klicem bude obsah XML atributu order.
        """

        if xml_data.tag != 'program':
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Invalid XML root Element. Expected program', True)

        if 'language' not in xml_data.attrib.get('language') != 'IPPcode20':
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Invalid XML structure. Expected language IPPCode20',
                     True)

        result: Dict[int, instructions.InstructionBase] = dict()
        for element in list(xml_data):
            if element.tag != 'instruction':
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Unknown element in program element.', True)

            try:
                order = int(element.attrib.get('order'))

                if order <= 0:
                    exit_app(exitCodes.INVALID_XML_STRUCT,
                             'Negative instructions order', True)
            except ValueError:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Order attribute must be integer', True)
            except TypeError:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Order element not found.', True)

            if order in result:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Found element with same order.', True)

            result[order] = InstructionsParser.parse_instruction(
                element, order)

        return dict(sorted(result.items()))

    @staticmethod
    def parse_instruction(element: Element, order: int) -> \
            instructions.InstructionBase:
        """ Nacteni a zpracovani jedne instrukce.

        Parameters
        ----------
        element: Element
            XML element obsahujici data instrukce.
        order: int
            Poradi instrukce (bude pouzit pouze pri hlaseni chyb.)
        Returns
        -------
        instructions.InstructionBase
            Instance tridy konkretni instrukce.
        """
        opcode = element.get('opcode')

        if opcode is None or len(opcode) == 0:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Missing element at {}'.format(order), True)

        opcode = opcode.upper()
        if opcode not in instructions.OPCODE_TO_CLASS_MAP:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Unknown opcode. ({})'.format(opcode), True)

        args = InstructionsParser.parse_arguments(element)
        instruction = instructions.OPCODE_TO_CLASS_MAP[opcode](args, opcode)

        for i in range(0, len(args)):
            expected = instruction.expected_args[i]
            real = args[i].arg_type

            is_invalid = False

            if expected == ArgumentTypes.SYMBOL:
                if real != ArgumentTypes.VARIABLE and \
                        real != ArgumentTypes.SYMBOL:
                    is_invalid = True
            elif expected == ArgumentTypes.VARIABLE and \
                    real != ArgumentTypes.VARIABLE:
                is_invalid = True
            elif expected == ArgumentTypes.LABEL and \
                    real != ArgumentTypes.LABEL:
                is_invalid = True
            elif expected == ArgumentTypes.TYPE and real != ArgumentTypes.TYPE:
                is_invalid = True

            if is_invalid:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid argument. Expected <{}>. Have: <{}>'
                         .format(expected.value, real.value))

        return instruction

    @staticmethod
    def parse_arguments(element: Element) -> List[InstructionArgument]:
        """ Nacteni parametru instrukce.

        Parameters
        ----------
        element: Element
            XML element obsahujici data instrukce.
        Returns
        -------
        List[InstructionArgument]
            Pole instanci parametru instrukce.
        """
        arg1 = element.findall('arg1')
        arg2 = element.findall('arg2')
        arg3 = element.findall('arg3')

        if len(arg1) > 1:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Multiple elements named arg1', True)
        elif len(arg2) > 1:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Multiple elements named arg2', True)
        elif len(arg3) > 1:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Multiple elements named arg3', True)

        if len(arg3) > 0 and (len(arg1) == 0 or len(arg2) == 0):
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Third argument was set, but first or second missing.',
                     True)
        if len(arg2) > 0 and len(arg1) == 0:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Second argument was set, but first missing.', True)

        args = list()

        if len(arg1) > 0:
            args.append(InstructionsParser.parse_argument(arg1[0]))
        if len(arg2) > 0:
            args.append(InstructionsParser.parse_argument(arg2[0]))
        if len(arg3) > 0:
            args.append(InstructionsParser.parse_argument(arg3[0]))

        return args

    @staticmethod
    def parse_argument(arg: Element) -> InstructionArgument:
        """ Zpracovani parametru instrukce.

        Parameters
        ----------
        arg: Element
            XML element parametru.
        Returns
        -------
        InstructionArgument
            Zpracovany parametr.
        """

        if len(list(arg)) > 0:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Argument contains unexpected elements.', True)

        arg_type = arg.attrib.get('type')
        arg_value = arg.text if arg.text is not None else ''

        if arg_type == ArgumentTypes.LABEL.value:
            InstructionsParser.validate_variable_name(arg_value, True)
            return Label(arg_value)
        elif arg_type == ArgumentTypes.VARIABLE.value:
            variable_parts = arg_value.split('@', 1)

            if len(variable_parts) == 2:
                InstructionsParser.validate_scope(variable_parts[0])
                InstructionsParser.validate_variable_name(variable_parts[1])

                if variable_parts[0] == 'GF':
                    return Variable(Frames.GLOBAL, variable_parts[1])
                elif variable_parts[0] == 'TF':
                    return Variable(Frames.TEMPORARY, variable_parts[1])
                elif variable_parts[0] == 'LF':
                    return Variable(Frames.LOCAL, variable_parts[1])
            else:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid variable. ({})'.format(arg_value), True)
        elif arg_type == 'nil':
            if arg_value != 'nil':
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid value of nil. ({})'.format(arg_value), True)

            return Symbol(DataTypes.NIL, None)
        elif arg_type == 'int':
            try:
                return Symbol(DataTypes.INT, int(arg_value))
            except ValueError:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid int value. ({})'.format(arg_value), True)
        elif arg_type == 'bool':
            if arg_value == 'true':
                return Symbol(DataTypes.BOOL, True)
            elif arg_value == 'false':
                return Symbol(DataTypes.BOOL, False)
            else:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid boolean value. ({})'.format(arg_value), True)
        elif arg_type == 'string':
            if re.compile('.*#.*').match(arg_value):
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Text cannot contains #.', True)

            fixed_string = InstructionsParser.fix_string(arg_value)
            return Symbol(DataTypes.STRING, fixed_string)
        elif arg_type == 'type':
            if arg_value == 'int':
                return Type(int)
            elif arg_value == 'string':
                return Type(str)
            elif arg_value == 'bool':
                return Type(bool)
            elif arg_value == 'float':
                return Type(float)
            else:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Unknown type value. ({})'.format(arg_value), True)
        elif arg_type == 'float':
            try:
                return Symbol(DataTypes.FLOAT, float.fromhex(arg_value))
            except Exception:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid format of operand.')
        else:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Unknown argument type. ({})'.format(arg_type), True)

    @staticmethod
    def validate_scope(scope: str):
        """ Kontrola platnosti ramce. """

        if scope != Frames.GLOBAL.value and scope != Frames.LOCAL.value and \
                scope != Frames.TEMPORARY.value:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Invalid scope. ({})'.format(scope), True)

    @staticmethod
    def validate_variable_name(name: str, is_label: bool = False):
        """ Kontrola spravnosti nazvu promenne, nebo navesti. """

        if re.compile(r"^[_\-$&%*!?a-zA-Z][_\-$&%*!?a-zA-Z0-9]*$").match(name)\
                is None:
            exit_app(exitCodes.INVALID_XML_STRUCT,
                     'Invalid {} name. ({})'.format(
                         'label' if is_label else 'variable', name), True)

    @staticmethod
    def fix_string(value: str) -> str:
        """ Osetreni retezce. Zpracovani escape sekvenci. """

        result: List[str] = list()

        splitedParts = value.split('\\')
        result.append(splitedParts[0])

        number_regex = re.compile("\\d{3}")

        for item in splitedParts[1:]:
            number_matched = number_regex.match(item[:3])

            if not number_matched:
                exit_app(exitCodes.INVALID_XML_STRUCT,
                         'Invalid hexadecimal escape.', True)

            result.append(chr(int(item[:3])))
            result.append(item[3:])

        return str().join(result)
