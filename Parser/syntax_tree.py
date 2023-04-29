import parser
import token
import symbol
import pprint

symbols = { 
    v: k for k, v in symbol.__dict__.items() if isinstance(v, int)
}
tokens = {
    v: k for k, v in token.__dict__.items() if isinstance(v, int)
}

lexicon = {**symbols, **tokens}

def replace(l: list):
    r = []
    for i in l:
        if isinstance(i, list):
            r.append(replace(i))
        else:
            if i in lexicon:
                r.append(lexicon[i])
            else:
                r.append(i)
    return r

def lex(expression):
    st = parser.expr(expression)
    st_list = parser.st2list(st)
    return replace(st_list)

def suite(expression):
    st = parser.suite(expression)
    st_list = parser.st2list(st)
    return replace(st_list)


if __name__ == '__main__':
    pprint.pprint(lex('3 * 4 + 5'))
    print('\n')
    pprint.pprint(suite('def test(a, b):\n\treturn a+b\n'))
