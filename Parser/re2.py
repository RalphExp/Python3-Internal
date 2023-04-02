#!/usr/bin/python3

# This file shows how to use NFA to construct a regular expression engine.

from __future__ import annotations

import pdb

class Token(object):
    END = 0
    ALTER = 1
    LPAREN = 2
    RPAREN = 3
    STAR = 4
    STAR2 = 5
    PLUS = 6
    PLUS2 = 7
    QUEST = 8
    QUEST2 = 9
    LBRACK = 10
    RBRACK = 11
    BACKSLASH = 12
    LBRACE = 13
    RBRACE = 14
    CHAR = 15

    def __init__(self, type, value, pos=None):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f'token: type = {self.type}, val = {self.value}, pos = {self.pos}'


class Tokenizer(object):
    def __init__(self, pattern):
        self._pat = pattern
        self._token = None
        self._index = 0
        self._token_dict = {
            '|': Token(Token.ALTER, '|'),
            '(': Token(Token.LPAREN, '('),
            ')': Token(Token.RPAREN, ')'),
            '[': Token(Token.LBRACK, '['),
            ']': Token(Token.RBRACK, ']'),
            '{': Token(Token.LBRACE, '{'),
            '}': Token(Token.RBRACE, '}'),
            '*': Token(Token.STAR, '*'),
            '+': Token(Token.PLUS, '+'),
            '?': Token(Token.QUEST, '?'),
        }
        self._token2_dict = {
            '*?': Token(Token.STAR2, '*?'),
            '+?': Token(Token.PLUS2, '+?'),
            '??': Token(Token.QUEST2, '??')
        }
        self.next()

    @property
    def index(self):
        return self._index

    @property
    def token(self):  
        return self._token
    
    def next(self):
        s = self._pat
        if self._index >= len(s):
            self._token = Token(Token.END, None, len(s))
            return self._token

        token = self._token2_dict.get(s[self._index:self._index+2], None)
        if token != None:
            token.pos = self._index
            self._index += 2
            self._token = token
            return token
        
        token = self._token_dict.get(s[self._index], None)
        if token != None:
            token.pos = self._index
            self._index += 1
            self._token = token
            return token
        
        token = Token(Token.CHAR, s[self._index], self._index)
        self._index += 1
        self._token = token
        return self._token
    

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

    def __init__(self, target:NFAState, value:str, type_):
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
        self._accept = value

    def appendArc(self, target:NFAState, value:str, type_):
        self._arcs.append(NFAArc(target, value, type_))

    def appendState(self, target:NFAState):
        self._arcs += target._arcs

    def prependArc(self, target:NFAState, value:str, type_):
        assert(len(self._arcs) == 1)
        self._arcs.insert(0, NFAArc(target, value, type_))

    def prependState(self, target:NFAState):
        self._arcs = target._arcs + self._arcs

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
        self._start = None
        self._end = None
        self._nodes = []
        self._groups = 0
    
    def newState(self) -> NFAState:
        state = NFAState()
        # state._index = len(self._nodes)
        self._nodes.append(state)
        return state
    
    def dump(self, debug:bool):
        """Dump a graphical representation of the NFA"""
        todo = [self.start]
        for i, state in enumerate(todo):
            if debug: print("  State", i, state is self.end and "(final)" or "")
            for arc in state._arcs:
                next = arc.target
                if next in todo:
                    j = todo.index(next)
                else:
                    j = len(todo)
                    todo.append(next)
                if debug:
                    if arc._type == NFAArc.EPSILON:
                        print("    %s -> %d" % ("ε", j))
                    elif arc._type == NFAArc.LGROUP:
                        print("    ( -> %d" % j)
                    elif arc._type == NFAArc.RGROUP:
                        print("    ) -> %d" % j)
                    elif arc._type == NFAArc.CHAR:
                        print("    %s -> %d" % (arc._value, j))
                    
        if debug: print("")
        self._nodes = todo

class Thread(object):
    pass


class Group(object):
    pass


class RegExp(object):
    """ A simple regular expression using NFA for matching
    note that is this different from pgen's NFA, we want to 
    make it more intuitive.
    """
    def __init__(self, pattern:str, debug:bool=False):
        self._pat = pattern
        self._debug = debug
        self._tokenizer = Tokenizer(self._pat)
        self._nfa = NFA()
        self._compiled = False

    def getToken(self):
        # getToken get the current token but not consume it
        return self._tokenizer.token

    def nextToken(self):
        # nextToken consumes the current one and get 
        # the next token from tokenizer
        return self._tokenizer.next()

    def concat(self) -> tuple[NFAState]:
        aa = self._nfa.newState()
        zz = aa

        while True:
            token = self.getToken()
            # currently only suport Token.CHAR
            if token.type == Token.CHAR:
                z = self._nfa.newState()
                zz.appendArc(z, token.value, NFAArc.CHAR)
                zz = z
                self.nextToken()
            elif token.type == Token.END:
                break
            else:
                break

        if zz == aa:
            # Null String!
            return None, None
        return aa, zz

    def group(self) -> tuple[NFAState]:
        """ concat single character,class,groups,closure,star,... etc.
        """
        aa = None # NFA State to return
        zz = None

        # pdb.set_trace()
        # invariant property: len(zz._arc) == 0
        while True:
            token = self.getToken()

            if token.type == Token.LPAREN:
                self._nfa._groups += 1
                group = self._nfa._groups
                self.nextToken() # consume '('
                a1, z1 = self.alternate()
                token = self.getToken()
                if token.type != Token.RPAREN:
                    raise Exception('Unmatch parenthesis')
                
                self.nextToken() # consume ')'
                a = self._nfa.newState()
                z = self._nfa.newState()
                a.appendArc(a1, group, NFAArc.LGROUP)
                z1.appendArc(z, group, NFAArc.RGROUP)
            elif token.type == Token.CHAR:
                # TODO: currently only handle Token.CHAR
                a, z = self.concat()
            else:
                # don't recognize this token, break
                break

            # now handle the STAR/PLUS/QUESTION
            token = self.getToken()
            if token.type == Token.STAR:
                self.nextToken()
                z1 = self._nfa.newState()
                a.appendArc(z1, None, NFAArc.EPSILON)
                z.appendArc(a, None, NFAArc.EPSILON)
                z = z1
            elif token.type == Token.STAR2:
                self.nextToken()
                z1 = self._nfa.newState()
                a.prependArc(z1, None, NFAArc.EPSILON)
                z.appendArc(a, None, NFAArc.EPSILON)
                z = z1
            elif token.type == Token.PLUS:
                self.nextToken()
                z1 = self._nfa.newState()
                z.appendArc(a, None, NFAArc.EPSILON)
                z.appendArc(z1, None, NFAArc.EPSILON)
                z = z1
            elif token.type == Token.PLUS2:
                self.nextToken()
                z1 = self._nfa.newState()
                z.appendArc(z1, None, NFAArc.EPSILON)
                z.appendArc(a, None, NFAArc.EPSILON)
                z = z1
            elif token.type == Token.QUEST:
                self.nextToken()
                a.appendArc(z, None, NFAArc.EPSILON)
            elif token.type == Token.QUEST2:
                self.nextToken()
                a.prependArc(z, None, NFAArc.EPSILON)
            elif token.type in (Token.ALTER, Token.END):
                # if meet the ALTER token, we should return and let alter
                # to handle it, but if a/z is None, we should skip it and
                # continue to parse.
                if token.type == Token.ALTER and a is None:
                    self.nextToken()
                    continue
                if aa is not None:
                    zz.appendArc(a, None, NFAArc.EPSILON)
                    zz = z
                else:
                    aa, zz = a, z
                break

            # not allow ++/**/*+/+*/... etc
            idx = self._tokenizer.index
            token = self.getToken()
            if token.type in {Token.PLUS, Token.PLUS2, Token.STAR, 
                                Token.STAR2, Token.QUEST, Token.QUEST2}:
                raise Exception(f'Syntax Error at position {idx}')

            # adjust aa and zz here
            # invariant property: len(zz._arc) == 0
            if aa is None:
                aa, zz = a, z
            else:
                # because len(zz._arc) == 0, so we can append state
                # this will reduce the state a little bit.
                zz.appendState(a)
                zz = z
            assert(len(zz._arcs) == 0)

        #end while
        return aa, zz


    def alternate(self) -> tuple[NFAState]:
        """ alternate split s into different section delimited by '|'
        """
        # pdb.set_trace()
        a, z = self.group()

        token = self.getToken()
        if token.type != Token.ALTER:
            return a, z
 
        aa = self._nfa.newState()
        zz = self._nfa.newState()

        while True:
            aa.appendArc(a, None, NFAArc.EPSILON)
            z.appendArc(zz, None, NFAArc.EPSILON)

            token = self.getToken()
            if token.type != Token.ALTER:
                break

            while True:
                # if multiple '|' shows up, combine them into one
                self.nextToken()
                if self.getToken().type != Token.ALTER:
                    break

            a, z = self.group()
            if a is None: # one possible pattern is 'abc|'
                break

        return aa, zz

    def compile(self) -> None:
        if self._compiled:
            return

        s = self._pat
        start, end = self.alternate()
        if self._tokenizer.index != len(s):
            raise Exception(f'Unexpected token: {self.getToken()}')

        if start is None:
            assert(end is None)
            start = self._nfa.newState()
            end = self._nfa.newState()

        end.accept = True
        self._nfa.start = start
        self._nfa.end = end
        self._nfa.dump(self._debug)
        self._compiled = True

    def match(text) -> Group or None:
        raise NotImplementedError

if __name__ == '__main__':
    re = RegExp('ab|||', debug=True)
    re.compile()
    re = RegExp('ab|cd|ef', debug=True)
    re.compile()
    re = RegExp('(a)*', debug=True)
    re.compile()
    re = RegExp('(ab)*', debug=True)
    re.compile()
    re = RegExp('(ab|cd)*', debug=True)
    re.compile()
    re = RegExp('(ab|c+?d)*', debug=True)
    re.compile()