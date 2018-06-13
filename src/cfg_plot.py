# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 20:50:47 2018

@author: DrLC
"""

import os, sys
import networkx as nx 
from networkx.drawing.nx_agraph import to_agraph 
import matplotlib.pyplot as plt

from cfg import CFG
from symtab import build_symtab

def plot(G, cfg, node="", pos=[0,0], entry=False):
    
    G.add_node(node.strip("<>"), pos=pos)
    if entry:
        G.add_node('entry', pos=[pos[0], pos[1]-100], node_color='blue')
        G.add_edge('entry', node.strip('<>'))
    for b in cfg.get_block():
        if node == b.get_name():
            if b.get_goto() is None:
                G.add_node("return", pos=[pos[0], pos[1]+100], node_color='blue')
                G.add_edge(node.strip('<>'), "return")
                continue
            g = b.get_goto().get_goto()
            if g['condition'] == '__ALWAYS__':
                for i in g['true']:
                    tmp_flag = False
                    for bb in cfg.get_block():
                        if i == bb.get_name():
                            tmp_flag = True
                            break
                    if ((not G.has_node(i.strip('<>'))) and tmp_flag):
                        plot(G, cfg, i, [pos[0], pos[1]+100])
                    if tmp_flag:
                        G.add_edge(node.strip('<>'), i.strip('<>'))
            else:
                for i in g['true']:
                    tmp_flag = False
                    for bb in cfg.get_block():
                        if i == bb.get_name():
                            tmp_flag = True
                            break
                    if ((not G.has_node(i.strip('<>'))) and tmp_flag):
                        plot(G, cfg, i, [pos[0]-10, pos[1]+100])
                    if tmp_flag:
                        G.add_edge(node.strip('<>'), i.strip('<>'), weight="T")
                for i in g['false']:
                    tmp_flag = False
                    for bb in cfg.get_block():
                        if i == bb.get_name():
                            tmp_flag = True
                            break
                    if ((not G.has_node(i.strip('<>'))) and tmp_flag):
                        plot(G, cfg, i, [pos[0]+10, pos[1]+100])
                    if tmp_flag:
                        G.add_edge(node.strip('<>'), i.strip('<>'), weight="F")

def generate_jpg(cfg, name="", out_dir=""):
        
    for key in cfg.keys():
        G = nx.DiGraph()
        plot(G, cfg[key], cfg[key].get_entry().get_name(), [0, 0], True)
        pos = nx.get_node_attributes(G, 'pos')
        edge_label = nx.get_edge_attributes(G,'weight')            
        nx.draw(G, pos, with_labels=True, font_size=8, node_size=500,
                node_shape='p', node_color=(1,0,1))
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_label)
        nx.draw_networkx_nodes(G, pos, ['entry', 'return'], with_labels=True,
                               font_size=8, node_size=500, node_shape='p',
                               node_color=(0,1,1))
        plt.title("CFG for Function \"" + key + "\" in \"" + path + "\"")
        plt.savefig(os.path.join(os.path.relpath(out_dir), name+"_"+key+".png"))
        plt.show()
        
def generate_cfg(cfg, name="", out_dir=""):
    
    stdout_save = sys.stdout
    for key in cfg.keys():
        with open(os.path.join(os.path.relpath(out_dir), name+"_"+key+".cfg"), 'w') as f:
            sys.stdout = f
            cfg[key].debug()
        sys.stdout = stdout_save
        
if __name__ == "__main__":
    
    path = "../benchmark/t1.ssa"
    out = "../output"
    
    _, file = os.path.split(path)
    name, _ = os.path.splitext(file)
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    cfg = {}
    for key in sym_tab.keys():
        cfg[key] = CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                       key)
    
    generate_jpg(cfg, name, out)
    generate_cfg(cfg, name, out)