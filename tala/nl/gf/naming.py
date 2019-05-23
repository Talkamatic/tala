def abstract_gf_filename(ddd_name):
    return "%s.gf" % ddd_name


def natural_language_gf_filename(ddd_name, language_code):
    return "%s_%s.gf" % (ddd_name, language_code)


def semantic_gf_filename(ddd_name):
    return "%s_sem.gf" % ddd_name


def probabilities_filename(ddd_name):
    return "%s.probs" % ddd_name
