import re
import typing as t
from dataclasses import dataclass

# Regular expression used to identify placeholders within event names
regex = r"\{(.*?)\}"
replace_regex = r"\{\{(.*?)\}\}"
pattern = re.compile(regex)
replace_pattern = re.compile(replace_regex)


@dataclass
class FilterSyntax:
    match_sep: str = "."
    match_all: str = ">"
    match_one: str = "*"


DEFAULT_SYNTAX = FilterSyntax()


def substitute_placeholders(
    subject: str,
    context: t.Optional[t.Dict[str, str]] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> t.Tuple[str, t.Dict[str, int]]:
    """Identify placeholders within event names and return
    a valid NATS subject as well as a list of placeholders.
    Each placeholder is a tuple of two elements:
        - index: The position of the placeholder within the NATS subject
        - name: The name of the placeholder

    Arguments:
        subject: an event name
        context: values used to replace placeholders

    Returns:
        a tuple of two elements: (subject, placeholders) where placeholders is a
        dict of string and ints.
    """
    values = context or {}
    syntax = syntax or DEFAULT_SYNTAX
    placeholder_tokens: t.Dict[str, int] = {}
    sanitized_subject = str(subject)

    for match in list(replace_pattern.finditer(subject)):
        start = match.start()
        end = match.end()
        placeholder = subject[start:end]
        # Replace in sanitized subject
        sanitized_subject = sanitized_subject.replace(
            placeholder, values[placeholder[2:-2]]
        )

    for match in list(pattern.finditer(sanitized_subject)):
        start = match.start()
        end = match.end()
        placeholder = subject[start : end - 1] + "}"
        # Replace in sanitized subject
        sanitized_subject = sanitized_subject.replace(placeholder, syntax.match_one)
        # Get placeholder name
        placeholder_name = placeholder[1:-1]
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
    syntax: t.Optional[FilterSyntax] = None,
) -> t.Dict[str, str]:
    syntax = syntax or DEFAULT_SYNTAX
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
    context: t.Optional[t.Mapping[str, str]] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> str:
    tokens = tokens.copy()
    placeholders = placeholders.copy()
    syntax = syntax or DEFAULT_SYNTAX
    if context:
        for key, value in context.items():
            if key in placeholders:
                tokens[placeholders.pop(key)] = value
    subject = syntax.match_sep.join(tokens)
    if placeholders:
        raise KeyError(
            f"Cannot render subject. Missing placeholders: {list(placeholders)}"
        )
    return subject


def filter_match(  # NOSONAR[python:S3776]
    filter: str,
    subject: str,
    syntax: t.Optional[FilterSyntax] = None,
) -> bool:
    """An approximative attempt to check if a filter matches a subject."""
    # Use default syntax when no syntax was provided
    syntax = syntax or DEFAULT_SYNTAX
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
            # If tokens are different, then let's continue our if/else statements
            matches = False
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
