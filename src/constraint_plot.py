# -*- coding: utf-8 -*-
"""
Created on Sun Jul  1 14:26:40 2018

@author: DrLC
"""

import os, sys
import networkx as nx 
from networkx.drawing.nx_agraph import to_agraph 
import matplotlib.pyplot as plt

import constraint
from constraint import CG
from cfg import CFG
from symtab import build_symtab

import os, sys

def plot(G, cg):
    
    G.add_node("ENTRY", node_color='blue')
    G.add_node("RETURN", node_color='blue')
    for c in cg.get_constraint_nodes():
        G.add_node(str(c.get_number())+". "+str(c))
    for c in cg.get_constraint_nodes():
        for to in c.get_next():
            G.add_edge(str(c.get_number())+". "+str(c),
                       str(to.get_number())+". "+str(to))
    if cg.get_return_node() is not None:
        G.add_edge(str(cg.get_return_node().get_number())+". "+str(cg.get_return_node()),
                   'RETURN')
    for c in cg.get_entry_nodes():
        G.add_edge('ENTRY', str(c.get_number())+". "+str(c))
    return G

def generate_jpg(cg, name="", out_dir=""):
        
    for key in cfg.keys():
        G = nx.DiGraph()
        plot(G, cg[key])          
        nx.draw(G, with_labels=True, font_size=8, edge_color='y',
                node_shape='.', node_color=(1,1,1), pos=nx.circular_layout(G))
        plt.title("CG for Function \"" + key + "\" in \"" + path + "\"")
        plt.savefig(os.path.join(os.path.relpath(out_dir), name+"_"+key+".png"))
        plt.show()
        
def generate_cfg(cg, name="", out_dir=""):
    
    stdout_save = sys.stdout
    for key in cg.keys():
        with open(os.path.join(os.path.relpath(out_dir), name+"_"+key+".cg"), 'w') as f:
            sys.stdout = f
            cg[key].debug()
        sys.stdout = stdout_save
        
def print_help():
    
    print ()
    print ("+----------------------------+")
    print ("|                            |")
    print ("|      Constraint Graph      |")
    print ("|          by DrLC           |")
    print ("|                            |")
    print ("+----------------------------+")
    print ()
    print ("Transfer .ssa file to constraint graph, and plot it.")
    print ()
    print ("Use this command to run.")
    print ("  python3 %s [-P|--path SSA_FILE_PATH]" % sys.argv[0])
    print ()
    exit(0)
 
def get_op():
    
    args = sys.argv
    if '-h' in args or '--help' in args:
        print_help()
    if len(args) == 1:
        path = '../benchmark/t7.ssa'
        out = '../output'
    elif len(args) == 3:
        if args[1] in ['-P', '--path']:
            path = args[2]
            out = '../output'
        elif args[1] in ['-O', '--output']:
            path = '../benchmark/t1.ssa'
            out = args[2]
    elif len(args) == 5:
        path = None
        out = None
        for i in [1, 3]:
            if args[i] in ['-P', '--path']:
                path = args[i+1]
            if args[i] in ['-O', '--output']:
                out = args[i+1]
        if path is None or out is None:
            print_help()
    else:
        print_help()
    return path, out
        
if __name__ == "__main__":
    
    path, out = get_op()
    
    _, file = os.path.split(path)
    name, _ = os.path.splitext(file)
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    cfg = {}
    for key in sym_tab.keys():
        cfg[key] = CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                       key)
    cg = {}
    for key in cfg.keys():
        cg[key] = CG(cfg[key], sym_tab[key], key)
        
    generate_jpg(cg, name, out)
    generate_cfg(cg, name, out)