# coding: utf-8

from tala.languages import ENGLISH, SWEDISH
from tala.rasa.constants import NEGATIVE_INTENT
from tala.rasa.generating.common_example import CommonExample


class SortNotSupportedException(Exception): pass


class Examples(object):
    @property
    def negative(self):
        raise NotImplementedError

    @property
    def integer(self):
        raise NotImplementedError

    @property
    def string(self):
        raise NotImplementedError

    @property
    def datetime(self):
        raise NotImplementedError

    def get_builtin_sort_examples(self, sort):
        if sort.is_domain_sort():
            return []
        if sort.is_integer_sort():
            return self.integer
        if sort.is_string_sort():
            return self.string
        if sort.is_datetime_sort():
            return self.datetime
        raise SortNotSupportedException(
            "Builtin sort '%s' is not yet supported together with RASA" % sort.get_name())

    @staticmethod
    def from_language(language_code):
        examples = {
            ENGLISH: EnglishExamples(),
            SWEDISH: SwedishExamples(),
        }
        return examples[language_code]


class EnglishExamples(Examples):
    @property
    def negative(self):
        phrases = ["aboard", "about", "above", "across", "after", "against", "along", "among", "as", "at",
                   "on", "atop", "before", "behind", "below", "beneath", "beside", "between", "beyond", "but",
                   "by", "come", "down", "during", "except", "for", "from", "in", "inside", "into", "less",
                   "like", "near", "of", "off", "on", "onto", "opposite", "out", "outside", "over", "past",
                   "save", "short", "since", "than", "then", "through", "throughout", "to", "toward", "under",
                   "underneath", "unlike", "until", "up", "upon", "with", "within", "without", "worth", "is",
                   "it", "the", "a", "am", "are", "them", "this", "that", "I", "you", "he", "she", "they",
                   "them", "his", "her", "my", "mine", "their", "your", "us", "our"]
        question_phrases = ["how", "how's", "how is", "how's the", "how is the", "when", "when's", "when is",
                            "when is the", "when's the", "what", "what is", "what's", "what's the",
                            "what is the", "why", "why is", "why's", "why is the", "why's the"]
        action_phrases = ["do", "make", "tell", "start", "stop", "enable", "disable", "raise", "lower",
                          "decrease", "increase", "act", "determine", "say", "ask", "go", "shoot", "wait",
                          "hang on", "ok", "show", "help"]
        intent = NEGATIVE_INTENT
        for phrase in phrases:
            yield CommonExample(intent, phrase)
        for phrase in question_phrases:
            yield CommonExample(intent, phrase)
        for phrase in action_phrases:
            yield CommonExample(intent, phrase)

    @property
    def integer(self):
        return ["0", "99", "1224", "a hundred and fifty seven", "three", "two thousand fifteen"]

    @property
    def string(self):
        return [
            "single", "double word", "three in one", "hey make it four", "the more the merrier five",
            "calm down and count to six", "bring them through to the jolly seven",
            "noone counts toes like an eight toed guy", "it matters to make sense for nine of us",
            "would you bring ten or none to a desert island"
        ]

    @property
    def datetime(self):
        return [
            "today",
            "Monday March 18",
            "the 1st of March",
            "11:45 am",
            "next 3 weeks",
            "in ten minutes",
            "March 20th at 22:00",
            "March twentieth at 10 pm"
        ]


class SwedishExamples(Examples):
    @property
    def negative(self):
        phrases = ["om", u"ovanför", u"tvärsöver", "efter", "mot", "bland", "runt", "som", u"på", "vid", u"ovanpå",
                   u"före", "bakom", "nedan", "under", "bredvid", "mellan", "bortom", "men", "av", "trots", "ner",
                   u"förutom", u"för", u"från", "i", "inuti", "in i", u"nära", u"nästa", "mittemot", "ut", u"utanför",
                   u"över", "per", "plus", "runt", "sedan", u"än", "genom", "tills", "till", "mot", "olik", "upp",
                   "via", "med", "inom", "utan", u"är", "vara", "den", "det", "en", "ett", "dem", "denna", "detta",
                   "jag", "du", "ni", "han", "hon", "hen", "de", "hans", "hennes", "hens", "min", "mina", "deras", "er",
                   "din", "vi", "oss", u"vår"]
        question_phrases = ["hur", u"hur är", u"när", u"när är", "vad", u"vad är", u"varför", u"varför är"]
        action_phrases = [u"gör", u"göra", "skapa", u"berätta", "tala om", u"börja", "starta", "sluta", "stopp",
                          "stanna", u"sätt på", u"stäng av", u"höj", u"sänk", u"öka", "minska", "agera", u"bestäm",
                          u"säg", u"fråga", u"gå", u"kör", u"vänta", "ok", "visa", u"hjälp"]
        intent = NEGATIVE_INTENT
        for phrase in phrases:
            yield CommonExample(intent, phrase)
        for phrase in question_phrases:
            yield CommonExample(intent, phrase)
        for phrase in action_phrases:
            yield CommonExample(intent, phrase)

    @property
    def integer(self):
        return ["0", "99", "1224", "etthundratjugosju", "tre", u"tvåtusenfemton"]

    @property
    def string(self):
        return [
            "enkel", "dubbelt ord", "det blir tre", u"fyra på en gång", u"ju fler desto bättre fem",
            u"håll andan och räkna till sex", "led dem fram till de glada sju",
            u"ingen räknar tår som den med åtta tår", u"det spelar roll att det låter rimligt för nio",
            u"tar du med tio eller inga till en öde ö"
        ]

    @property
    def datetime(self):
        return [
            "idag",
            u"måndag 18 mars",
            "1:a mars",
            "klockan 11.45",
            u"följande tre veckor",
            "om tio minuter",
            u"20:e mars vid 22.00",
            u"tjugonde mars vid tio på kvällen"
        ]
