import itertools

def _strip_outer_parentheses(s):
    """Safely strips wrapping parentheses only if they truly match each other."""
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        matched = True
        for i in range(len(s) - 1):
            if s[i] == "(": depth += 1
            elif s[i] == ")": depth -= 1
            if i > 0 and depth == 0:
                matched = False
                break
        if matched:
            s = s[1:-1]
        else:
            break
    return s

def human_str_to_tree(s):
    """Recursively builds an AST directly from a human-readable string representation."""
    s = _strip_outer_parentheses(s)
    if len(s) == 1:
        return s
    
    depth = 0
    for i in range(len(s)):
        idx = len(s) - 1 - i
        c = s[idx]
        if c == ")": depth += 1
        elif c == "(": depth -= 1

        if depth == 0 and i < len(s) - 1:
            left = s[:idx]
            right = s[idx:]
            return (human_str_to_tree(left), human_str_to_tree(right))
        
    raise ValueError(f"Malformed expression: {s}")

def tree_to_last(tree, app="'"):
    """Converts an AST into a left-associative application form."""
    if isinstance(tree, str):
        return tree
    left, right = tree
    return app + tree_to_last(left, app) + tree_to_last(right, app)

def tree_to_bin_str(tree, bin_mapping, app_bin="0"):
    """Converts an AST into a binary string representation using a provided mapping."""
    if isinstance(tree, str):
        return bin_mapping[tree]
    left, right = tree
    return app_bin + tree_to_bin_str(left, bin_mapping, app_bin) + tree_to_bin_str(right, bin_mapping, app_bin)

def tree_to_human_str(tree):
    """Pretty-prints an AST back into a simplified left-associative human-readable string format."""
    if isinstance(tree, str):
        return tree
    left, right = tree

    left_str = tree_to_human_str(left)
    right_str = tree_to_human_str(right)

    if isinstance(right, tuple):
        right_str = f"({right_str})"
    
    return left_str + right_str

def human_str_to_bin_str(s, bin_mapping, app_bin="0"):
    """Convenience function to convert a human-readable string directly to a binary string."""
    return tree_to_bin_str(human_str_to_tree(s), bin_mapping, app_bin)

def human_str_to_last(s, app="'"):
    """Convenience function to convert a human-readable string directly to a left-associative application form."""
    return tree_to_last(human_str_to_tree(s), app)

def last_to_human_str(s, app="'"):
    """Converts a left-associative application form back into a human-readable string."""
    def tokenize(string):
        tokens, i = [], 0
        while i < len(string):
            if string[i:i+len(app)] == app:
                tokens.append(app); i += len(app)
            else:
                tokens.append(string[i]); i += 1
        return tokens
    
    def build_tree(tokens):
        if not tokens: return None
        token = tokens.pop(0)
        if token != app: return token
        return (build_tree(tokens), build_tree(tokens))
    
    return tree_to_human_str(build_tree(tokenize(s)))

def is_prefix_free(codes):
    """Checks if a set of codes is prefix-free."""
    for c1 in codes:
        for c2 in codes:
            if c1 != c2 and c2.startswith(c1):
                return False
    return True

def _generate_abstract_trees(n):
    """Generates all unique full binary trees with n leaves, favoring left-heavy trees first."""
    if n == 1:
        return [None]
    trees = []
    for i in range(n-1, 0, -1):
        left_trees = _generate_abstract_trees(i)
        right_trees = _generate_abstract_trees(n - i)
        for left in left_trees:
            for right in right_trees:
                trees.append((left, right))
    return trees

def _fill_tree(abstract_tree, leaf_iterator):
    """Replace None leaves in an abstract tree with values from the leaf iterator."""
    if abstract_tree is None:
        return next(leaf_iterator)
    left, right = abstract_tree
    return (_fill_tree(left, leaf_iterator), _fill_tree(right, leaf_iterator))

def enumerate_terms(n, combinators, bin_mapping, app="'", app_bin="0"):
    """Enumerates all unique terms of length n for a given set of combinators"""
    all_bin_tokens = list(bin_mapping.values()) + [app_bin]
    if not is_prefix_free(all_bin_tokens):
        raise ValueError("The provided binary codes are not prefix-free, which may lead to ambiguity.")
    
    abstract_trees = _generate_abstract_trees(n)
    results = []

    for combo in itertools.product(combinators, repeat=n):
        for abstract_tree in abstract_trees:
            tree = _fill_tree(abstract_tree, iter(combo))
            results.append({
                "human": tree_to_human_str(tree),
                "last": tree_to_last(tree, app),
                "bin": tree_to_bin_str(tree, bin_mapping, app_bin),
                "tree": tree
            })
    return results

COMBINATORS = {
    "I": {"arity": 1, "rewrite": lambda args: args[0]},
    "K": {"arity": 2, "rewrite": lambda args: args[0]},
    "S": {"arity": 3, "rewrite": lambda args: ((args[0], args[2]), (args[1], args[2]))},
    "W": {"arity": 2, "rewrite": lambda args: ((args[0], args[1]), args[1])},
    "B": {"arity": 3, "rewrite": lambda args: (args[0], (args[1], args[2]))},
    "C": {"arity": 3, "rewrite": lambda args: ((args[0], args[2]), args[1])},
}

def reduce_step(tree, rules):
    if isinstance(tree, str):
        return tree, False
    
    curr = tree
    args = []
    while isinstance(curr, tuple):
        args.append(curr[1])
        curr = curr[0]

    if curr in rules and len(args) >= rules[curr]["arity"]:
        arity = rules[curr]["arity"]
        used_args = args[-arity:][::-1]
        remaining_args = args[:-arity]

        res = rules[curr]["rewrite"](used_args)

        for arg in reversed(remaining_args):
            res = (res, arg)
        return res, True
    
    for i in range(len(args) - 1, -1, -1):
        new_arg, changed = reduce_step(args[i], rules)
        if changed:
            args[i] = new_arg
            res = curr
            for arg in reversed(args):
                res = (res, arg)
            return res, True
        
    return tree, False

def reduce_step_iterative(tree, rules):
    """Iteratively search for the leftmost reducible redex and perform one rewrite."""
    if isinstance(tree, str):
        return tree, False

    stack = [(tree, ())]
    while stack:
        node, path = stack.pop()
        if isinstance(node, str):
            continue

        curr = node
        args = []
        while isinstance(curr, tuple):
            args.append(curr[1])
            curr = curr[0]

        if curr in rules and len(args) >= rules[curr]["arity"]:
            arity = rules[curr]["arity"]
            used_args = args[-arity:][::-1]
            remaining_args = args[:-arity]

            res = rules[curr]["rewrite"](used_args)
            for arg in reversed(remaining_args):
                res = (res, arg)

            full = res
            for direction, sibling in reversed(path):
                if direction == "left":
                    full = (full, sibling)
                else:
                    full = (sibling, full)
            return full, True

        left, right = node
        stack.append((right, path + (("right", left),)))
        stack.append((left, path + (("left", right),)))

    return tree, False

def count_leaves(tree):
    """
    Counts leaves of an AST, leveraging memoization to handle
    highly-duplicated shared subtrees (DAGs) in O(n) unique nodes.
    """
    cache = {}

    def _count(node):
        node_id = id(node)
        if node_id in cache:
            return cache[node_id]
        
        if isinstance(node, str):
            return 1
        
        result = _count(node[0]) + _count(node[1])
        cache[node_id] = result
        return result
    
    return _count(tree)

def evaluate_combinator(tree, rules, max_steps=1000):
    """
    Reduce a single combinator term up to max_steps.
    Uses an explicit stack-based reduction step to avoid deep recursion.
    Returns (final_tree, steps_used, normalized).
    """
    steps = 0
    current_tree = tree
    while steps < max_steps:
        current_tree, changed = reduce_step_iterative(current_tree, rules)
        if not changed:
            return current_tree, steps, True
        steps += 1

    # If the reduction limit was reached, verify whether the result is already in normal form.
    _, changed = reduce_step_iterative(current_tree, rules)
    if not changed:
        return current_tree, steps, True
    return current_tree, steps, False


def evaluate_term(human_term, rules=COMBINATORS, max_steps=1000):
    """
    Parse a human-readable single term and simulate its evaluation.
    Useful for single-term experiments without deep recursive call stacks.
    """
    tree = human_str_to_tree(human_term)
    return evaluate_combinator(tree, rules, max_steps)
