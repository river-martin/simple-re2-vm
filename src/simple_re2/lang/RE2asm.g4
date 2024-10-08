grammar RE2asm;

options {
	language = Python3;
}

// Parser rules

program: line+;

line: indicator (consumeByte | capture | nop | match);

// '+' means that the instruction on the next line is a part of the current instruction's list
indicator: PLUS | DOT;

consumeByte: KW_BYTE byteRange hint TO lineNum;

byteRange: '[' low '-' high ']';

low
	returns[val]: hb = hexByte {$val = $hb.val};

high
	returns[val]: hb = hexByte {$val = $hb.val};

hexByte
	returns[val]:
	digit1 = hex_digit digit2 = hex_digit {$val = int($digit1.val + $digit2.val, 16)};

hex_digit
	returns[val]: NUMERIC_DIGIT | ALPHA_DIGIT;

hint
	returns[val]: uint;

lineNum
	returns[int val]: uint;

capture: KW_CAPTURE spBufIndex TO lineNum;

// Index into the string pointer buffer
spBufIndex: uint;

uint: NUMERIC_DIGIT+;

nop: KW_NOP TO lineNum;

match: KW_MATCH hint;

// Lexer rules

// Comment
COMMENT: ';' ~[\n]* -> skip;

// Whitespace
WS: [ \t\r\n]+ -> skip;

KW_NOP: 'nop';

KW_MATCH: 'match!';

KW_BYTE: 'byte';

KW_CAPTURE: 'capture';

DOT: '.';

PLUS: '+';

TO: '->';

// Used in hexadecimal digits
ALPHA_DIGIT: [a-fA-F];

NUMERIC_DIGIT: [0-9];