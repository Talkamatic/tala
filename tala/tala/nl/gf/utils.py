import os
import re


class GrammarSanityException(Exception):
    pass


BIND = "&+"
META = "#?#"

TOKENISE_RE = re.compile(r"\s*(p\.m\.|a\.m\.|\d{1,2}\:\d{2}|[\w0-9_\\\-']+|\S)\s*", flags=re.UNICODE)

PUNCTUATION_RE = re.compile(r"\s+([!,.?])")

NL_PLACEHOLDER_PREFIX = "nl_placeholder"
SEM_PLACEHOLDER_PREFIX = "sem_placeholder"
PLACEHOLDER_NAME_PREFIX = "placeholder"

UNFORMATTED_PLACEHOLDER_REGEXP = "_%s_\w+(\s|$)"
NL_PLACEHOLDER_REGEXP = UNFORMATTED_PLACEHOLDER_REGEXP % NL_PLACEHOLDER_PREFIX
SEM_PLACEHOLDER_REGEXP = UNFORMATTED_PLACEHOLDER_REGEXP % SEM_PLACEHOLDER_PREFIX

MAX_NUM_PLACEHOLDERS = 10


def tokenise(s):
    tokenised = [_f for _f in TOKENISE_RE.split(s) if _f]
    return tokenised


def str_lin(lin, marked=None):
    return " ; ".join(str_phrase(phrase, marked) for phrase in lin)


def lin_to_moves(lin):
    moves = [move.strip() for move in lin_to_move(lin).split(";") if META not in move]
    return moves


def lin_to_move(lin):
    return "".join(concat_string_tokens(lin))


def concat_string_tokens(tokens):
    try:
        first_quote_index = tokens.index('"')
        tokens_from_first_quote = tokens[first_quote_index + 1:]
        second_quote_index = tokens_from_first_quote.index('"')
    except ValueError:
        return tokens
    tokens_between_quotes = tokens_from_first_quote[0:second_quote_index]
    string_token = " ".join(tokens_between_quotes)
    tokens_before_first_quote = tokens[0:first_quote_index]
    tokens_after_second_quote = tokens_from_first_quote[second_quote_index + 1:]
    result = tokens_before_first_quote
    result.append('"')
    result.append(string_token)
    result.append('"')
    result.extend(concat_string_tokens(tokens_after_second_quote))
    return result


def str_phrase(phrase, marked=None):
    phrase = bind_tokens(phrase)
    str = " ".join(str_token(token, marked) for token in phrase)
    str = PUNCTUATION_RE.sub(r"\1", str)
    return str


def str_token(token, marked=None):
    if isinstance(token, str):
        return token
    word, path = token
    star = "*" if is_path(marked) and startswith(path, marked) else ""
    return star + word + "/" + str_path(path)


def is_path(path):
    return (isinstance(path, tuple) and all(isinstance(n, int) and n >= 1 for n in path))


def bind_tokens(tokens):
    result = []
    binding = False
    for token in tokens:
        if binding:
            result[-1] += token
            binding = False
        elif token == BIND:
            binding = True
        else:
            result.append(token)
    return result


def startswith(sequence, prefix):
    return sequence[:len(prefix)] == prefix


def str_path(path):
    if path is None:
        return str(None)
    return "".join(map(str, path))


def assert_grammar_is_lower_case(filename):
    if not os.path.exists(filename):
        return
    with open(filename) as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            line = without_comments(line)
            expected_lower_case_tokens = language_tokens(line)
            for expected_lower_case_text in expected_lower_case_tokens:
                if not expected_lower_case_text == expected_lower_case_text.lower():
                    msg_string = "Expected lower case grammar %r, but found deviation on line %s: %r"
                    msg = msg_string % (filename, line_number, expected_lower_case_text)
                    raise GrammarSanityException(msg)


def language_token_is_constant(entry):
    return entry.startswith("_") and entry.endswith("_")


def language_token_is_nl_placeholder(token):
    return re.search(NL_PLACEHOLDER_REGEXP, token) is not None


def remove_nl_placeholders_from_string(string):
    return re.sub(NL_PLACEHOLDER_REGEXP, "", string)


def remove_sem_placeholders_from_string(string):
    return re.sub(SEM_PLACEHOLDER_REGEXP, "", string)


def nl_user_answer_placeholder_of_sort(sort, index):
    return "_%s_%s%s_" % (NL_PLACEHOLDER_PREFIX, sort, index)


def semantic_user_answer_placeholder_of_sort(sort, index):
    return "_%s_%s%s_" % (SEM_PLACEHOLDER_PREFIX, sort, index)


def name_of_user_answer_placeholder_of_sort(sort, index):
    return "%s_%s%s" % (PLACEHOLDER_NAME_PREFIX, sort, index)


def without_comments(line):
    return line.split("--")[0]


def language_tokens(line):
    tokens = line.split('"')
    language_tokens = tokens[1::2]  # every odd element
    return [token for token in language_tokens if not language_token_is_constant(token)]


def lower_gf_string_but_insert_capit_and_bind(string):
    lowered_string = '"'
    previous_char = None
    for char in string:
        if not char.isupper():
            lowered_string += char
        else:
            is_char_in_mid_of_word = previous_char and not previous_char.isspace()
            if is_char_in_mid_of_word:
                lowered_string += '" ++ CAPIT ++ BIND ++ "%s' % char.lower()
            else:
                lowered_string += '" ++ CAPIT ++ "%s' % char.lower()

        previous_char = char
    lowered_string += '"'
    if "CAPIT" in lowered_string:
        return "(%s)" % lowered_string
    return lowered_string
