# Python3 Parser

## The pgen module

### startup
Python3 use a tool named pgen to generate its Grammar Automaton, let's do this ourselves, enter the Parser directory, and type the following command, the correspondence files will be generated.

```python3 -m pgen ../Grammar/Grammar ../Grammar/Tokens graminit.h graminit.c --verbose --graph graph ```

### how to debug pgen
To see how it works, we need to use a debugger (pdb), change the \_\_main\_\_.py file to use pdb, you can also modify any python file, adding pdb.set_trace(), so pdb will set the break points and will stop there when it hits the break point.

```python
 42 if __name__ == "__main__":
 43     import pdb
 44     pdb.set_trace()
 45     main()
 ```

pgen.py use a Class ParserGenerator to parse the Grammar file, generate the (token_name, token_num pairs) and (token_operator, token_name pairs)

```python
class ParserGenerator(object):
    def __init__(self, grammar_file, token_file, verbose=False, graph_file=None):
        with open(grammar_file) as f:
            self.grammar = f.read()
        with open(token_file) as tok_file:
            token_lines = tok_file.readlines()
        self.tokens = dict(token.generate_tokens(token_lines))
        self.opmap = dict(token.generate_opmap(token_lines))
        # Manually add <> so it does not collide with !=
        self.opmap["<>"] = "NOTEQUAL"
        self.verbose = verbose
        self.filename = grammar_file
        self.graph_file = graph_file
        self.dfas, self.startsymbol = self.create_dfas()
        self.first = {}  # map from symbol name to set of tokens
        self.calculate_first_sets()
```

The tokens and opmap look like this:
```
(Pdb) p self.tokens
{'ENDMARKER': 0, 'NAME': 1, 'NUMBER': 2, 'STRING': 3, 'NEWLINE': 4, 'INDENT': 5, 'DEDENT': 6, 'LPAR': 7, 'RPAR': 8, 'LSQB': 9, 'RSQB': 10, 'COLON': 11, 'COMMA': 12, 'SEMI': 13, 'PLUS': 14, 'MINUS': 15, 'STAR': 16, 'SLASH': 17, 'VBAR': 18, 'AMPER': 19, 'LESS': 20, 'GREATER': 21, 'EQUAL': 22, 'DOT': 23, 'PERCENT': 24, 'LBRACE': 25, 'RBRACE': 26, 'EQEQUAL': 27, 'NOTEQUAL': 28, 'LESSEQUAL': 29, 'GREATEREQUAL': 30, 'TILDE': 31, 'CIRCUMFLEX': 32, 'LEFTSHIFT': 33, 'RIGHTSHIFT': 34, 'DOUBLESTAR': 35, 'PLUSEQUAL': 36, 'MINEQUAL': 37, 'STAREQUAL': 38, 'SLASHEQUAL': 39, 'PERCENTEQUAL': 40, 'AMPEREQUAL': 41, 'VBAREQUAL': 42, 'CIRCUMFLEXEQUAL': 43, 'LEFTSHIFTEQUAL': 44, 'RIGHTSHIFTEQUAL': 45, 'DOUBLESTAREQUAL': 46, 'DOUBLESLASH': 47, 'DOUBLESLASHEQUAL': 48, 'AT': 49, 'ATEQUAL': 50, 'RARROW': 51, 'ELLIPSIS': 52, 'COLONEQUAL': 53, 'OP': 54, 'AWAIT': 55, 'ASYNC': 56, 'TYPE_IGNORE': 57, 'TYPE_COMMENT': 58, 'ERRORTOKEN': 59, 'COMMENT': 60, 'NL': 61, 'ENCODING': 62, 'N_TOKENS': 63, 'NT_OFFSET': 256}
```

```
(Pdb) p self.opmap
{'(': 'LPAR', ')': 'RPAR', '[': 'LSQB', ']': 'RSQB', ':': 'COLON', ',': 'COMMA', ';': 'SEMI', '+': 'PLUS', '-': 'MINUS', '*': 'STAR', '/': 'SLASH', '|': 'VBAR', '&': 'AMPER', '<': 'LESS', '>': 'GREATER', '=': 'EQUAL', '.': 'DOT', '%': 'PERCENT', '{': 'LBRACE', '}': 'RBRACE', '==': 'EQEQUAL', '!=': 'NOTEQUAL', '<=': 'LESSEQUAL', '>=': 'GREATEREQUAL', '~': 'TILDE', '^': 'CIRCUMFLEX', '<<': 'LEFTSHIFT', '>>': 'RIGHTSHIFT', '**': 'DOUBLESTAR', '+=': 'PLUSEQUAL', '-=': 'MINEQUAL', '*=': 'STAREQUAL', '/=': 'SLASHEQUAL', '%=': 'PERCENTEQUAL', '&=': 'AMPEREQUAL', '|=': 'VBAREQUAL', '^=': 'CIRCUMFLEXEQUAL', '<<=': 'LEFTSHIFTEQUAL', '>>=': 'RIGHTSHIFTEQUAL', '**=': 'DOUBLESTAREQUAL', '//': 'DOUBLESLASH', '//=': 'DOUBLESLASHEQUAL', '@': 'AT', '@=': 'ATEQUAL', '->': 'RARROW', '...': 'ELLIPSIS', ':=': 'COLONEQUAL', '<>': 'NOTEQUAL'}
```

then Python use a library named tokenizer.py to generate the Tokens. The token name will match the name of self.tokens list.
Before moving on, we can make a simple calculator using the tokenizer.py. See calc.py



then ParserGenerator will create DFA for the parser, but before creating the DFA, ParserGenerator will create NFA using the syntax in the grammar file, if --verbose is set, ParserGenerator will dump the NFA to the console.

