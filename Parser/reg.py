#!/usr/bin/python3

# This file shows how to use NFA to create a regular 
# expression engine.

class Token(object):
    END = 0
    ALTER = 1
    LPAREN = 2
    RPAREN = 3
    STAR = 4
    STAR2 = 5
    PLUS = 6
    PLUS2 = 7
    QUESTION = 8
    CHAR = 9
    LBRACK = 10
    RBRACK = 11
    BACKSLASH = 12
    LBRACE = 13
    RBRACE = 14

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

class Tokenizer(object):

    def __init__(self, pattern):
        self._pat = pattern
        self._cache = None
        self._index = 0

        self._token_dict = {
            '|': Token(Token.ALTER),
            '(': Token(Token.LPAREN),
            ')': Token(Token.RPAREN),
            '[': Token(Token.LBRACK),
            ']': Token(Token.RBRACK),
            '{': Token(Token.LBRACE),
            '}': Token(Token.RBRACE),
            '*': Token(Token.STAR),
            '+': Token(Token.PLUS),
            '?': Token(Token.QUESTION),
        }

        self._token2_dict = {
            '*?': Token(Token.STAR2),
            '+?': Token(Token.PLUS2)
        }

    def putToken(self, token):
        assert(self._cache is None)
        self._cache = token

    def getToken(self):
        if self._cache:
            token = self._cache 
            self._cache = None
            return token
        
        if self._index >= len(self._pat):
            return Token(Token.END, None)

        s = self._pat
        token = self._token2_dict.get(s[self._index:self._index+2], None) 
        if token != None:
            self._index += 2
            return token
        
        token = self._token_dict.get(s[self._index], None)
        if token != None:
            self._index += 1
            return token
        
        token = Token(Token.CHAR, s[self._index])
        self._index += 1
        return token

class NFAArc(object):
    """ NFAArc represent the arcs connecting to the nextN States,
    value is diffent according to different type. if type is 
        1) EPSILON_TYPE, value is None
        2) CHAR_TYPE, value is a single character
        3) CLASS_TYPE, value is a set
        4) LPAR_TYPE, value is the group number
        5) RPAR_TYPE, value is the group number
    """
    EPSILON = 0
    CHAR = 1
    CLASS = 2
    LGROUP = 3
    RGROUP = 4

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
    def accept(self, value:bool):
        self.accept = value

    def addArc(self, target, value, type_):
        self._arcs.append(NFAArc(target, value, type_))

    def copy(self, state2):
        self._arcs = state2._arc
        self.accept = state2.accept
        state2._arc = None

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
        self._groups = 0
    
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
        self._tokenizer = Tokenizer(self._pat)

    def getToken(self):
        return self._tokenizer.getToken()
    
    def putToken(self, token):
        return self._tokenizer.putToken(token)

    def concat(self) -> tuple[NFAState]:
        pass

    def group(self) -> tuple[NFAState]:
        """ concat single character,class,groups,closure,star,... etc.
        """
        s = self._pat
        aa = None # NFA State to return
        zz = None # NFA State to return

        # !!! invariant feature: len(zz._arc) == 0
        while True:
            token = self.getToken()
            if token.type == Token.LPAREN:
                self._nfa.groups += 1
                self._index += 1
                group = self._nfa.groups
                start, end = self.alternate()

                token = self.getToken()
                if token.type != Token.RPAREN:
                    raise Exception('unmatch parenthesis')
                
                if aa == None:
                    assert(zz == None)
                    aa = self._nfa.allocState()
                    zz = self._nfa.allocState()
                    aa.addArc(start, group, NFAArc.LGROUP)
                    end.addArc(zz, group, NFAArc.LGROUP)
                else:
                    zz.addArc(start, group, NFAArc.LGROUP)
                    z = self._nfa.allocState()
                    end.addArc(z, group, NFAArc.LGROUP)
                    zz = z
            else:
                a, z = self.concat()
                token = self.getToken()
                if token.type == Token.STAR:
                    pass
                elif token.type == Token.STAR2:
                    pass
                elif token.type == Token.PLUS:
                    pass
                elif token.type == Token.PLUS2:
                    pass
                elif token.type == Token.QUESTION:
                    pass
                else: # don't recognize this token, return
                    zz.copy(a)
                    zz = z
                    return aa, zz
                
    def alternate(self) -> tuple[NFAState]:
        """ alternate split s into different section delimit by '|'
        """
        s = self._pat
        a, z = self.group()
        
        token = self.getToken()
        if token.value != Token.ALTER:
            self.putToken(token)
            return a, z
 
        aa = self._nfa.allocState()
        zz = self._nfa.allocState()

        while True:
            aa.addArc(a, None, NFAArc.EPSILON)
            z.addArc(zz, None, NFAArc.EPSILON)
            token = self.getToken()
            if token.value != Token.ALTER:
                self.putToken(token)
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