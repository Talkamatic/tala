import tala.nl.gf.resource
from tala.nl.gf.resource import VP, SINGULAR, PLURAL, MASCULINE, FEMININE  # noqa: F401


class NP(tala.nl.gf.resource.NP):
    def __init__(self, indefinite, gender, number=SINGULAR):
        self.indefinite = indefinite
        self.number = number
        self.gender = gender
        self.definite = None


top = [NP("avvia visualizzazione", "xxxxxxxxxxx"), "cancella", "ricomincia", "stop"]

up = ["indietro", "torna indietro"]
