# coding: utf-8

from jinja2 import Template

from tala.nl.languages import ENGLISH, SWEDISH, SPANISH


class SortNotSupportedException(Exception):
    pass


class Examples(object):
    @property
    def negative(self):
        raise NotImplementedError()

    @property
    def integer(self):
        raise NotImplementedError()

    @property
    def string(self):
        raise NotImplementedError()

    @property
    def datetime(self):
        raise NotImplementedError()

    @property
    def person_name(self):
        raise NotImplementedError()

    @property
    def yes(self):
        raise NotImplementedError()

    @property
    def no(self):
        raise NotImplementedError()

    @property
    def top(self):
        raise NotImplementedError()

    @property
    def up(self):
        raise NotImplementedError()

    @property
    def answer_templates(self):
        yield Template('{{ name }}')

    @property
    def answer_negation_templates(self):
        raise NotImplementedError()

    def get_builtin_sort_examples(self, sort):
        if sort.is_domain_sort():
            return []
        if sort.is_integer_sort():
            return self.integer
        if sort.is_string_sort():
            return self.string
        if sort.is_datetime_sort():
            return self.datetime
        if sort.is_person_name_sort():
            return self.person_name
        raise SortNotSupportedException("Builtin sort '%s' is not yet supported together with RASA" % sort.get_name())

    @staticmethod
    def from_language(language_code):
        examples = {ENGLISH: EnglishExamples(), SWEDISH: SwedishExamples(), SPANISH: SpanishExamples()}
        return examples[language_code]


class EnglishExamples(Examples):
    @property
    def negative(self):
        phrases = [
            "aboard", "about", "above", "across", "after", "against", "along", "among", "as", "at", "on", "atop",
            "before", "behind", "below", "beneath", "beside", "between", "beyond", "but", "by", "come", "down",
            "during", "except", "for", "from", "in", "inside", "into", "less", "like", "near", "of", "off", "on",
            "onto", "opposite", "out", "outside", "over", "past", "save", "short", "since", "than", "then", "through",
            "throughout", "to", "toward", "under", "underneath", "unlike", "until", "up", "upon", "with", "within",
            "without", "worth", "is", "it", "the", "a", "am", "are", "them", "this", "that", "I", "you", "he", "she",
            "they", "them", "his", "her", "my", "mine", "their", "your", "us", "our"
        ]
        question_phrases = [
            "how", "how's", "how is", "how's the", "how is the", "when", "when's", "when is", "when is the",
            "when's the", "what", "what is", "what's", "what's the", "what is the", "why", "why is", "why's",
            "why is the", "why's the"
        ]
        action_phrases = [
            "do", "make", "tell", "start", "stop", "enable", "disable", "raise", "lower", "decrease", "increase", "act",
            "determine", "say", "ask", "go", "shoot", "wait", "hang on", "ok", "show", "help"
        ]
        for phrase in phrases:
            yield phrase
        for phrase in question_phrases:
            yield phrase
        for phrase in action_phrases:
            yield phrase

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
            "today", "Monday March 18", "the 1st of March", "11:45 am", "next 3 weeks", "in ten minutes",
            "March 20th at 22:00", "March twentieth at 10 pm"
        ]

    @property
    def person_name(self):
        return [
            "John", "Mary", "James", "Jack", "Harry", "Tom", "William", "George", "Charlie", "Josh", "Lewis", "Michael",
            "Ben", "Chris", "Robert", "Mark", "Scott", "Beth", "Alice", "Jessica", "Grace", "Rachel", "Anna",
            "Kathrine", "Emily", "Megan", "Olivia", "Rebecca", "Smith", "Brown", "Wilson", "Stewart", "Thompson",
            "Anderson", "Murray", "Morrison", "Walker", "Watson", "Miller", "Campbell", "Hunter", "Gray", "Cameron",
            "Mitchell", "Black", "Allan", "Marshall", "Harris Duncan", "Max Mackenzie", "Ethan Hamilton",
            "Sophie Simpson", "Lucy Wright", "Emma Murphy", "Charlotte Jones", "Thomas Gordon"
        ]

    @property
    def yes(self):
        return [
            "yes", "yeah", "yep", "sure", "ok", "of course", "very well", "fine", "right", "excellent", "okay",
            "perfect", "I think so"
        ]

    @property
    def no(self):
        return [
            "no", "nope", "no thanks", "no thank you", "negative", "don't want to", "don't", "do not", "please don't"
        ]

    @property
    def top(self):
        return [
            "forget it", "never mind", "get me out of here", "start over", "beginning", "never mind that", "restart"
        ]

    @property
    def up(self):
        return [
            "go back", "back", "previous", "back to the previous", "go to the previous", "go back to the previous one"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('not {{ name }}')


class SwedishExamples(Examples):
    @property
    def negative(self):
        phrases = [
            "om", u"ovanför", u"tvärsöver", "efter", "mot", "bland", "runt", "som", u"på", "vid", u"ovanpå", u"före",
            "bakom", "nedan", "under", "bredvid", "mellan", "bortom", "men", "av", "trots", "ner", u"förutom", u"för",
            u"från", "i", "inuti", "in i", u"nära", u"nästa", "mittemot", "ut", u"utanför", u"över", "per", "plus",
            "runt", "sedan", u"än", "genom", "tills", "till", "mot", "olik", "upp", "via", "med", "inom", "utan", u"är",
            "vara", "den", "det", "en", "ett", "dem", "denna", "detta", "jag", "du", "ni", "han", "hon", "hen", "de",
            "hans", "hennes", "hens", "min", "mina", "deras", "er", "din", "vi", "oss", u"vår"
        ]
        question_phrases = ["hur", u"hur är", u"när", u"när är", "vad", u"vad är", u"varför", u"varför är"]
        action_phrases = [
            u"gör", u"göra", "skapa", u"berätta", "tala om", u"börja", "starta", "sluta", "stopp", "stanna", u"sätt på",
            u"stäng av", u"höj", u"sänk", u"öka", "minska", "agera", u"bestäm", u"säg", u"fråga", u"gå", u"kör",
            u"vänta", "ok", "visa", u"hjälp"
        ]
        for phrase in phrases:
            yield phrase
        for phrase in question_phrases:
            yield phrase
        for phrase in action_phrases:
            yield phrase

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
            "idag", u"måndag 18 mars", "1:a mars", "klockan 11.45", u"följande tre veckor", "om tio minuter",
            u"20:e mars vid 22.00", u"tjugonde mars vid tio på kvällen"
        ]

    @property
    def person_name(self):
        return [
            "Astrid", "Nils", "Lisa", "Mats", "Alexander", "Annika", "Erika", "Claes", "Marcus", "Katarina", "Leif",
            "Sara", "Oskar", "Andreas", "Per", "Roger", "Niklas", "Christer", "Johan", "Danielsson", u"Nordström",
            "Svensson", "Jonasson", "Karlsson", "Holm", "Olofsson", u"Sandström", "Holmberg", "Olsson", "Persson",
            "Bergman", "Lindholm", "Axelsson", "Emelie Pettersson", "Johannes Henriksson", "Martin Magnusson",
            "Patrik Isaksson", "Jakob Eliasson", "Roland Ali", u"Viktor Nyström", "Helen Viklund", "Kurt Gustafsson",
            "Anette Samuelsson", "Annika Lundberg", u"Eva Löfgren", "Linda Hassan", "Robert Norberg"
        ]

    @property
    def yes(self):
        return [
            "ja", "javisst", "japp", "absolut", u"det stämmer", "precis", u"självklart", u"varför inte", "ok", "okej",
            "det blir kanon", "perfekt", "det skulle jag tro"
        ]

    @property
    def no(self):
        return [
            "nej", "nix", u"nähe du", "icke", "nej tack", "helst inte", "det vill jag inte", "det tror jag inte",
            "det skulle jag inte tro", u"gör inte det", u"gör det inte"
        ]

    @property
    def top(self):
        return [u"glöm alltihop", "jag skiter i detta", u"ta mig härifrån", u"börja om", u"börja från noll"]

    @property
    def up(self):
        return [
            u"gå tillbaka", u"vad var den förra", "backa", u"förra", "tillbaka", "ta mig tillbaka", u"backa till förra"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('inte {{ name }}')


class SpanishExamples(Examples):
    @property
    def negative(self):
        phrases = [
            "a bordo", "acerca de", "arriba", u"a través de", u"después de", "en contra", "a lo largo de", "entre",
            "como", "en", "en", "en lo alto", "antes", u"detrás", "abajo", "debajo", "al lado", "entre", u"más allá de",
            "pero", "por", "abajo", "durante", "excepto", "para", "desde", "en", "dentro", "en", "menos", "como",
            "cerca", "de", "encima de", "sobre", "opuesto", "fuera", "fuera de", "corto", "desde", "que", "entonces",
            "a lo largo de", "hasta", "hacia", "debajo de", "a diferencia de", "hasta", "arriba", "con", "dentro de",
            "sin", "vale", "es"
            "se", "el", "la"
            "a", "soy", "son", "ellos", "este", "ese", "yo", "usted ", u"él", "ella", "ellos", "ellas", "su", "sus",
            "mi", "tu", u"tú", "nosotros", "nosotras", "vosotros", "vosotras", "nuestro", "nuestra", "vuestro",
            "vuestra", "vuestros", "vuestras", u"mío", u"mía", u"míos", u"mías", "tuyo", "tuyos", "tuya", "tuyas",
            "suyo", "suya", "suyos", "suyas"
        ]
        question_phrases = [
            u"cómo", u"cómo está", u"cómo es", u"cómo está el", u"cómo es el", u"cómo está la", u"cómo es la",
            u"cómo están los", u"cómo están las"
            u"cuándo", u"cuándo es", u"cuándo está", u"cuándo es el", u"cuándo es la", u"cuándo son los",
            u"cuándo son las", u"cuándo está el", u"cuándo está la", u"cuándo están los", u"cuándo están las", u"qué",
            u"qué es", u"qué es la", u"qué es el", u"qué son los", u"qué son las", u"cuál", u"cuál es", u"cuál es la",
            u"cuál es el", u"cuáles son los", u"cuáles son las", u"por qué", u"por qué es", u"por qué está",
            u"por qué es el", u"por qué es la", u"por qué son", u"por qué son los", u"por qué son las",
            u"por qué está el", u"por qué está la", u"por qué están los", u"por qué están las"
        ]
        action_phrases = [
            "hacer", "decir", "iniciar", "detener", "habilitar", "deshabilitar", "querer", "dar", "haber"
            "subir", "bajar", "disminuir", "aumentar", "actuar", "determinar", "preguntar", "ir", "disparar", "esperar",
            "esperar", "aceptar", "mostrar", u"enseñar", "ayudar"
        ]
        for phrase in phrases:
            yield phrase
        for phrase in question_phrases:
            yield phrase
        for phrase in action_phrases:
            yield phrase

    @property
    def integer(self):
        return [
            "0", "99", "1224", "100000", "100.000", "una", "uno", u"dieciséis", "veintiuno", "veintiuno",
            "veinte y uno", "tres", "dos mil quince", "mil cincuenta y siete"
        ]

    @property
    def string(self):
        return [
            "singular", "doble palabra", "tres en uno", "hey pon cuatro", u"cuanto más mejor cinco",
            u"cálmate y cuenta hasta seis", u"llévalos hasta el siete",
            "nadie cuenta los dedos de los pies como un chico de ocho dedos",
            "importa tener sentido para nueve de nosotros", u"llevarías diez o ninguno a una isla desierta"
        ]

    @property
    def datetime(self):
        return [
            "hoy", "ayer", "este lunes", u"miércoles", "viernes 18 de febrero", "20 de febrero", "el 1 de marzo",
            "11:45 de la noche", "a las tres y quince", "la semana que viene", "en cinco minutos",
            u"próximos tres meses", "este fin de semana", u"el 12 de marzo a las 8 de la mañana"
        ]

    @property
    def person_name(self):
        return [
            "Antonio", u"José", "Manuel", "Francisco", "David", "Juan", "Javier", "Daniel", u"Jesús", "Carlos",
            "Alejandro", "Miguel", "Pedro", "Pablo", u"Ángel", "Sergio", "Alberto", u"María", u"Cármen", "Ana",
            "Isabel", "Laura", "Cristina", "Marta", "Dolores", u"Lucía", "Paula", "Mercedes", "Rosario", "Teresa",
            "Sara", "Reyes", "Caballero", "Nieto", "Pascual", "Ferrer", u"Giménez", "Lorenzo", "Pastor", "Soto",
            "Soler", "Parra", u"García", u"González", u"López", u"Pérez", u"Gómez", u"Díaz", "Alonso", "Moreno",
            "Navarro", u"Rámos", "Torres", "Castillo", "Carlos Aguilar Moreno", u"Pedro Sánchez Álvarez",
            "Sonia Reina Sanz", "Cristina Claret Iglesias", u"Manuel Núñez Santos", "Rafael Rubio Molina",
            u"Isabel Tomás Comas", "Anna Delgado Prieto", "Lorena Fuentes Ortiz", "Silvia Carrasco Rojas"
        ]

    @property
    def yes(self):
        return [
            u"sí", "claro", "desde luego", "por supuesto", "de acuerdo", "vale", "perfecto", "bien", "okei", "sip",
            "sep"
        ]

    @property
    def no(self):
        return ["no", u"de ningún modo", "de ninguna manera", "en absoluto", "na", "nop", "ni de broma", "para nada"]

    @property
    def top(self):
        return [
            "vuelve a empezar", "vuelve al principio", "vuelve al inicio", "principio", "inicio", "desde el principio",
            "reinicia", "empieza de nuevo", u"olvídalo", "olvida todo"
        ]

    @property
    def up(self):
        return [
            u"atrás", u"vuelve atrás", "vuelve", "regresa", u"vuelve una atrás", u"quiero ir atrás",
            u"quiero volver atrás"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('no {{ name }}')
