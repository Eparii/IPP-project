import sys
from sys import stdin
from helper import exit_app
from enums import exitCodes
from argparse import ArgumentParser
from instruction_parser import InstructionsParser
from program import Program
from stats import Stats


def argument_parse_error(message: str):
    exit_app(exitCodes.INVALID_ARGUMENTS, message)


if '--help' in sys.argv and len(sys.argv) > 2:
    exit_app(exitCodes.INVALID_ARGUMENTS,
             '--help cannot be combined with another parameters')

parser = ArgumentParser()
parser.add_argument('--source', type=str)
parser.add_argument('--input', type=str)
parser.add_argument('--stats', type=str)
parser.add_argument('--insts', default=False, action='store_true')
parser.add_argument('--vars', default=False, action='store_true')
parser.error = argument_parse_error

arguments = parser.parse_args()

if arguments.source is None and arguments.input is None:
    exit_app(exitCodes.INVALID_ARGUMENTS,
             '--source or --input or both parameters are required.')

xml_file = stdin
try:
    if arguments.source is not None:
        xml_file = open(arguments.source, 'r')
except Exception:
    exit_app(exitCodes.CANNOT_READ_FILE, 'Cannot open XML file.')

input_file = stdin
try:
    if arguments.input is not None:
        input_file = open(arguments.input, 'r')
except Exception:
    exit_app(exitCodes.CANNOT_READ_FILE, 'Cannot open inputs file')

stats: Stats = None
if arguments.stats is not None:
    try:
        if not arguments.insts and not arguments.vars:
            exit_app(exitCodes.INVALID_ARGUMENTS,
                     'For stats parameter is required minimal ' +
                     'one of --vars or --insts parameters.')

        stats_file = open(arguments.stats, 'w+')
        stats = Stats(stats_file, arguments.insts, arguments.vars)
    except Exception as e:
        print(e)
        exit_app(exitCodes.CANNOT_WRITE_FILE, 'Cannot open stats file')

instructions = InstructionsParser.parse_file(xml_file)
program = Program(list(instructions.values()), input_file, stats)
program.run()

if stats is not None:
    stats.save()
    stats_file.close()

exit(int(program.exit_code))
