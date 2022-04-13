from typing import IO, Dict, List
from models import Symbol
from sys import argv


class Stats():
    """ Rozsireni statistik """

    def __init__(self, file: IO, insts_enabled: bool, vars_enabled: bool):
        self.file = file
        self.insts_count = 0
        self.vars_count = 0
        self.insts_enabled = insts_enabled
        self.vars_enabled = vars_enabled

    def increment_insts(self):
        if not self.insts_enabled:
            return

        self.insts_count += 1

    def increment_vars(self, gf: Dict[str, Symbol],
                       lf_stack: List[Dict[str, Symbol]],
                       tf: Dict[str, Symbol]):
        if not self.vars_enabled:
            return

        cnt = len(gf) + (len(tf) if tf is not None else 0) + \
            (len(lf_stack[-1]) if len(lf_stack) > 0 else 0)

        if cnt > self.vars_count:
            self.vars_count = cnt

    def save(self):
        for arg in argv:
            if arg == '--insts':
                self.file.write('{}\n'.format(self.insts_count))
            elif arg == '--vars':
                self.file.write('{}\n'.format(self.vars_count))
