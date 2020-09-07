from tala.utils.as_json import AsJSONMixin


class TISNode(AsJSONMixin):
    def pretty_string_new(self, path):
        output = ""
        for attr in sorted(self.__dict__.keys()):
            value = self.__dict__[attr]
            path.append(str(attr))
            output += self.value_string_new(path, value)
            path.pop()
        return output

    def value_string_new(self, path, value):
        try:
            return value.pretty_string_new(path)
        except AttributeError:
            string_value = str(value)
            if len(string_value) > 0 and string_value[0] != "_":
                return "\n" + ".".join(path) + ": " + string_value
            return ""

    def pretty_string(self, indentation_level):
        output = ""
        for attr in sorted(self.__dict__.keys()):
            value = self.__dict__[attr]
            output += "\n" + self.indent(indentation_level + 1)
            output += attr + ": " + self.value_string(value, indentation_level + 1)
        return output

    def value_string(self, value, indentation_level):
        try:
            return value.pretty_string(indentation_level)
        except AttributeError:
            return str(value)

    def indent(self, indentation_level):
        return "\t" * indentation_level
