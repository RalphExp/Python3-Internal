#!/usr/bin/python3

import tokenize
import token
import io

cached_token = None

def getToken(gen):
    global cached_token
    
    tok = None
    if cached_token is not None:
        tok = cached_token
        cached_token = None
    else:
        tok = next(gen)
    return tok


def putToken(tok):
    global cached_token
    assert (cached_token is None)
    cached_token = tok


def factor(gen):
    tok = getToken(gen)
    while tok.type not in (token.NEWLINE, token.INDENT):
        break

    if tok.type == token.OP and tok.string == '-':
        nextTok = getToken(gen)
        while nextTok.type not in (token.NEWLINE, token.INDENT):
            break

        if nextTok.type != token.NUMBER:
            raise Exception('number not found after token -')
            
        return -1 * float(nextTok.string)

    if tok.type == token.NUMBER:
        return float(tok.string)
        
    if tok.type == token.OP and tok.string == '(':
        t = expr(gen)
        tok = getToken(gen)
        while tok.type not in (token.NEWLINE, token.INDENT):
            break
        
        if tok.type != token.OP or tok.string != ')':
            raise Exception('unmatched parenthesis')
        return t

    putToken(tok)
    return None    

def term(gen):
    e = factor(gen)

    while True:
        tok = getToken(gen)
        if tok.type in (token.NEWLINE, token.INDENT):
            continue

        if tok.type == token.OP and tok.string == '*':
            e *= factor(gen)
        elif tok.type == token.OP and tok.string == '/':
            t = factor(gen)
            if t == 0:
                raise Exception('divide by 0')
            e /= t
        else:
            putToken(tok)
            break

    return e


def expr(gen):
    t = term(gen)
    
    while True:
        tok = getToken(gen)
        if tok.type in (token.NEWLINE, token.INDENT):
            continue
        if tok.type == token.OP and tok.string == '+':
            t += term(gen)
        elif tok.type == token.OP and tok.string == '-':
            t -= term(gen)
        else:
            putToken(tok)
            break
    return t


def calculate(gen):
    e = expr(gen)
    tok = getToken(gen)
    if tok.type != token.ENDMARKER:
        raise Exception('unrecognized token: ' + str(tok))
    return e


if __name__ == '__main__':
    while True:
        line = io.StringIO(input('input a math expression: '))
        gen = tokenize.generate_tokens(line.readline)
        e = calculate(gen)
        if e is not None:
            print(e)