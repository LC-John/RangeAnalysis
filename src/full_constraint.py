# -*- coding: utf-8 -*-
"""
Created on Tue Jul  3 13:10:21 2018

@author: DrLC
"""

from symtab import build_symtab
import constraint
import cfg

import os, sys
from interval import interval

class FCG(object):
    
    def __init__(self, _cfg={}, _main="", _symtab={}):
        
        assert _main in _cfg.keys()
        
        self.__entry_set_enable = True
        self.__name = _main
        
        main = constraint.CG(_cfg[_main], _symtab[_main], _main)
        self.__main = main.get_constraint_nodes()
        self.__entry = self.__entry_reorder(main.get_entry_nodes(), _symtab[_main]['decl'])
        self.__return = main.get_return_node()
        self.__call = []
        tb_del = []
        for i in self.__main:
            if type(i) is constraint.CallNode:
                tb_del.append(i)
                tmp_func_name = i.get_name().strip().split("(")[0].strip()
                assert tmp_func_name in _cfg.keys()
                tmp_func_cg = constraint.CG(_cfg[tmp_func_name],
                                            _symtab[tmp_func_name],
                                            tmp_func_name)
                self.__call += tmp_func_cg.get_constraint_nodes()
                tmp_func_entry = self.__entry_reorder(tmp_func_cg.get_entry_nodes(),
                                                      _symtab[tmp_func_name]['decl'])
                for en, prv in zip(tmp_func_entry, i.get_prev()):
                    if en is None:
                        continue
                    prv.del_next(i)
                    prv.add_next(en)
                    en.add_prev(prv)
                tmp_func_return = tmp_func_cg.get_return_node()
                assert len(i.get_next()) == 1
                nxt = i.get_next()[0]
                nxt.del_prev(i)
                nxt.add_prev(tmp_func_return)
                tmp_func_return.add_next(nxt)
        for i in tb_del:
            self.__main.remove(i)
        self.__constraint = self.__main + self.__call
        
        self.__simplify()
        tb_del = []
        for i in self.__main:
            if i not in self.__constraint:
                tb_del.append(i)
        for i in tb_del:
            self.__main.remove(i)
        tb_del = []
        for i in self.__call:
            if i not in self.__constraint:
                tb_del.append(i)
        for i in tb_del:
            self.__call.remove(i)
        
    def __entry_reorder(self, _entry=[], _funcdecl=None):
        
        ret = []
        for a in _funcdecl.get_args():
            match_flag = False
            for e in _entry:
                if e.get_name().startswith(a.get_name()):
                    ret.append(e)
                    match_flag = True
                    break
            if not match_flag:
                ret.append(None)
        return ret

    def __simplify(self):
        
        while self.__backward_simplify_iter():
            pass
        while self.__forward_simplify_iter():
            pass
        tb_del = []
        for c in self.__constraint:
            if len(c.get_next()) == 0 and len(c.get_prev()) == 0:
                tb_del.append(c)
        for c in tb_del:
            self.__constraint.remove(c)
        
    def __backward_simplify_iter(self):
        
        ret = []
        for c in self.__constraint:
            if c.get_prev() == []:
                continue
            tb_del_ = []
            for prv in c.get_prev():
                if prv not in self.__constraint:
                    tb_del_.append(prv)
            for i in tb_del_:
                c.del_prev(i)
            if c.get_prev() == []:
                ret.append(c)
        for i in ret:
            self.__constraint.remove(i)
            if i in self.__entry:
                self.__entry.remove(i)
        if len(ret) == 0:
            return False
        else:
            return True
          
    def __forward_simplify_iter(self):
        
        ret = []
        if self.__return is None:
            ret = self.__constraint
        else:
            for c in self.__constraint:
                if (type(c) is constraint.VarNode and len(c.get_next()) == 0
                    and (not self.__return.get_number() == c.get_number())):
                    ret.append(c)
                    for prv in c.get_prev():
                        prv.del_next(c)
        for i in ret:
            self.__constraint.remove(i)
            if i in self.__entry:
                self.__entry.remove(i)
        if len(ret) == 0:
            return False
        else:
            return True
        
    def debug(self):
        
        print ()
        print ('Full constraint graph ' + self.__name)
        if len(self.__entry) == 0:
            print ('No entry')
        else:
            print ('Entry: ', end="")
            for i in self.__entry:
                print (str(i.get_number()), end=" ")
            print ()
        if self.__return is None:
            print ("No return")
        else:
            print ("Return: "+str(self.__return.get_number()))
        if len(self.__constraint) == 0:
            print ("No constraint")
        else:
            print ("Constraint:")
            for c in self.__constraint:
                c.debug()
        
    def set_entry_range(self, _range={}):
        
        assert len(_range) == len(self.__entry)
        assert self.__entry_set_enable
        for en, r in zip(self.__entry, _range):
            if en is None:
                continue
            assert en.get_name().startswith(r[2])
            for prv in en.get_prev():
                self.__constraint.remove(prv)
            en.clr_prev()
            tmp_node = constraint.RangeNode(r[0], r[1])
            self.__constraint.append(tmp_node)
            en.add_prev(tmp_node)
            tmp_node.add_next(en)
        self.__entry = []
        self.__entry_set_enable = False
        for c in self.__constraint:
            if type(c) is constraint.RangeNode and len(c.get_prev()) == 0:
                assert (len(c.get_next()) == 1)
                if type(c.get_next()[0]) is constraint.VarNode:
                    c.get_next()[0].set_minmax_widen(c.get_interval())
                    self.__entry.append(c.get_next()[0])
                
    def get_name(self):             return self.__name
    def get_constraint_nodes(self): return self.__main + self.__call
    def get_entry_nodes(self):      return self.__entry
    def get_return_node(self):      return self.__return
        
def print_help():
    
    print ()
    print ("+---------------------------------+")
    print ("|                                 |")
    print ("|      Full Constraint Graph      |")
    print ("|            by DrLC              |")
    print ("|                                 |")
    print ("+---------------------------------+")
    print ()
    print ("Transfer .ssa file to constraint graph, and embed the function calling.")
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
        path = '../benchmark/t9.ssa'
    elif len(args) == 3 and args[1] in ['-P', '--path']:
        path = args[2]
    else:
        print_help()
    return path

if __name__ == "__main__":
    
    path = get_op()
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    _cfg_ = {}
    for key in sym_tab.keys():
        _cfg_[key] = cfg.CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                             key)
        
    cg = FCG(_cfg_, "foo", sym_tab)
    cg.debug()