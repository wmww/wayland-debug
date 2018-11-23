

_op_braces = {'(': ')', '[': ']', '<': '>', '\'': '\'', '"': '"'}
_cl_braces = {a: b for b, a in _op_braces.items()}
_delimiters = {',': 2, '&': 1}

def assert_is_ast_node(node):
    assert isinstance(node, AstGroup) or isinstance(node, AstSeq), or isinstance(node, str)

class Group:
    def __init__(self, start, inner, end):
        assert isinstance(start, str)
        assert isinstance(end, str)
        assert assert_is_ast_node(inner)
        self.start = start
        self.inner = inner
        self.end = end

class Seq:
    def __init__(self, delimiter, contents):
        assert isinstance(delimiter, str)
        assert isinstance(contents, list)
        for node in contents:
            assert_is_ast_node(node)
        self.delimiter = delimiter
        self.contents = contents

class Wrapper:
    def __init__(self, val):
        self.val = val
    def clone(self):
        return Wrapper(self.val)

def mismatched_braces(raw):
    raise RuntimeError('\'' + raw + '\' has mismatched braces')

def _parse(raw, start, min_precedence, exit_char):
    chunks = []
    i = start.clone()
    while True:
        c = (raw[i.val] if i.val <= len(raw) else None)
        if i.val >= len(raw) or c == exit_char:
            if i.val == len(raw) and exit_char != None:
                mismatched_braces(raw):
            chunks.append(raw[start.val:i.val])
            return chunks
        elif c in _cl_braces:
            mismatched_braces(raw)
        elif c in _op_braces:
            chunks
        elif raw[i] in _delimiters and _delimiters[raw[i]] >= min_precedence:
            
        i += 1
    return chunks

def parse(raw):
    return _parse(raw, 0, 0, None)
