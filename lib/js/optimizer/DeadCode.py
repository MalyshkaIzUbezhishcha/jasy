#
# JavaScript Tools - Dead Code Removal
# Copyright 2010 Sebastian Werner
#

import logging

def optimize(node):
    """ Reprocesses JavaScript to remove dead paths """
    optimized = False
    
    # Process from inside to outside
    for child in node:
        if optimize(child):
            optimized = True
        
    # Optimize if cases
    if node.type == "if":
        check = __checkCondition(node.condition)
        if check is not None:
            optimized = True
            
            if check is True:
                node.parent.replace(node, node.thenPart)
                
            elif check is False:
                if hasattr(node, "elsePart"):
                    node.parent.replace(node, node.elsePart)
                else:
                    node.parent.remove(node)
    
    # Optimize hook statement
    if node.type == "hook":
        check = __checkCondition(node[0])
        if check is not None:
            optimized = True
        
            if check is True:
                node.parent.replace(node, node[1])
            elif check is False:
                node.parent.replace(node, node[2])
                
    # Optimize switch statement
    if node.type == "switch" and node.discriminant.type in ("string", "number"):
        discriminant = node.discriminant.value
        fallback = None
        matcher = None
        allowed = ["default", "case"]
        
        for child in node:
            # Require that every case block ends with a break (no fall-throughs)
            if child.type == "case":
                block = child[len(child)-1]
                if len(block) == 0 or block[len(block)-1].type != "break":
                    logging.warn("Could not optimize switch statement (at line %s) because of fallthrough break statement." % node.line)
                    return False

            if child.type == "default":
                fallback = child.statements

            elif child.type == "case" and child.label.value == discriminant:
                matcher = child.statements
                
                # Remove break statement
                matcher.pop()
            
        if matcher or fallback:
            if not matcher:
                matcher = fallback
                
            node.parent.replace(node, matcher)
            optimized = True
    
    return optimized



#
# Implementation
#

def __checkCondition(node):
    if node.type == "false":
        return False
    elif node.type == "true":
        return True
    elif node.type == "eq":
        return __compareNodes(node[0], node[1])
    elif node.type == "ne":
        return __invertResult(__compareNodes(node[0], node[1]))
    elif node.type == "not":
        return __invertResult(__checkCondition(node[0]))
    elif node.type == "and":
        return __checkCondition(node[0]) and __checkCondition(node[1])
    elif node.type == "or":
        return __checkCondition(node[0]) or __checkCondition(node[1])

    return None


def __invertResult(result):
    if type(result) == bool:
        return not result
    return result


def __compareNodes(a, b):
    if a.type == b.type:
        if a.type in ("string","number"):
            return a.value == b.value
        elif a.type == "true":
            return True
        elif b.type == "false":
            return False    
    elif a.type in ("true","false") and b.type in ("true","false"):
        return False

    return None
    