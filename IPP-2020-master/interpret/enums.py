from enum import IntEnum, Enum


class exitCodes(IntEnum):
    """ Stavove kody, se kterymi muze byt interpret ukoncen. """

    INVALID_ARGUMENTS = 10         # Neplatne parametry prikazove radky.
    CANNOT_READ_FILE = 11          # Nelze otevrit vstupni soubor.
    CANNOT_WRITE_FILE = 12         # Nelze otevrit vystupni soubor.
    INVALID_XML_FORMAT = 31        # Chybny format XML. (Dle standardu)
    INVALID_XML_STRUCT = 32        # Chybna data v XML.
    SEMANTIC_ERROR = 52            # Semanticka chyba.
    INVALID_DATA_TYPE = 53         # Neplatny datovy typ
    UNDEFINED_VARIABLE = 54        # Nedefinovana promenna.
    INVALID_FRAME = 55             # Neplatny ramec.
    UNDEFINED_VALUE = 56           # Nedefinovana hodnota v definovane promenne
    INVALID_OPERAND_VALUE = 57     # Neplatna hodnota v operandech.
    INVALID_STRING_OPERATION = 58   # Neplatny retezec.


class ArgumentTypes(Enum):
    """ Typy operandu. """

    VARIABLE = 'var'   # Promenna
    SYMBOL = 'symb'    # Symbol (promenna, nebo konstanta)
    LABEL = 'label'    # Navesti
    TYPE = 'type'      # Typ


class Frames(Enum):
    """ Datove ramce. """

    GLOBAL = 'GF'      # Globalni (promenne) ramec.
    LOCAL = 'LF'       # Lokalni ramec.
    TEMPORARY = 'TF'   # Docasny ramec.


class DataTypes(Enum):
    """ Podporovane datove typy. """

    NIL = 'nil'            # Nil (null)
    INT = 'int'            # Celociselna hodnota (integer)
    BOOL = 'bool'          # Pravdivostni hodnota {true, false}
    STRING = 'string'      # Retezec
    FLOAT = 'float'        # Cislo s plovouci desetinnou carkou.
