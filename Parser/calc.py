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
    

def skipBlank(gen):
    tok = getToken(gen)
    while tok.type in (token.NEWLINE, token.INDENT):
        tok = getToken(gen)
    return tok


def factor(gen):
    tok = skipBlank(gen)

    if tok.exact_type == token.MINUS:
        nextTok = skipBlank(gen)

        if nextTok.exact_type != token.NUMBER:
            raise Exception('number not found after token -')
            
        return -1 * float(nextTok.string)

    if tok.exact_type == token.NUMBER:
        return float(tok.string)
        
    if tok.exact_type == token.LPAR:
        t = expr(gen)
        tok = skipBlank(gen)
        
        if tok.exact_type != token.RPAR:
            raise Exception('unexpected token: ' + str(tok))
        return t

    putToken(tok)
    return None    


def term(gen):
    e = factor(gen)

    while True:
        tok = skipBlank(gen)
        if tok.exact_type == token.STAR:
            e *= factor(gen)
        elif tok.exact_type == token.SLASH:
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
        tok = skipBlank(gen)
        if tok.exact_type == token.PLUS:
            t += term(gen)
        elif tok.exact_type == token.MINUS:
            t -= term(gen)
        else:
            putToken(tok)
            break
    return t


def calculate(gen):
    e = expr(gen)
    tok = getToken(gen)
    if tok.type != token.ENDMARKER:
        raise Exception('unexpected token: ' + str(tok))
    return e


if __name__ == '__main__':
    while True:
        line = io.StringIO(input('input a math expression: '))
        gen = tokenize.generate_tokens(line.readline)

        try:
            value = calculate(gen)
            if value is not None:
                print(value)
        except Exception as e:
            print(str(e))