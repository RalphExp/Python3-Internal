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

pgen.py use a Class ParserGenerator **pgen.py** to parse the Grammar file, generate the (token_name, token_num pairs) and (token_operator, token_name pairs)

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



then ParserGenerator will create DFA for the parser, but before creating the DFA, ParserGenerator will create NFA using the syntax in the grammar file. **metaparser.py**

### Grammar File
This is a snippet of the grammar file:
```
single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
file_input: (NEWLINE | stmt)* ENDMARKER
eval_input: testlist NEWLINE* ENDMARKER

decorator: '@' namedexpr_test NEWLINE
decorators: decorator+
decorated: decorators (classdef | funcdef | async_funcdef)

async_funcdef: ASYNC funcdef
funcdef: 'def' NAME parameters ['->' test] ':' [TYPE_COMMENT] func_body_suite

parameters: '(' [typedargslist] ')'
```

every rule has the form ```NAME ':' rhs NEWLINE```

- ```NAME``` is the rule name, such as single_input, file_input, ... etc.
- ```rhs``` is "right hand side", which is composed of a series of TERMINAL and NON-TERMINAL symbol 

and every rule may contains several meta symbol, just like the regular expressions:
- ```|``` means alternative
- ```[``` and ```]``` means optional
- ```*``` means the content may repeat any times
- ```+``` means the content at least show up once

To parse these rules, pgen use a class **GrammarParser** (see *metaparser.py*) to do the job:
alternative has the lowest priority, so the method parse_rhs handles the alternative at the outmost level. The variable a means this is a **start state** and varible z means this is an **end state** of the automaton fragment, if the ```|``` symbol is found, it create a new state aa which will link to all the a variables, it will also create a new state zz, which is linked by all the z variables. The　_parse_items method acts as concatenation and the _parse_item handles the STAR and PLUS, finally the _parse_atom method handles the NAME and STRING.


```python
def _parse_rhs(self):
   # rhs: items ('|' items)*
   a, z = self._parse_items()
   if self.value != "|":
       return a, z
   else:
       aa = NFAState(self._current_rule_name)
       zz = NFAState(self._current_rule_name)
       while True:
           # Allow to transit directly to the previous state and connect the end of the
           # previous state to the end of the current one, effectively allowing to skip
           # the current state.
           aa.add_arc(a)
           z.add_arc(zz)
           if self.value != "|":
               break

           self._gettoken()
           a, z = self._parse_items()
       return aa, zz

def _parse_items(self):
     # items: item+
     a, b = self._parse_item()
     while self.type in (tokenize.NAME, tokenize.STRING) or self.value in ("(", "["):
         c, d = self._parse_item()
         # Allow a transition between the end of the previous state
         # and the beginning of the new one, connecting all the items
         # together. In this way we can only reach the end if we visit
         # all the items.
         b.add_arc(c)
         b = d
     return a, b

def _parse_item(self):
    # item: '[' rhs ']' | atom ['+' | '*']
    if self.value == "[":
        self._gettoken()
        a, z = self._parse_rhs()
        self._expect(tokenize.OP, "]")
        # Make a transition from the beginning to the end so it is possible to
        # advance for free to the next state of this item # without consuming
        # anything from the rhs.
        a.add_arc(z)
        return a, z
    else:
        a, z = self._parse_atom()
        value = self.value
        if value not in ("+", "*"):
            return a, z
        self._gettoken()
        z.add_arc(a)
        if value == "+":
            # Create a cycle to the beginning so we go back to the old state in this
            # item and repeat.
            return a, z
        else:
            # The end state is the same as the beginning, so we can cycle arbitrarily
            # and end in the beginning if necessary.
            return a, a

def _parse_atom(self):
    # atom: '(' rhs ')' | NAME | STRING
    if self.value == "(":
        self._gettoken()
        a, z = self._parse_rhs()
        self._expect(tokenize.OP, ")")
        return a, z
    elif self.type in (tokenize.NAME, tokenize.STRING):
        a = NFAState(self._current_rule_name)
        z = NFAState(self._current_rule_name)
        # We can transit to the next state only if we consume the value.
        a.add_arc(z, self.value)
        self._gettoken()
        return a, z
    else:
        self._raise_error(
            "expected (...) or NAME or STRING, got {} ({})",
            self._translation_table.get(self.type, self.type),
            self.value,
        )
   ```


