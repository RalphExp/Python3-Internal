#!/usr/bin/python3

# This file shows how to use NFA to construct a regular expression engine.
# for fun only :)

from __future__ import annotations
from collections import OrderedDict
from itertools import count

import sys
import copy
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
    CARET = 16
    DOLLAR = 17
    DOT = 18

    def __init__(self, type, value=None, pos=None):
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
        self._tokenDict = {
            '|': Token(Token.ALTER),
            '(': Token(Token.LPAREN),
            ')': Token(Token.RPAREN),
            '[': Token(Token.LBRACK),
            ']': Token(Token.RBRACK),
            '{': Token(Token.LBRACE),
            '}': Token(Token.RBRACE),
            '*': Token(Token.STAR),
            '+': Token(Token.PLUS),
            '?': Token(Token.QUEST),
            '^': Token(Token.CARET),  # currently not supported
            '$': Token(Token.DOLLAR), # currently not supported
            '.': Token(Token.DOT)     # currently not supported
        }
        self._tokenDict2 = {
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

        token = self._tokenDict2.get(s[self._index:self._index+2], None)
        if token != None:
            token.pos = self._index
            self._index += 2
            self._token = token
            return token
        
        token = self._tokenDict.get(s[self._index], None)
        if token != None:
            token.pos = self._index
            self._index += 1
            self._token = token
            return token
        
        token = Token(Token.CHAR, s[self._index].encode('utf-8'), self._index)
        self._index += 1
        self._token = token
        return self._token
    
class Range(object):
    def __init__(self, ranges:list[tuple]):
        self._ranges = ranges

    def match(self, c):
        for r in self._ranges:
            if r[0] <= c <= r[1]:
                return True
        return False

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
    ANCHOR = 5 # ^ matches the beginning, $ matches the end

    def __init__(self, target:NFAState, value:str or int, type_):
        self._type = type_
        self._value = value
        self._target = target

    @property
    def type(self):
        return self._type
    
    @property
    def value(self):
        return self._value
    
    @property
    def target(self):
        return self._target
    
    @target.setter
    def target(self, target):
        self._target = target


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

    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, val:int):
        self._index = val

    def appendArc(self, target:NFAState, value, type_):
        self._arcs.append(NFAArc(target, value, type_))

    def appendState(self, target:NFAState):
        self._arcs += target._arcs

    def prependArc(self, target:NFAState, value, type_):
        assert(len(self._arcs) == 1)
        self._arcs.insert(0, NFAArc(target, value, type_))

    def prependState(self, target:NFAState):
        self._arcs = target._arcs + self._arcs

    def copy(self, state2):
        self._arcs = state2._arc
        self.accept = state2.accept
        state2._arc = None

    @staticmethod
    def _closure(state:NFAState, result:list[NFAState], filter:set):
        """ closure return the states can be reach by 
        an ε transition in DFS order.
        """
        
        for arc in state._arcs:
            if arc.type == NFAArc.EPSILON and arc.target not in filter:
                result.append(arc.target)
                filter.add(arc.target)
                NFAState._closure(arc.target, result, filter)
            
    @staticmethod
    def closure(state):
        result = [state]
        filter = {state}
        NFAState._closure(state, result, filter)
        return result
    
    def __hash__(self):
        # assert(self._index is not None)
        return self._index

    def __eq__(self, state):
        # __eq__ can be used to simplify the states
        if len(self._arcs) != len(state._arcs):
            return False
        
        for i in range(len(self._arcs)):
            if self._arcs[i] != state._arcs[i]:
                return False
        return True
    
    def simplify(self):
        raise NotImplementedError

    
class NFA(object):
    def __init__(self):
        self._start = None
        self._end = None
        self._nodes = []
        self._groups = 0
    
    def newState(self) -> NFAState:
        state = NFAState()
        # state._index = len(self._nodes)
        # self._nodes.append(state)
        return state
    
    def dump(self, debug:bool):
        """Dump a graphical representation of the NFA"""
        todo = [self._start]

        for i, state in enumerate(todo):
            # set index to the state, index will be used in hashing
            state.index = i
            if debug: print("  State", i, state is self._end and "(final)" or "")
            for arc in state._arcs:
                next = arc.target
                if next in todo:
                    j = todo.index(next)
                    # XXX: there's a trap here, because of the __eq__, 
                    # next may not equal to todo[j], must fix the arc to 
                    # point to the correct state
                    if next.index != todo[j].index:
                        arc.target = todo[j]
                else:
                    j = len(todo)
                    todo.append(next)
                if debug:
                    if arc.type == NFAArc.EPSILON:
                        print("    %s -> %d" % ("ε", j))
                    elif arc.type == NFAArc.LGROUP:
                        print("    ( -> %d" % j)
                    elif arc.type == NFAArc.RGROUP:
                        print("    ) -> %d" % j)
                    elif arc.type == NFAArc.CHAR:
                        print("    %s -> %d" % (arc.value, j))
                    
        if debug: print("")
        self._nodes = todo


class Thread(object):
    """ use google re2's BFS matching algorithm
    """
    def __init__(self, id, state, text, pos, groups=None):
        self._id = id
        self._state = state
        self._text = text
        self._pos = pos
        self._groups = groups or {0: [pos, None]}

    def _advance(self, state:NFAState, threads:list[Thread], filter:set):
        if state.accept:
            self._groups = copy.deepcopy(self._groups)
            self._groups[0][1] = self._pos
            threads.append(self)
            return

        for arc in state._arcs:
            if arc.target in filter:
                continue

            filter.add(arc.target)
            if arc.type == NFAArc.EPSILON:
                th = self.copy(arc.target)
                th._advance(arc.target, threads, filter)

            elif arc.type == NFAArc.CHAR and self._pos < len(self._text):
                if arc.value == self._text[self._pos].encode('utf-8'):
                    th = self.copy(arc.target, pos=self._pos+1)
                    if arc.target.accept:
                        th._groups = copy.deepcopy(self._groups)
                        th._groups[0][1] = self._pos+1
                    threads.append(th)

            elif arc.type == NFAArc.CLASS and self._pos < len(self._text):
                # FIXME: how to match unicode characters??
                char = int.from_bytes(self._text[self._pos].encode('utf-8'), byteorder='little')
                if arc.value.match(char):
                    th = self.copy(arc.target, pos=self._pos+1)
                    if arc.target.accept:
                        th._groups = copy.deepcopy(self._groups)
                        th._groups[0][1] = self._pos+1
                    threads.append(th)

            elif arc.type == NFAArc.LGROUP:
                th = self.copy(arc.target)
                # only record the first occurrence
                if not th.groups.get(arc.value):
                    th._groups = copy.deepcopy(self._groups)
                    th._groups[arc.value] = [self._pos, None]
                th._advance(arc.target, threads, filter)

            elif arc.type == NFAArc.RGROUP:
                assert(self._groups[arc.value])
                th = self.copy(arc.target)
                if not th.groups[arc.value][1]:
                    th._groups = copy.deepcopy(self._groups)
                    th._groups[arc.value][1] = self._pos
                th._advance(arc.target, threads, filter)
        return threads

    def copy(self, state, pos=None) -> Thread:
        th = Thread(self._id, state, self._text, self._pos, self.groups)
        if pos: th._pos = pos
        return th

    def advance(self, filter:set) -> list[NFAState]:
        newThreads = []
        self._advance(self._state, newThreads, filter)
        return newThreads
    
    @property
    def gid(self):
        """ generation id, the smaller the id is, the earlier the 
        thread has been created
        """
        return self._id

    @property
    def groups(self):
        return self._groups

    @property
    def state(self):
        return self._state


class RegExp(object):
    """ A simple regular expression using NFA for matching
    note that is this different from pgen's NFA, we want to 
    make it more intuitive.

    usage:
        re = re2.RegExp(pattern)
        g = re.search(text)
        ...
    """
    def __init__(self, pattern:str, debug:bool=False):
        self._pat = pattern
        self._debug = debug
        self._tokenizer = Tokenizer(self._pat)
        self._nfa = NFA()
        self._compiled = False
        self._threads = OrderedDict()

    def getToken(self):
        # getToken get the current token but not consume it
        return self._tokenizer.token

    def nextToken(self):
        # nextToken consumes the current one and get 
        # the next token from tokenizer
        return self._tokenizer.next()

    def modify(self, a, z) -> tuple[NFAState]:
        """ handles STAR/QUEST/PLUS,... etc.
        """
 
        # invariant property: len(z._arc) == 0
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
        else:
            return a, z

        # not allow ++/**/*+/+*/... etc
        idx = self._tokenizer.index
        token = self.getToken()
        if token.type in {Token.PLUS, Token.PLUS2, Token.STAR, 
                            Token.STAR2, Token.QUEST, Token.QUEST2}:
            raise Exception(f'Syntax Error at position {idx}')
        
        assert(len(z._arcs) == 0) 
        return a, z

    def concat(self) -> tuple[NFAState]:
        aa = None
        zz = None

        while True:
            token = self.getToken()
            # currently only suport Token.CHAR
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
                a = self._nfa.newState()
                z = self._nfa.newState()
                a.appendArc(z, token.value, NFAArc.CHAR)
                self.nextToken()
            elif token.type == Token.DOT:
                a = self._nfa.newState()
                z = self._nfa.newState()
                a.appendArc(z, Range([(0, sys.maxunicode)]), NFAArc.CLASS)
                self.nextToken()
            else:
                # currently not implement or token we don't recognize
                break

            a, z = self.modify(a, z)
            if not aa:
                aa = a
                zz = z
            else:
                zz.appendState(a)
                zz = z

        if zz == aa:
            # Null String!
            return None, None
        return aa, zz

    def alternate(self) -> tuple[NFAState]:
        """ alternate split s into different section delimited by '|'
        """
        a, z = self.concat()
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

            a, z = self.concat()
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
        self._nfa._start = start
        self._nfa._end = end
        self._nfa.dump(self._debug)
        self._compiled = True

    def addThread(self, text:str, pos:int, filter:set, gen):
        start = self._nfa._start
        # states = NFAState.closure(start)
        threads = []    
        th = Thread(next(gen), start, text, pos, groups=None)
        threads += th.advance(filter)
        return threads

    def search(self, text, pos=0) -> dict:
        if self._compiled == False:
            self.compile()

        self._threads.clear()
        gen = count()
        matchThread = None
        matched = False

        def compareThread(th1:Thread, th2:Thread):
            """ we want to choose the longest match,
            which can be compared by the gid
            """
            if th1 is None:
                return th2
            if th1.gid < th2.gid:
                return th1
            # when th1.gid == th2.gid alway choose th2,
            # because th2 is a longer match. if th1.gid > th2.gid,
            # it means th2 is a earlier matching.
            return th2

        while pos <= len(text):
            filter = set() # intermediate states
            newThreads = OrderedDict() # result (state, thread)
            matched = False
            for _, thread in self._threads.items():
                threads = thread.advance(filter)
                for th in threads:
                    if th.state.accept:
                        matchThread = compareThread(matchThread, th)
                        # all the thread in threads have the same gid
                        # we don't need to advance any more
                        matched = True
                        break
                    
                    if not newThreads.get(th.state):
                        newThreads[th.state] = th
                if matched:
                    # from here on, the rest threads are not considered a
                    # candidate, e.g. in the regular expression A|B, when A
                    # is a correct matching, B is not considered any more
                    break
            
            # try to add new threads at the start state
            if not matchThread:
                threads = self.addThread(text, pos, filter, gen)
                for th in threads:
                    if th.state.accept:
                        matchThread = compareThread(matchThread, th)
                        # all the thread in threads have the same gid
                        # we don't need to advance any more
                        break
                    if not newThreads.get(th.state):
                        newThreads[th.state] = th
            
            if len(newThreads) == 0 and matchThread:
                break

            self._threads = newThreads
            pos += 1

        return matchThread.groups if matchThread is not None else None 


if __name__ == '__main__':
    re = RegExp('(ab|c+?d)', debug=True)
    re.compile()
    g = re.search('ccccccccd')
    print(g)

    re = RegExp('(a(b*)c(d*e))', debug=True)
    g = re.search('sssabbbbbbcdddef')
    print(g)

    re = RegExp('(ab)*', debug=True)
    g = re.search('ab')
    print(g)

    re = RegExp('(ab)*?', debug=True)
    g = re.search('ab')
    print(g)

    re = RegExp('(ab)+', debug=True)
    g = re.search('abab')
    print(g)

    re = RegExp('(ab)+?', debug=True)
    g = re.search('abab')
    print(g)

    re = RegExp('a(.*)bc', debug=True)
    g = re.search('abababc')
    print(g)

    re = RegExp('a(.*?)b', debug=True)
    g = re.search('abab')
    print(g)