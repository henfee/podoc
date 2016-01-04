# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging

# from six import string_types

from podoc.tree import Node, TreeTransformer
from podoc.plugin import IPlugin
# from podoc.utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------------

# def _remove_meta(d):
#     if isinstance(d, dict):
#         return {k: _remove_meta(v) for k, v in d.items() if k != 'm'}
#     elif isinstance(d, list):
#         return [_remove_meta(v) for v in d]
#     else:
#         return d


# def ae(a, b):
#     if isinstance(a, (list, dict)):
#         assert _remove_meta(a) == _remove_meta(b)
#     else:
#         assert a == b


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

# List of allowed Pandoc block names.
PANDOC_BLOCK_NAMES = (
    'Plain',
    'Para',
    'Header',
    'CodeBlock',
    'BlockQuote',
    'BulletList',
    'OrderedList',
    # The following are not supported yet in podoc.
    # 'RawBlock',
    # 'DefinitionList',
    # 'HorizontalRule',
    # 'Table',
    # 'Div',
)


# List of allowed Pandoc inline names.
PANDOC_INLINE_NAMES = (
    # 'Str',
    'Emph',
    'Strong',
    'Code',
    'Link',
    'Image',
    # The following are not supported yet in podoc.
    # 'LineBreak',
    # 'Math',
    # 'Strikeout',
    # 'Space',
)


class ASTNode(Node):
    def is_block(self):
        return self.name in PANDOC_BLOCK_NAMES

    def is_inline(self):
        return self.name in PANDOC_INLINE_NAMES

    def validate(self):
        if self.is_inline():
            # The children of an Inline node cannot be blocks.
            for child in self.children:
                if hasattr(child, 'is_block'):
                    assert not child.is_block()


#------------------------------------------------------------------------------
# AST <-> pandoc
#------------------------------------------------------------------------------

def _node_dict(node, children=None):
        return {'t': node.name,
                # 'm': node.meta,
                'c': children or node.inner_contents}


class PodocToPandoc(object):
    def __init__(self):
        self.transformer = TreeTransformer()
        self.transformer.set_fold(lambda _: _)
        for m in dir(self):
            if m.startswith('transform_'):
                self.transformer.register(getattr(self, m))

    def transform_Node(self, node):
        return _node_dict(node)

    def transform_str(self, text):
        return {'t': 'Str', 'c': text}

    def transform_Header(self, node):
        children = [node.level, ['', [], []], node.inner_contents]
        return _node_dict(node, children)

    def transform_CodeBlock(self, node):
        children = [['', [node.lang], []], node.inner_contents]
        return _node_dict(node, children)

    def transform_OrderedList(self, node):
        children = [[node.start,
                    {"t": node.style, "c": []},
                    {"t": node.delim, "c": []}], node.inner_contents]
        return _node_dict(node, children)

    def transform_Link(self, node):
        children = [node.inner_contents, [node.url, '']]
        return _node_dict(node, children)

    def transform_Image(self, node):
        children = [node.inner_contents, [node.url, '']]
        return _node_dict(node, children)

    def transform_Code(self, node):
        children = [['', [], []], node.inner_contents]
        return _node_dict(node, children)

    def transform(self, ast):
        blocks = self.transformer.transform(ast)['c']
        return [{'unMeta': {}}, blocks]


class PandocToPodoc(object):
    pass


#------------------------------------------------------------------------------
# AST plugin
#------------------------------------------------------------------------------

class ASTPlugin(IPlugin):
    """The file format is JSON, same as the pandoc json format."""
    def attach(self, podoc):
        # An object in the language 'ast' is an instance of AST.
        podoc.register_lang('ast', file_ext='.json',
                            open_func=self.open, save_func=self.save)

    def open(self, path):
        """Open a .json file and return an AST instance."""
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            ast_obj = json.load(f)
        assert isinstance(ast_obj, list)
        # ast = AST.from_dict(ast_obj)
        # assert isinstance(ast, AST)
        # return ast

    def save(self, path, ast):
        """Save an AST instance to a JSON file."""
        # assert isinstance(ast, AST)
        ast_obj = ast.to_dict()
        assert isinstance(ast_obj, list)
        logger.debug("Save JSON file `%s`.", path)
        # with open(path, 'w') as f:
        #     json.dump(ast_obj, f, sort_keys=True, indent=2)
        #     # Add a new line at the end.
        #     f.write('\n')
