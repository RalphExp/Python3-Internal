import graphviz

# install graphviz
# e.g. sudo apt-get install graphviz
# pip install graphviz


# graph file is generated by the pgen command
# python3 -m pgen ../Grammar/Grammar ../Grammar/Tokens graminit.h graminit.c --graph graph 

if __name__ == '__main__':
    s = graphviz.Source.from_file('graph', format='jpg')
    s.view(directory='graphs')
