class Instruction:
    """An instruction for the regex virtual machine (VM)."""

    def __init__(self, op: str, args: list[str]):
        self.op = op
        self.args = args

    def __repr__(self):
        return f"{self.op} {', '.join(self.args)}".strip()


class Program(list):
    def __init__(self, instructions: list[Instruction]):
        super().__init__()

    def __repr__(self) -> str:
        return "\n".join([str(instr) for instr in self])

    def __str__(self) -> str:
        return self.__repr__()