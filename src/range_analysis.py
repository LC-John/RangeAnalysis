# -*- coding: utf-8 -*-
"""
Created on Wed Jul  4 16:13:29 2018

@author: DrLC
"""

import constraint
import cfg
from full_constraint import FCG
from symtab import build_symtab

from interval import interval
import sys, os

def arithmetic_op(s1, s2, op):
    
    if op == '+':
        ret = s1 + s2
    elif op == '-':
        ret = s1 - s2
    elif op == '*':
        ret = s1 * s2
    elif op == '/':
        ret = s1 / s2
    elif op == 'merge':
        if len(s1) == 0 and len(s2) > 0:
            ret = s2
        elif len(s1) > 0 and len(s2) == 0:
            ret = s1
        elif len(s1) == 0 and len(s2) == 0:
            ret = interval()
        else:
            ret = interval((min(s1[0][0], s2[0][0]), max(s1[0][1], s2[0][1])))
    else: assert False, "Invalid arithmetic option \"%s\"" % op
    if len(ret)>1:
        ret_ = ret[0]
        for i in ret[1:]:
            ret_ = (min(ret_[0], i[0]), max(ret_[1], i[1]))
        return interval(ret_)
    else: return ret

def ft_range(ft_l, ft_r, ft_var):
    
    var_range = ft_var.get_minmax()
    if var_range is None:
        return None
    if len(var_range) < 1:
        return var_range
    if ft_l['ft'] is None:
        tmp_l = float(ft_l['val'])
    elif ft_l['op'] is 'pass':
        tmp_l = var_range[0][0]
    else:
        tmp_l = arithmetic_op(var_range, interval((ft_l['val'], ft_l['val'])), ft_l['op'])
        tmp_l = tmp_l[0][0]
    if ft_r['ft'] is None:
        tmp_r = float(ft_r['val'])
    elif ft_r['op'] is 'pass':
        tmp_r = var_range[0][1]
    else:
        tmp_r = arithmetic_op(var_range, interval((ft_r['val'], ft_r['val'])), ft_r['op'])
        tmp_r = tmp_r[0][1]
    return interval((tmp_l, tmp_r))
    
    
def widen(cg=None, curr_nodes=[], flag=[], updated=False):
    
    if len(curr_nodes) == 0:
        return updated
    next_nodes = []
    for curr in curr_nodes:
        assert curr.get_minmax() is not None
        if curr not in cg.get_constraint_nodes():
            continue
        if flag[cg.get_constraint_nodes().index(curr)]:
            continue
        flag[cg.get_constraint_nodes().index(curr)] = True
        for n in curr.get_next():
            if type(n) is constraint.VarNode:
                tmp_r = curr.get_minmax()
                if n.get_minmax() is not None:
                    tmp_r = arithmetic_op(tmp_r, n.get_minmax(), 'merge')
                old_range = n.get_minmax()
                tmp_updated = n.set_minmax_widen(tmp_r)
                if not old_range == n.get_minmax():
                    updated = True
                next_nodes.append(n)
            elif type(n) is constraint.RangeNode:
                assert (len(n.get_next()) <= 1)
                if len(n.get_next()) == 0:
                    continue
                assert type(n.get_next()[0]) is constraint.VarNode
                tmp_r = n.get_interval()
                tmp_c = curr.get_minmax()
                tmp_r = tmp_r & tmp_c
                old_range = n.get_next()[0].get_minmax()
                tmp_updated = n.get_next()[0].set_minmax_widen(tmp_r)
                if not old_range == n.get_next()[0].get_minmax():
                    updated = True
                next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.FtRangeNode:
                assert (len(n.get_prev()) >= 2 and len(n.get_next()) <= 1)
                if len(n.get_next()) == 0:
                    continue
                assert type(n.get_next()[0]) is constraint.VarNode
                tmp_r = None
                tmp_c = None
                for prv in n.get_prev():
                    if ((n.get_l()['ft'] is not None and n.get_l()['ft'].startswith(prv.get_name())) \
                        or (n.get_r()['ft'] is not None and n.get_r()['ft'].startswith(prv.get_name()))):
                        if tmp_r is None:
                            tmp_r = ft_range(n.get_l(), n.get_r(), prv)
                        else:
                            tmp_r = arithmetic_op(ft_range(n.get_l(), n.get_r(), prv),
                                                  tmp_r, "merge")
                    else:
                        if tmp_c is None:
                            tmp_c = prv.get_minmax()
                        else:
                            tmp_c = arithmetic_op(prv.get_minmax(), tmp_c, "merge")
                if tmp_c is None:
                    continue
                old_range = n.get_next()[0].get_minmax()
                if tmp_r is None:
                    tmp_updated = n.get_next()[0].set_minmax_widen(tmp_c)
                else:
                    tmp_updated = n.get_next()[0].set_minmax_widen(tmp_c & tmp_r)
                if not old_range == n.get_next()[0].get_minmax():
                    updated = True
                next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.PhiNode:
                assert (len(n.get_next()) == 1 \
                        and type(n.get_next()[0]) is constraint.VarNode)
                tmp_r = None
                for prv in n.get_prev():
                    if prv.get_minmax() is None:
                        continue
                    if tmp_r is None:
                        tmp_r = prv.get_minmax()
                    else:
                        tmp_r = arithmetic_op(tmp_r, prv.get_minmax(), 'merge')
                if tmp_r is not None:
                    old_range = n.get_next()[0].get_minmax()
                    tmp_updated = n.get_next()[0].set_minmax_widen(tmp_r)
                    if not old_range == n.get_next()[0].get_minmax():
                        updated = True
                    next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.ArithmeticNode:
                assert (len(n.get_prev()) in [1, 2] and len(n.get_next()) == 1)
                if type(n.get_prev()[0]) is constraint.VarNode:
                    tmp_r1 = n.get_prev()[0].get_minmax()
                elif type(n.get_prev()[0]) is constraint.RangeNode:
                    tmp_r1 = n.get_prev()[0].get_interval()
                else: assert False
                if len(n.get_prev()) == 1:
                    tmp_r2 = tmp_r1
                elif type(n.get_prev()[1]) is constraint.VarNode:
                    tmp_r2 = n.get_prev()[1].get_minmax()
                elif type(n.get_prev()[1]) is constraint.RangeNode:
                    tmp_r2 = n.get_prev()[1].get_interval()
                else: assert False
                if (tmp_r1 is not None and tmp_r2 is not None):
                    tmp_r = arithmetic_op(tmp_r1, tmp_r2, n.get_op())
                    old_range = n.get_next()[0].get_minmax()
                    tmp_updated = n.get_next()[0].set_minmax_widen(tmp_r)
                    if not old_range == n.get_next()[0].get_minmax():
                        updated = True
                    next_nodes.append(n.get_next()[0])
            else:
                print (type(n))
                assert False
    return widen(cg, next_nodes, flag, updated)
    
def narrow(cg=None, curr_nodes=[], flag=[], updated=False):
    
    if len(curr_nodes) == 0:
        return updated
    next_nodes = []
    for curr in curr_nodes:
        assert curr.get_minmax() is not None
        if curr not in cg.get_constraint_nodes():
            continue
        if flag[cg.get_constraint_nodes().index(curr)]:
            continue
        flag[cg.get_constraint_nodes().index(curr)] = True
        for n in curr.get_next():
            if type(n) is constraint.VarNode:
                tmp_r = curr.get_minmax()
                if n.get_minmax() is not None:
                    tmp_r = arithmetic_op(tmp_r, n.get_minmax(), 'merge')
                old_range = n.get_minmax()
                tmp_updated = n.set_minmax_narrow(tmp_r)
                if not old_range == n.get_minmax():
                    updated = True
                next_nodes.append(n)
            elif type(n) is constraint.RangeNode:
                assert (len(n.get_next()) <= 1)
                if len(n.get_next()) == 0:
                    continue
                assert type(n.get_next()[0]) is constraint.VarNode
                tmp_r = n.get_interval()
                tmp_c = curr.get_minmax()
                tmp_r = tmp_r & tmp_c
                old_range = n.get_next()[0].get_minmax()
                tmp_updated = n.get_next()[0].set_minmax_narrow(tmp_r)
                if not old_range == n.get_next()[0].get_minmax():
                    updated = True
                next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.FtRangeNode:
                assert (len(n.get_prev()) >= 2 and len(n.get_next()) <= 1)
                if len(n.get_next()) == 0:
                    continue
                assert type(n.get_next()[0]) is constraint.VarNode
                tmp_r = None
                tmp_c = None
                for prv in n.get_prev():
                    if ((n.get_l()['ft'] is not None and n.get_l()['ft'].startswith(prv.get_name())) \
                        or (n.get_r()['ft'] is not None and n.get_r()['ft'].startswith(prv.get_name()))):
                        if tmp_r is None:
                            tmp_r = ft_range(n.get_l(), n.get_r(), prv)
                        else:
                            tmp_r = arithmetic_op(ft_range(n.get_l(), n.get_r(), prv),
                                                  tmp_r, "merge")
                    else:
                        if tmp_c is None:
                            tmp_c = prv.get_minmax()
                        else:
                            tmp_c = arithmetic_op(prv.get_minmax(), tmp_c, "merge")
                if tmp_c is None:
                    continue
                old_range = n.get_next()[0].get_minmax()
                if tmp_r is None:
                    tmp_updated = n.get_next()[0].set_minmax_narrow(tmp_c)
                else:
                    tmp_updated = n.get_next()[0].set_minmax_narrow(tmp_c & tmp_r)
                if not old_range == n.get_next()[0].get_minmax():
                    updated = True
                next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.PhiNode:
                assert (len(n.get_next()) == 1 \
                        and type(n.get_next()[0]) is constraint.VarNode)
                old_range = n.get_next()[0].get_minmax()
                for prv in n.get_prev():
                    if prv.get_minmax() is None:
                        continue                
                    tmp_updated = n.get_next()[0].set_minmax_narrow(prv.get_minmax())
                if not old_range == n.get_next()[0].get_minmax():
                    updated = True
                next_nodes.append(n.get_next()[0])
            elif type(n) is constraint.ArithmeticNode:
                assert (len(n.get_prev()) in [1, 2] and len(n.get_next()) == 1)
                if type(n.get_prev()[0]) is constraint.VarNode:
                    tmp_r1 = n.get_prev()[0].get_minmax()
                elif type(n.get_prev()[0]) is constraint.RangeNode:
                    tmp_r1 = n.get_prev()[0].get_interval()
                else: assert False
                if len(n.get_prev()) == 1:
                    tmp_r2 = tmp_r1
                elif type(n.get_prev()[1]) is constraint.VarNode:
                    tmp_r2 = n.get_prev()[1].get_minmax()
                elif type(n.get_prev()[1]) is constraint.RangeNode:
                    tmp_r2 = n.get_prev()[1].get_interval()
                else: assert False
                if (tmp_r1 is not None and tmp_r2 is not None):
                    tmp_r = arithmetic_op(tmp_r1, tmp_r2, n.get_op())
                    old_range = n.get_next()[0].get_minmax()
                    tmp_updated = n.get_next()[0].set_minmax_narrow(tmp_r)
                    if not old_range == n.get_next()[0].get_minmax():
                        updated = True
                    next_nodes.append(n.get_next()[0])
            else:
                print (type(n))
                assert False
    return narrow(cg, next_nodes, flag, updated)
    
def print_help():
    
    print ()
    print ("+--------------------------+")
    print ("|                          |")
    print ("|      Range Analysis      |")
    print ("|         by DrLC          |")
    print ("|                          |")
    print ("+--------------------------+")
    print ()
    print ("Return value range analysis.")
    print ()
    print ("Use this command to run.")
    print ("  python3 %s [-P|--path SSA_FILE_PATH] [-M|--main MAIN_FUNCTION_NAME]" % sys.argv[0])
    print ()
    exit(0)

def get_op():
    
    args = sys.argv
    if '-h' in args or '--help' in args:
        print_help()
    if len(args) == 1:
        path = '../benchmark/t2.ssa'
        main = 'foo'
    elif len(args) == 3:
        if args[1] in ['-P', '--path']:
            path = args[2]
            main = 'foo'
        elif args[1] in ['-M', '--main']:
            main = args[2]
            path = '../benchmark/t2.ssa'
        else:
            print_help()
    elif len(args) == 5:
        if args[1] in ['-P', '--path'] and args[3] in ['-M', '--main']:
            path = args[2]
            main = args[4]
        elif args[3] in ['-P', '--path'] and args[1] in ['-M', '--main']:
            main = args[2]
            path = args[4]
        else:
            print_help()
    else:
        print_help()
    return path, main
    
if __name__ == "__main__":
    
    path, main_func = get_op()
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    _cfg_ = {}
    for key in sym_tab.keys():
        _cfg_[key] = cfg.CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                             key)

    assert main_func in _cfg_.keys(), ("Function %s not found!" % main_func)
        
    argument = []
    for i in sym_tab['foo']['decl'].get_args():
        key = i.get_name()
        tmp_l = float(input("Lower bound of %s << " % key))
        tmp_r = float(input("Upper bound of %s << " % key))
        argument.append([tmp_l, tmp_r, key])
    cg = FCG(_cfg_, main_func, sym_tab)
    cg.set_entry_range(argument)
    
    flags = [False for i in cg.get_constraint_nodes()]
    updated = widen(cg, cg.get_entry_nodes(), flags, False)    
    while updated:
        flags = [False for i in cg.get_constraint_nodes()]
        updated = widen(cg, cg.get_entry_nodes(), flags, False)
    flags = [False for i in cg.get_constraint_nodes()]
    updated = narrow(cg, cg.get_entry_nodes(), flags, False)    
    while updated:
        flags = [False for i in cg.get_constraint_nodes()]
        updated = narrow(cg, cg.get_entry_nodes(), flags, False)
        
    print ("Return value range >> ", end='')
    if len(cg.get_return_node().get_minmax()) < 1:
        print ("NULL")
    else:
        print ("[", end='')
        print (cg.get_return_node().get_minmax()[0][0], end="")
        print (",", end="")
        print (cg.get_return_node().get_minmax()[0][1], end="")
        print ("]")