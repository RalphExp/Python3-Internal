#!/usr/bin/python3

# This file shows how to use NFA to create a regular 
# expression engine.

class NFAArc(object):
    """ NFAArc represent the arcs connecting to the nextN States,
    value is diffent according to different type. if type is 
        1) EPSILON_TYPE, value is None
        2) CHAR_TYPE, value is a single character
        3) CLASS_TYPE, value is a set
        4) LPAR_TYPE, value is the group number
        5) RPAR_TYPE, value is the group number
    """
    EPSILON_TYPE = 0
    CHAR_TYPE = 1
    CLASS_TYPE = 2
    LPAR_TYPE = 3
    RPAR_TYPE = 4

    def __init__(self, target, value, type_):
        self._type = type_
        self._value = value
        self._target = target

    @property
    def arctype(self):
        return self.type_
    
    @property
    def value(self):
        return self.value_
    
    @property
    def target(self):
        return self._target
    
    @target.setter
    def target(self, tar):
        self._target = tar


class NFAState(object):
    def __init__(self):
        self._index = None
        self._arcs = []
        self._accept = False

    @property
    def accept(self):
        return self._accept
    
    @accept.setter
    def accept(self, val:bool):
        self.accept = val

    def addArc(self, target, value, type_):
        self._arcs.append(NFAArc(target, value, type_))

    def __eq__(self, state):
        # __eq__ can be used to simplify the states
        if len(self._arcs) != len(state._arcs):
            return False
        
        for i in range(len(self._arcs)):
            if self._arcs[i] != state._arcs[i]:
                return False
        return True

    
class NFA(object):
    def __init__(self):
        self._start = -1
        self._end = -1
        self._nodes = []
    
    def allocState(self) -> NFAState:
        state = NFAState()
        state._index = len(self._nodes)
        self._nodes.append(state)
        return state


class Thread(object):
    pass


class Group(object):
    pass


class RegExp(object):
    """ A simple regular expression using NFA for matching
    note that is this different from pgen's NFA, we want to 
    make it more intuitive
    """
    def __init__(self, pattern):
        self._pat = pattern
        self._index = 0
        self._compiled = False
        self._nfa = compile()
        self._compiled = True

    def concat(self) -> tuple[NFAState]:
        """ concat single character,class,groups,closure,star,... etc.
        """
        s = self._pat
        a = None

        while self._index < len(s):
            if s[self._index] == '(':
                self._index += 1
                a, z = self.alternate()
                if s[self._index] != ')':
                    raise Exception('unmatch parenthesis')
                aa = self._nfa.allocState()
                zz = self._nfa.allocState()
                
    def alternate(self) -> tuple[NFAState]:
        """ alternate split s into different section delimit by '|'
        """
        s = self._pat
        a, z = self.concat()
        
        if self._index == len(s) or s[self._index] != '|':
            return a, z
 
        aa = self._nfa.allocState()
        zz = self._nfa.allocState()

        while True:
            aa.addArc(a, None, NFAArc.EPSILON_TYPE)
            z.addArc(zz, None, NFAArc.EPSILON_TYPE)
            
            if self._index < len(s) and s[self._index] == '|':
                break

            self._index += 1
            a, z = self.concat(s)
        return aa, zz

    
    def compile(self, s:str) -> NFA:
        start, end = self.alternate(s)
        if self._index != len(s):
            raise Exception(f'Unexpected character: {s[self._index]} as position {self._index}')

        end.accept = True
        return NFA(start, end)

    def match(text) -> Group or None:
        pass

if __name__ == '__main__':
    pass