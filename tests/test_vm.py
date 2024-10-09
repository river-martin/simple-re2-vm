import pytest
from simple_re2 import vm, assembler

def test_run():
    with open("a_or_eps_or_b.re2asm") as f:
        prog = assembler.assemble(f)
    vm.run(prog, "ab".encode('utf-8'))

if __name__ == '__main__':
    pytest.main()