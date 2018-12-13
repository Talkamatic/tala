def readable_list(elements):
    if len(elements) == 0:
        return ""
    if len(elements) == 1:
        return elements[0]
    return "%s and %s" % (", ".join(elements[:-1]), elements[-1])
