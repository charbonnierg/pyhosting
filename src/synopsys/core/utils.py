import re
import typing as t

from .syntax import FilterSyntax

# Regular expression used to identify placeholders within event names
regex = r"\{(.*?)\}"
replace_regex = r"\{\{(\w*?)\}\}"
pattern = re.compile(regex)
replace_pattern = re.compile(replace_regex)


def normalize_filter_subject(
    subject: str,
    syntax: FilterSyntax,
) -> t.Tuple[str, t.Dict[str, int]]:
    """Identify placeholders within event names and return
    a valid NATS subject as well as a list of placeholders.
    Each placeholder is a tuple of two elements:
        - index: The position of the placeholder within the NATS subject
        - name: The name of the placeholder

    Arguments:
        subject: an event name
        syntax: subject syntax

    Returns:
        a tuple of two elements: (subject, placeholders) where placeholders is a
        dict of string and ints.
    """
    placeholder_tokens: t.Dict[str, int] = {}
    sanitized_subject = str(subject)

    for match in list(pattern.finditer(sanitized_subject)):
        start = match.start()
        end = match.end()
        placeholder = subject[start : end - 1] + "}"
        # Replace in sanitized subject
        sanitized_subject = sanitized_subject.replace(placeholder, syntax.match_one)
        # Get placeholder name
        placeholder_name = placeholder[1:-1]
        if not placeholder_name:
            raise ValueError(f"Placeholder cannot be empty: '{subject}'")
        if syntax.match_sep in placeholder_name:
            raise ValueError(f"Invalid placeholder name: Contains '{syntax.match_sep}'")
        # Check that placeholder is indeed a whole token and not just a part
        try:
            next_char = subject[end]
        except IndexError:
            next_char = ""
        if start:
            previous_char = subject[start - 1]
        else:
            previous_char = ""
        if previous_char and previous_char != syntax.match_sep:
            raise ValueError("Placeholder must occupy whole token")
        if next_char and next_char != syntax.match_sep:
            raise ValueError("Placeholder must occupy whole token")
        # Append placeholder
        placeholder_tokens[placeholder_name] = subject.split(".").index(placeholder)

    return sanitized_subject, placeholder_tokens


def extract_subject_placeholders(
    subject: str,
    placeholders: t.Dict[str, int],
    syntax: FilterSyntax,
) -> t.Dict[str, str]:
    placeholders = placeholders.copy()
    tokens = subject.split(syntax.match_sep)
    values: t.Dict[str, str] = {}
    while placeholders:
        key, idx = placeholders.popitem()
        try:
            values[key] = tokens[idx]
        except IndexError as exc:
            raise ValueError(
                f"Invalid subject. Missing placeholder: {key} (index: {idx})"
            ) from exc
    return values


def render_subject(
    tokens: t.List[str],
    placeholders: t.Dict[str, int],
    context: t.Any,
    syntax: FilterSyntax,
) -> str:
    tokens = tokens.copy()
    placeholders = placeholders.copy()
    if context:
        for key, value in dict(context).items():
            if key in placeholders:
                tokens[placeholders.pop(key)] = value
    subject = syntax.match_sep.join(tokens)
    if placeholders:
        raise ValueError(
            f"Cannot render subject. Missing placeholders: {list(placeholders)}"
        )
    return subject


def filter_match(
    filter: str,
    subject: str,
    syntax: FilterSyntax,
) -> bool:
    """An approximative attempt to check if a filter matches a subject."""
    # Use default syntax when no syntax was provided
    if not subject:
        raise ValueError("Subject cannot be empty")
    if not filter:
        raise ValueError("Filter subject cannot be empty")
    # By default consider there is no match
    matches = False
    # If both subjects are equal
    if subject == filter:
        return True
    subject_tokens = subject.split(syntax.match_sep)
    filter_tokens = filter.split(syntax.match_sep)
    total_tokens = len(subject_tokens)
    # Iterate over each token
    for idx, token in enumerate(filter_tokens):
        # If tokens are equal, let's continue
        try:
            if token == subject_tokens[idx]:
                # Continue the iteration on next token
                continue
        except IndexError:
            # If filter is longer than subject then filter cannot match
            return False
        # If token is match_all (">" by default)
        if token == syntax.match_all:
            # Then we can return True
            return True
        # If token is mach_one ("*" by default)
        if token == syntax.match_one:
            matches = True
        # Else it means that subject do not match
        else:
            return False
    if token == syntax.match_one and (total_tokens - idx) > 1:
        return False
    return matches
