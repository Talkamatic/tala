from __future__ import unicode_literals


class ThirdPartyParser:
    def parse(self, string):
        raise Exception("Parse function in third party parse should be overridden")
