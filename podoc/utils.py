# -*- coding: utf-8 -*-

"""Utility functions."""

from contextlib import contextmanager
import json
import logging
import os
import os.path as op
import sys

from six import string_types, StringIO, PY2

logger = logging.getLogger(__name__)


if PY2:
    # This exception is only defined in Python 3.
    class FileNotFoundError(OSError):  # pragma: no cover
        pass


#------------------------------------------------------------------------------
# Bunch
#------------------------------------------------------------------------------

class Bunch(dict):
    """A dict with additional dot syntax."""
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        return Bunch(super(Bunch, self).copy())


#------------------------------------------------------------------------------
# File I/O
#------------------------------------------------------------------------------

def open_text(path):
    assert op.exists(path)
    with open(path, 'r') as f:
        out = f.read()
    return out


def save_text(path, contents):
    with open(path, 'w') as f:
        return f.write(contents)


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


#------------------------------------------------------------------------------
# Path
#------------------------------------------------------------------------------

def _normalize_path(path):
    assert isinstance(path, string_types)
    assert path
    path = op.realpath(op.expanduser(path))
    return path


class Path(object):
    def __init__(self, path):
        self.path = _normalize_path(path)

    def __repr__(self):
        return '<Path `{}`>'.format(self.path)

    def exists(self):
        return op.exists(self.path)


#------------------------------------------------------------------------------
# Testing utils
#------------------------------------------------------------------------------

def get_test_file_path(lang, filename):
    curdir = op.realpath(op.dirname(__file__))
    # Construct the directory name for the language and test filename.
    dirname = op.realpath(op.join(curdir, lang))
    path = op.join(dirname, 'test_files', filename)
    assert op.exists(path)
    return path


def _are_dict_equal(t0, t1):
    """Assert the equality of nested dicts, removing all private fields."""
    if isinstance(t0, list):
        assert isinstance(t1, list)
        return all(_are_dict_equal(c0, c1) for c0, c1 in zip(t0, t1))
    elif isinstance(t0, (string_types, int)):
        assert isinstance(t1, (string_types, int))
        return t0 == t1
    assert isinstance(t0, dict)
    assert isinstance(t1, dict)
    k0 = {k for k in t0.keys() if not k.startswith('_')}
    k1 = {k for k in t1.keys() if not k.startswith('_')}
    assert k0 == k1
    return all(_are_dict_equal(t0[k], t1[k]) for k in k0)


def _remove_private(d):
    if isinstance(d, dict):
        return {k: _remove_private(v)
                for k, v in d.items()
                if not k.startswith('_')}
    elif isinstance(d, list):
        return [_remove_private(c) for c in d]
    return d


def assert_equal(p0, p1):
    if isinstance(p0, string_types):
        assert p0.rstrip('\n') == p1.rstrip('\n')
    elif isinstance(p0, dict):
        if not _are_dict_equal(p0, p1):
            assert _remove_private(p0) == _remove_private(p1)
    else:
        assert p0 == p1


#------------------------------------------------------------------------------
# pandoc wrapper
#------------------------------------------------------------------------------

# TODO: commonmark instead
PANDOC_MARKDOWN_FORMAT = ('markdown_strict+'
                          'fancy_lists+'
                          'startnum+'
                          'backtick_code_blocks+'
                          'hard_line_breaks+'
                          'tex_math_dollars'
                          )


def pandoc(obj, to, **kwargs):
    """Convert a string or a file with pandoc."""
    import pypandoc
    return pypandoc.convert(obj, to, **kwargs)


def get_pandoc_formats():
    import pypandoc
    return pypandoc.get_pandoc_formats()


def has_pandoc():  # pragma: no cover
    try:
        import pypandoc
        pypandoc.get_pandoc_version()
        return True
    except ImportError:
        logger.debug("pypandoc is not installed.")
    except FileNotFoundError:
        logger.debug("pandoc is not installed.")
    return False


def generate_json_test_files():  # pragma: no cover
    """Regenerate all *.json files in ast/test_files."""
    curdir = op.realpath(op.dirname(__file__))
    directory = op.join(curdir, 'markdown', 'test_files')
    files = os.listdir(directory)
    for file in files:
        if file.endswith('.md'):
            path = op.join(directory, file)
            out = pandoc(open_text(path), 'json',
                         format=PANDOC_MARKDOWN_FORMAT)
            base = op.splitext(file)[0]
            path_json = op.join(curdir, 'ast', 'test_files', base + '.json')
            with open(path_json, 'w') as fw:
                d = json.loads(out)
                json.dump(d, fw, sort_keys=True, indent=4)
