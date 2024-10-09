import collections


class Instruction:
    """Base class for all instructions"""

    def __init__(self, indicator: str, kw: str):
        self.indicator = indicator
        self.kw = kw


type ip_type = int
type byte = int


class InstrByteRange(Instruction):
    """Instruction that consumes a byte from the input"""

    def __init__(
        self, indicator: str, kw: str, min: byte, max: byte, hint: int, out: int
    ):
        super().__init__(indicator, kw)
        self.min, self.max = min, max
        self.hint = hint
        self.out = out


class InstrMatch(Instruction):
    """Instruction that triggers a match"""

    def __init__(self, indicator: str, kw: str):
        super().__init__(indicator, kw)


class InstrNop(Instruction):
    """Instruction used for transitions without actions"""

    def __init__(self, indicator: str, kw: str, out: int):
        super().__init__(indicator, kw)
        self.out = out


class InstrCapture(Instruction):
    """Instruction that saves the current position in the input"""

    def __init__(self, indicator: str, kw: str, sp_buf_index: int, out: int):
        super().__init__(indicator, kw)
        self.sp_buf_index = sp_buf_index
        self.out = out


class WorkQueue:
    """An ordered set of instructions to be executed when in a given DFA state."""

    def __init__(self):
        # Used to check if an instruction is already in the queue
        self.ordered_dict = collections.OrderedDict()
        self.contains_InstrMatch = False

    def add(self, ip, instrs: list[Instruction]):
        """
        Add `ip` to the work queue, as well all instructions reachable from `ip`, via empty transitions.

        Args:
            ip (int): The instruction pointer to add to the work queue
            instrs (list[Instruction]): The list of all instructions in the program
                (used to determine which instructions are reachable from ip)
        """
        ip_stack = []
        while ip is not None or len(ip_stack) > 0:
            if ip is None:
                ip = ip_stack.pop()
            instr = instrs[ip]
            if ip in self.ordered_dict.keys():
                # We don't want to add duplicates
                ip = None
                continue
            else:
                # Add the ip to the work queue if it is the head of its sublist
                # This is the case iff the previous instruction in the program is the last in *its* sublist
                if instrs[ip - 1].indicator == ".":
                    self.ordered_dict[ip] = instr
                match instr:
                    case InstrCapture() | InstrNop():
                        # Captures are treated as no-ops by the DFA because it does not track submatch boundaries
                        if instr.indicator == "+":
                            ip_stack.append(ip + 1)
                        ip = instr.out
                    case InstrByteRange():
                        if instr.indicator == ".":
                            # We only follow empty transitions here, and we are at the end of the sublist
                            ip = None
                            continue
                        else:
                            assert instr.indicator == "+"
                            # The VM should go to the next instruction in the sublist if the byte is out of range
                            # (i.e. if the `ByteRange` instruction fails to consume the current byte)
                            ip = ip + 1
                    case InstrMatch():
                        assert instr.indicator == "."
                        # NOTE: The line below fixes a bug in the actual C++ implementation of RE2
                        self.contains_InstrMatch = True
                        ip = None
                        continue
                    case _:
                        raise ValueError(
                            f"Unknown instruction type: {type(instrs[ip])}"
                        )

    def to_list(self) -> list[ip_type]:
        return list(self.ordered_dict.keys())

    def clear(self):
        self.contains_InstrMatch = False
        self.ordered_dict.clear()

    def is_empty(self) -> bool:
        return len(self.ordered_dict) == 0


def _run_on_byte(
    instrs: list[Instruction], clist: list[ip_type], next_q: WorkQueue, c: byte
):
    i = 0  # index into clist
    while i < len(clist):
        ip = clist[i]
        instr = instrs[ip]
        match instr:
            case InstrNop() | InstrCapture():
                # Captures are treated as no-ops.
                # no-op transitions are followed in WorkQueue.add()
                pass
            case InstrByteRange():
                if instr.min <= c <= instr.max:
                    # When the DFA is in the next state, it should
                    # continue execution along the path that consumed the byte
                    next_q.add(instr.out, instrs)
                    # We can skip over the rest of the instructions in the current sublist
                    if instr.hint > 0:
                        # The hint tells us where the first instruction in the next sublist is
                        i += (
                            instr.hint - 1
                        )  # -1 because we increment i at the end of the loop
                    else:
                        # We have to find the last instruction in the current sublist, since we don't have a hint
                        while instr.indicator == "+":
                            i += 1
                            instr = instrs[clist[i]]
            case InstrMatch():
                # We only care about the first match
                return
            case _:
                raise ValueError(f"Unknown instruction {instr}")
        i += 1


from simple_re2.vm import *


def run(prog: list[Instruction], input: bytes):
    """
    Run the regex program `prog`.

    Args:
        prog (list[Instruction]): The regex program to run
        input (bytes): The UTF-8 encoded input string
    Returns:
        int | None: The end of the last match in the input, or None if no match was found
    """
    # Add start instruction at index 0
    prog = [InstrNop(".", "nop", 1)] + prog
    q = WorkQueue()
    next_q = WorkQueue()
    q.add(0, prog)
    sp = 0
    last_match_sp = sp if q.contains_InstrMatch else None
    while sp < len(input) and not q.is_empty():
        _run_on_byte(prog, q.to_list(), next_q, input[sp])
        sp += 1
        if next_q.contains_InstrMatch:
            last_match_sp = sp
        # Swap the queues
        q, next_q = next_q, q
        next_q.clear()
    return last_match_sp


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a regex program on an input string"
    )
    parser.add_argument(
        "prog_file", type=argparse.FileType("r"), help="The regex program file"
    )
    parser.add_argument("input", type=str, help="The input string")
    args = parser.parse_args()
    import simple_re2.assembler as assembler

    prog = assembler.assemble(args.prog_file)
    args.prog_file.close()
    input_bytes = args.input.encode("utf-8")
    match_end = run(prog, input_bytes)
    if match_end is not None:
        print(f"Match ends at byte {match_end}")
    else:
        print("No match found")


if __name__ == "__main__":
    main()
