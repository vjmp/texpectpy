import threading
import inspect
import re

from collections import defaultdict
from difflib import unified_diff
from StringIO import StringIO
from os.path import dirname, join, basename, splitext

NEWLINE = '\n'
SPACE = ' '
PREFIX = 'test_'
NEWLINE_PATTERN = re.compile(r'\r?\n')

def _lines(text):
    return NEWLINE_PATTERN.split(text)

def _less(name):
    return name[len(PREFIX):] if name.startswith(PREFIX) else name

def _dig(depth, frame):
    for _ in range(depth):
        frame = frame.f_back
    return frame

def _function_name(depth):
    frame = _dig(depth, inspect.currentframe())
    return _less(frame.f_code.co_name)

def _dirname(depth):
    frame = _dig(depth, inspect.currentframe())
    return dirname(frame.f_code.co_filename)

def _filename(depth):
    frame = _dig(depth, inspect.currentframe())
    filename = basename(frame.f_code.co_filename)
    root, _ = splitext(filename)
    return _less(root)

def _approved_file(name, distance=2):
    filename = '%s.%s.ok' % (_filename(distance), _less(name))
    return join(_dirname(distance), filename)

def _received_file(name, distance=2):
    filename = '%s.%s.nok' % (_filename(distance), _less(name))
    return join(_dirname(distance), filename)

def _both_paths(name):
    return _approved_file(name, 4), _received_file(name, 4)

def _read(filename):
    with open(filename) as source:
        return _lines(source.read())

def _write(filename, content):
    with open(filename, 'w+') as target:
        target.write(content)

def _as_tagset(tagset):
    return tuple(sorted(tagset if isinstance(tagset, set) else {tagset}))

class _StreamLogger(object):
    def __init__(self, stream):
        self._atomic = threading.RLock()
        self._stream = stream

    def is_valid(self):
        return True

    def log(self, message):
        with self._atomic:
            self._stream.write(message)
            if not message.endswith(NEWLINE):
                self._stream.write(NEWLINE)
            self._stream.flush()

class _Hold(object):
    strategy = None

class _Space(object):
    def __init__(self):
        self._atomic = threading.RLock()
        self._dimension = defaultdict(_Hold)

    def into_stream(self, tagsets, stream):
        strategy = _StreamLogger(stream)
        with self._atomic:
            for tagset in tagsets:
                self._dimension[tagset].strategy = strategy

    def log(self, tagsets, form, args):
        with self._atomic:
            strategies = set(self._dimension[x].strategy for x in tagsets)
        loggers = filter(lambda x: x, strategies)
        if loggers:
            prefix = SPACE.join(tagsets[0])
            message = "%s: %s" % (prefix, (form % args))
            for logger in loggers:
                logger.log(message)

_REGISTRY = _Space()

class At(object):
    def __init__(self, *tagsets):
        self._tagsets = tuple(_as_tagset(x) for x in tagsets)

    def __call__(self, form, *args):
        _REGISTRY.log(self._tagsets, form, args)
        return self

    log = __call__ # just alias for calling directly; do not remove

    def returns(self, *values):
        caller = _function_name(2)
        self.log("%s returns %r", caller, values)
        return values if len(values) > 1 else values[0]

    def into(self, stream):
        _REGISTRY.into_stream(self._tagsets, stream)
        return self

class Approve(object):
    def __init__(self, *tagsets):
        self._tagsets = tuple(_as_tagset(x) for x in tagsets)
        self._stream = None
        self._approved, self._received = _both_paths(_function_name(2))

    def __enter__(self):
        self._stream = StringIO()
        _REGISTRY.into_stream(self._tagsets, self._stream)
        return self

    def __exit__(self, kind, _value, _trace):
        if kind:
            return False
        try:
            golden_master = _read(self._approved)
        except IOError as err:
            if err.errno != 2:
                raise
            _write(self._received, self._stream.getvalue())
            raise AssertionError, "Missing %s file!" % self._approved
        else:
            sut_content = self._stream.getvalue()
            changed = NEWLINE.join(unified_diff(golden_master,
                _lines(sut_content), fromfile='Expected', tofile='Actual',
                n=1))
            if changed:
                _write(self._received, sut_content)
                raise AssertionError, "Content does not match:\n%s" % changed
        return False

    def __call__(self, fn):
        self._approved, self._received = _both_paths(fn.func_name)
        def wrapper(*args, **kvargs):
            with self:
                return fn(*args, **kvargs)
        return wrapper

