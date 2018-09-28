from pprint import pprint
from treelib import Node, Tree

def tree_from_token(root):
    def add_children(root, tree):
        for c in root.children:
            tree.create_node("{}:{}/{}".format(c.dep_,c,c.pos_), hash(c), parent=hash(root), data=c)
            add_children(c, tree)

    tree = Tree()
    tree.create_node("{}/{}".format(root, root.pos_), hash(root), data=root)
    add_children(root, tree)
    return tree



def tree_from_doc(doc):            
    # 1. Find root
    root = [t for t in doc if t.dep_ == 'ROOT'][0]
    return tree_from_token(root)

def tree_from_annotation(annot):            
    doc = nlp(annot[0])
    labels = annot[1]['entities']
    root = [t for t in doc if t.dep_ == 'ROOT'][0]
    return tree_from_token_with_labels(root, labels)
