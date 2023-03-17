# Chapter1 Parser

### play with pgen

Python3 use a tool named pgen to generate its Grammar Automaton, let's do this ourselves, enter the Parser directory, and type the following command, the correspondence files will be generated.

```python3 -m pgen ../Grammar/Grammar ../Grammar/Tokens graminit.h graminit.c --graph graph
```

To see how it works, we need to use a debugger (pdb), let's do it again

```pdb pgen/__main__.py ../Grammar/Grammar ../Grammar/Tokens graminit.h graminit.c --graph graph
```

