import re
import simple_re2.vm as vm


class EmptyLineError(Exception):
    pass


def expect(
    tok_str: str,
    rule_name: str,
):
    """Check if the token string matches the rule name.

    Args:
        tok_str (str): The token string to check.
        rule_name (str): The name of the rule to check against.
    Returns:
        re.Match: The match object.
    Raises:
        ValueError: If the token string does not match the rule name.
    """
    HEX_BYTE = r"[\da-f]{2}"
    patterns = {
        "INDICATOR": r"[+.]",
        "KEYWORD": r"byte|match!|nop|capture",
        "BYTE_RANGE": rf"\[(?P<min>{HEX_BYTE})-(?P<max>{HEX_BYTE})\]",
        "HINT": r"\d+",
        "TO": r"->",
        "OUT": r"\d+",
        "SP_BUF_INDEX": r"\d+",
    }
    m = re.match(patterns[rule_name], tok_str)
    if not m:
        raise ValueError(
            f"Expected {rule_name} (`{patterns[rule_name]}`), got '{tok_str}'"
        )
    return m


def parse_instruction(line: str) -> vm.Instruction:
    import re

    # Remove comments
    line = re.sub(r"(.*);.*", r"\1", line)
    line = line.strip()
    if line == "":
        raise EmptyLineError()

    token_strs = iter(line.split())

    indicator = next(token_strs)
    expect(indicator, rule_name="INDICATOR")
    kw = next(token_strs)
    expect(kw, rule_name="KEYWORD")
    match kw:
        case "byte":
            byte_range_str = next(token_strs)
            m = expect(byte_range_str, rule_name="BYTE_RANGE")
            min, max = m.group("min"), m.group("max")

            hint = next(token_strs)
            expect(hint, "HINT")

            expect(next(token_strs), "TO")

            out = next(token_strs)
            expect(out, "OUT")

            return vm.InstrByteRange(
                indicator, kw, int(min, base=16), int(max, base=16), int(hint), int(out)
            )
        case "match!":
            return vm.InstrMatch(indicator, kw)
        case "nop":
            expect(next(token_strs), rule_name="TO")

            out = next(token_strs)
            expect(out, rule_name="OUT")

            return vm.InstrNop(indicator, kw, int(out))
        case "capture":
            sp_buf_index = next(token_strs)
            expect(sp_buf_index, rule_name="SP_BUF_INDEX")

            expect(next(token_strs), rule_name="TO")
            out = next(token_strs)
            expect(out, rule_name="OUT")
            return vm.InstrCapture(indicator, kw, int(sp_buf_index), int(out))
        case _:
            raise ValueError(f"Unknown keyword {kw}")


def assemble(regex_prog_file):
    """Create a list of `Instruction` objects from a regex program file."""
    instructions = list[vm.Instruction]()
    for line in regex_prog_file:
        try:
            instructions.append(parse_instruction(line))
        except EmptyLineError as e:
            pass
    return instructions
