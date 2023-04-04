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
 43     def _parse_rhs(self):
 44         # rhs: items ('|' items)*
 45         a, z = self._parse_items()
 46         if self.value != "|":
 47             return a, z
 48         else:
 49             aa = NFAState(self._current_rule_name)
 50             zz = NFAState(self._current_rule_name)
 51             while True:
 52                 # Allow to transit directly to the previous state and connect the end of the
 53                 # previous state to the end of the current one, effectively allowing to skip
 54                 # the current state.
 55                 aa.add_arc(a)
 56                 z.add_arc(zz)
 57                 if self.value != "|":
 58                     break
 59 
 60                 self._gettoken()
 61                 a, z = self._parse_items()
 62             return aa, zz
   ```

### NFA
Now come back to the method create_dfas, because the --verbose parameter, line 156 will dump the NFA generate by GrammarParser

```python
149     def create_dfas(self):
150         rule_to_dfas = collections.OrderedDict()
151         start_nonterminal = None
152 
153         for nfa in GrammarParser(self.grammar).parse():
154             if self.verbose:
155                 print("Dump of NFA for", nfa.name)
156                 nfa.dump()
157             if self.graph_file is not None:
158                 nfa.dump_graph(self.graph_file.write)
159             dfa = DFA.from_nfa(nfa)
160             if self.verbose:
161                 print("Dump of DFA for", dfa.name)
162                 dfa.dump()
163             dfa.simplify()
164             if self.graph_file is not None:
165                 dfa.dump_graph(self.graph_file.write)
166             rule_to_dfas[dfa.name] = dfa
167 
168             if start_nonterminal is None:
169                 start_nonterminal = dfa.name
170 
171         return rule_to_dfas, start_nonterminal
```

For the rule ```single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE```
the output looks like the following, note that State 0 use three epsilon transition to reach state 1, 2, 3 respectively, state 6(compound_stmt) also use a epsilon transition to goto state 8 (NEWLINE). The rest of the rules are handled similarily, I saved them in the **automaton.txt**. For a interesting application of NFA see reg.py, a simple regular expression engine.


**NFA of single_input**
```
  State 0 
    -> 1
    -> 2
    -> 3
  State 1 
    NEWLINE -> 4
  State 2 
    simple_stmt -> 5
  State 3 
    compound_stmt -> 6
  State 4 
    -> 7
  State 5 
    -> 7
  State 6 
    -> 8
  State 7 (final)
  State 8 
    NEWLINE -> 9
  State 9 
    -> 7
```

then pgen use ```DFA.from_nfa(nfa)``` to convert the NFA into DFA, the idea is simple:
* 1 compute the closure state of the start state
* 2 put the closure state into a list
* 3 for every closure state in the list, find all the different labels that will lead to the next state, also compute the closure state of these states
* 4 from the above computation, if the closure state is not in the list, put it into the list
* 5 from the current closure state, for each label, add an arc to the new closure state computed in step 3
* 6 repeat step 3 until all the closure state in the list have been processed.

```python
    @classmethod
    def from_nfa(cls, nfa):
        # step1: 
        add_closure(nfa.start, base_nfa_set)
        
        # step2:
        states = [DFAState(nfa.name, base_nfa_set, nfa.end)]
        
        # step3:
        for state in states:
            arcs = {}
            for nfa_state in state.nfa_set:
                for nfa_arc in nfa_state.arcs:
                    if nfa_arc.label is not None:
                        nfa_set = arcs.setdefault(nfa_arc.label, set())
                        add_closure(nfa_arc.target, nfa_set)

            # step3: different labels lead to the new closure (nfa_set)
            for label, nfa_set in sorted(arcs.items()):
                for exisisting_state in states:
                    if exisisting_state.nfa_set == nfa_set:
                        next_state = exisisting_state
                        break
                else:
                    next_state = DFAState(nfa.name, nfa_set, nfa.end)
                    # step4: add new state to list
                    states.append(next_state)

                # step5: add new arc
                state.add_arc(next_state, label)

        return cls(nfa.name, states)
```

DFA also use a simplify method to reduce the number DFAState, simplify compares every pair of DFAState, if they are *equal*, they can be combined together. Equal means the \_\_eq\_\_ function returns True.

* The two state must be both the accept state or not the accept state.
* The two state must have the same number of arcs.
* For each arc in state1 there must be an arc in state2 that these 2 arcs have the same label and the same target.

``` python
class DFAState(object):
    ...
    
    def __eq__(self, other):
        # The nfa_set does not matter for equality
        assert isinstance(other, DFAState)
        if self.is_final != other.is_final:
            return False
        # We cannot just return self.arcs == other.arcs because that
        # would invoke this method recursively if there are any cycles.
        if len(self.arcs) != len(other.arcs):
            return False
        for label, next_ in self.arcs.items():
            if next_ is not other.arcs.get(label):
                return False
        return True
```

### Grammar file for C
After creating and simplifing the DFA, pgen will create a graminit.h and graminit.c file for the C parser to consume.

It does the following step:
* create the firstset for every name(non-terminated symbol)
``` python
    def calculate_first_sets_for_rule(self, name):
        dfa = self.dfas[name]
        self.first[name] = None  # dummy to detect left recursion
        state = dfa.states[0]
        totalset = set()
        overlapcheck = {}

        # for every state can be reached from state[0]
        # calculate their first set and add them together as our first set
        for label, next in state.arcs.items():
            if label in self.dfas:
                # this is a non-terminal symbol
                # calculate its first set
                if label in self.first:
                    fset = self.first[label]
                    if fset is None:
                        raise ValueError("recursion for rule %r" % name)
                else:
                    self.calculate_first_sets_for_rule(label)
                    fset = self.first[label]
                # add to our first set
                totalset.update(fset)
                overlapcheck[label] = fset
            else:
                # this is an terminal symbol (TOKEN), add it directly
                totalset.add(label)
                overlapcheck[label] = {label}
        inverse = {}
        for label, itsfirst in overlapcheck.items():
            for symbol in itsfirst:
                if symbol in inverse:
                    raise ValueError(
                        "rule %s is ambiguous; %s is in the"
                        " first sets of %s as well as %s"
                        % (name, symbol, label, inverse[symbol])
                    )
                inverse[symbol] = label
        self.first[name] = totalset
```