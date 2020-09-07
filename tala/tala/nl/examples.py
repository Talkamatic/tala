# coding: utf-8

from jinja2 import Template

from tala.nl.languages import ENGLISH, SWEDISH, SPANISH, PERSIAN


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
        examples = {ENGLISH: EnglishExamples(), SWEDISH: SwedishExamples(), SPANISH: SpanishExamples(), PERSIAN: PersianExamples()}
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
            "om", "ovanför", "tvärsöver", "efter", "mot", "bland", "runt", "som", "på", "vid", "ovanpå", "före",
            "bakom", "nedan", "under", "bredvid", "mellan", "bortom", "men", "av", "trots", "ner", "förutom", "för",
            "från", "i", "inuti", "in i", "nära", "nästa", "mittemot", "ut", "utanför", "över", "per", "plus",
            "runt", "sedan", "än", "genom", "tills", "till", "mot", "olik", "upp", "via", "med", "inom", "utan", "är",
            "vara", "den", "det", "en", "ett", "dem", "denna", "detta", "jag", "du", "ni", "han", "hon", "hen", "de",
            "hans", "hennes", "hens", "min", "mina", "deras", "er", "din", "vi", "oss", "vår"
        ]
        question_phrases = ["hur", "hur är", "när", "när är", "vad", "vad är", "varför", "varför är"]
        action_phrases = [
            "gör", "göra", "skapa", "berätta", "tala om", "börja", "starta", "sluta", "stopp", "stanna", "sätt på",
            "stäng av", "höj", "sänk", "öka", "minska", "agera", "bestäm", "säg", "fråga", "gå", "kör",
            "vänta", "ok", "visa", "hjälp"
        ]
        for phrase in phrases:
            yield phrase
        for phrase in question_phrases:
            yield phrase
        for phrase in action_phrases:
            yield phrase

    @property
    def integer(self):
        return ["0", "99", "1224", "etthundratjugosju", "tre", "tvåtusenfemton"]

    @property
    def string(self):
        return [
            "enkel", "dubbelt ord", "det blir tre", "fyra på en gång", "ju fler desto bättre fem",
            "håll andan och räkna till sex", "led dem fram till de glada sju",
            "ingen räknar tår som den med åtta tår", "det spelar roll att det låter rimligt för nio",
            "tar du med tio eller inga till en öde ö"
        ]

    @property
    def datetime(self):
        return [
            "idag", "måndag 18 mars", "1:a mars", "klockan 11.45", "följande tre veckor", "om tio minuter",
            "20:e mars vid 22.00", "tjugonde mars vid tio på kvällen"
        ]

    @property
    def person_name(self):
        return [
            "Astrid", "Nils", "Lisa", "Mats", "Alexander", "Annika", "Erika", "Claes", "Marcus", "Katarina", "Leif",
            "Sara", "Oskar", "Andreas", "Per", "Roger", "Niklas", "Christer", "Johan", "Danielsson", "Nordström",
            "Svensson", "Jonasson", "Karlsson", "Holm", "Olofsson", "Sandström", "Holmberg", "Olsson", "Persson",
            "Bergman", "Lindholm", "Axelsson", "Emelie Pettersson", "Johannes Henriksson", "Martin Magnusson",
            "Patrik Isaksson", "Jakob Eliasson", "Roland Ali", "Viktor Nyström", "Helen Viklund", "Kurt Gustafsson",
            "Anette Samuelsson", "Annika Lundberg", "Eva Löfgren", "Linda Hassan", "Robert Norberg"
        ]

    @property
    def yes(self):
        return [
            "ja", "javisst", "japp", "absolut", "det stämmer", "precis", "självklart", "varför inte", "ok", "okej",
            "det blir kanon", "perfekt", "det skulle jag tro"
        ]

    @property
    def no(self):
        return [
            "nej", "nix", "nähe du", "icke", "nej tack", "helst inte", "det vill jag inte", "det tror jag inte",
            "det skulle jag inte tro", "gör inte det", "gör det inte"
        ]

    @property
    def top(self):
        return ["glöm alltihop", "jag skiter i detta", "ta mig härifrån", "börja om", "börja från noll"]

    @property
    def up(self):
        return [
            "gå tillbaka", "vad var den förra", "backa", "förra", "tillbaka", "ta mig tillbaka", "backa till förra"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('inte {{ name }}')


class SpanishExamples(Examples):
    @property
    def negative(self):
        phrases = [
            "a bordo", "acerca de", "arriba", "a través de", "después de", "en contra", "a lo largo de", "entre",
            "como", "en", "en", "en lo alto", "antes", "detrás", "abajo", "debajo", "al lado", "entre", "más allá de",
            "pero", "por", "abajo", "durante", "excepto", "para", "desde", "en", "dentro", "en", "menos", "como",
            "cerca", "de", "encima de", "sobre", "opuesto", "fuera", "fuera de", "corto", "desde", "que", "entonces",
            "a lo largo de", "hasta", "hacia", "debajo de", "a diferencia de", "hasta", "arriba", "con", "dentro de",
            "sin", "vale", "es"
            "se", "el", "la"
            "a", "soy", "son", "ellos", "este", "ese", "yo", "usted ", "él", "ella", "ellos", "ellas", "su", "sus",
            "mi", "tu", "tú", "nosotros", "nosotras", "vosotros", "vosotras", "nuestro", "nuestra", "vuestro",
            "vuestra", "vuestros", "vuestras", "mío", "mía", "míos", "mías", "tuyo", "tuyos", "tuya", "tuyas",
            "suyo", "suya", "suyos", "suyas"
        ]
        question_phrases = [
            "cómo", "cómo está", "cómo es", "cómo está el", "cómo es el", "cómo está la", "cómo es la",
            "cómo están los", "cómo están las"
            "cuándo", "cuándo es", "cuándo está", "cuándo es el", "cuándo es la", "cuándo son los",
            "cuándo son las", "cuándo está el", "cuándo está la", "cuándo están los", "cuándo están las", "qué",
            "qué es", "qué es la", "qué es el", "qué son los", "qué son las", "cuál", "cuál es", "cuál es la",
            "cuál es el", "cuáles son los", "cuáles son las", "por qué", "por qué es", "por qué está",
            "por qué es el", "por qué es la", "por qué son", "por qué son los", "por qué son las",
            "por qué está el", "por qué está la", "por qué están los", "por qué están las"
        ]
        action_phrases = [
            "hacer", "decir", "iniciar", "detener", "habilitar", "deshabilitar", "querer", "dar", "haber"
            "subir", "bajar", "disminuir", "aumentar", "actuar", "determinar", "preguntar", "ir", "disparar", "esperar",
            "esperar", "aceptar", "mostrar", "enseñar", "ayudar"
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
            "0", "99", "1224", "100000", "100.000", "una", "uno", "dieciséis", "veintiuno", "veintiuno",
            "veinte y uno", "tres", "dos mil quince", "mil cincuenta y siete"
        ]

    @property
    def string(self):
        return [
            "singular", "doble palabra", "tres en uno", "hey pon cuatro", "cuanto más mejor cinco",
            "cálmate y cuenta hasta seis", "llévalos hasta el siete",
            "nadie cuenta los dedos de los pies como un chico de ocho dedos",
            "importa tener sentido para nueve de nosotros", "llevarías diez o ninguno a una isla desierta"
        ]

    @property
    def datetime(self):
        return [
            "hoy", "ayer", "este lunes", "miércoles", "viernes 18 de febrero", "20 de febrero", "el 1 de marzo",
            "11:45 de la noche", "a las tres y quince", "la semana que viene", "en cinco minutos",
            "próximos tres meses", "este fin de semana", "el 12 de marzo a las 8 de la mañana"
        ]

    @property
    def person_name(self):
        return [
            "Antonio", "José", "Manuel", "Francisco", "David", "Juan", "Javier", "Daniel", "Jesús", "Carlos",
            "Alejandro", "Miguel", "Pedro", "Pablo", "Ángel", "Sergio", "Alberto", "María", "Cármen", "Ana",
            "Isabel", "Laura", "Cristina", "Marta", "Dolores", "Lucía", "Paula", "Mercedes", "Rosario", "Teresa",
            "Sara", "Reyes", "Caballero", "Nieto", "Pascual", "Ferrer", "Giménez", "Lorenzo", "Pastor", "Soto",
            "Soler", "Parra", "García", "González", "López", "Pérez", "Gómez", "Díaz", "Alonso", "Moreno",
            "Navarro", "Rámos", "Torres", "Castillo", "Carlos Aguilar Moreno", "Pedro Sánchez Álvarez",
            "Sonia Reina Sanz", "Cristina Claret Iglesias", "Manuel Núñez Santos", "Rafael Rubio Molina",
            "Isabel Tomás Comas", "Anna Delgado Prieto", "Lorena Fuentes Ortiz", "Silvia Carrasco Rojas"
        ]

    @property
    def yes(self):
        return [
            "sí", "claro", "desde luego", "por supuesto", "de acuerdo", "vale", "perfecto", "bien", "okei", "sip",
            "sep"
        ]

    @property
    def no(self):
        return ["no", "de ningún modo", "de ninguna manera", "en absoluto", "na", "nop", "ni de broma", "para nada"]

    @property
    def top(self):
        return [
            "vuelve a empezar", "vuelve al principio", "vuelve al inicio", "principio", "inicio", "desde el principio",
            "reinicia", "empieza de nuevo", "olvídalo", "olvida todo"
        ]

    @property
    def up(self):
        return [
            "atrás", "vuelve atrás", "vuelve", "regresa", "vuelve una atrás", "quiero ir atrás",
            "quiero volver atrás"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('no {{ name }}')


class PersianExamples(Examples):
    @property
    def negative(self):
        phrases = [
            "داخل", "درباره", "بالا", "در سراسر", "بعد", "علیه", "همراه", "در بین", "به عنوان", "در", "روی", "بالای",
            "قبل", "پشت", "زیر", "زیر", "کنار", "بین", "فراتر", "اما", "توسط", "بیا", "پایین", "هنگام", "به جز",
            "برای", "از", "در", "داخل", "به", "کمتر", "مانند", "نزدیک", "از", "خاموش", "روشن", "روی", "مخالف",
            "خارج", "بیش", "گذشته", "ذخیره", "کوتاه", "از", "بعد", "از طریق", "سراسر", "به", "به سمت", "زیر",
            "بر خلاف", "تا", "بالا", "بر", "با", "بدون", "ارزش", "است", "آن", "این", "یک", "من", "هستند", "آنها",
            "این", "آن", "من", "شما", "او", "آنها", "ایشان", "او", "اون", "مال", "آنها", "شما", "ما"
        ]
        question_phrases = [
            "چگونه", "چطور", "چه وقت", "چه وقتی", "برای چه", "وقتی", "چه زمانی", "چه موقع", "کی" "چه زمانی", "چه",
            "برای چی", "چطور میشه که", "چی میشه که", "برای چه", "چرا"
        ]
        action_phrases = [
            "انجام بده", "بساز", "بگو", "شروع کن", "متوقف کن", "فعال کن", "غیرفعال کن", "افزایش بده", "پایین بیار",
            "کاهش بده", "افزایش بده", "عمل کن", "تعیین کن", "بگو", "سؤال کن", "برو", "شلیک کن", "صبر کن", "متوقف شو",
            "نشون بده", "نمایش بده", "کمک کن"
        ]
        for phrase in phrases:
            yield phrase
        for phrase in question_phrases:
            yield phrase
        for phrase in action_phrases:
            yield phrase

    @property
    def integer(self):
        return ["0", "99", "1224", "صد و پنجاه و هفت", "سه", "دو هزار و پانزده"]

    @property
    def string(self):
        return [
            "تک", "کلمه دوتایی", "سه در یک", "چهار تاش  از اونها بده", "پنج انگشت با هم برابرند",
            "آرام باش و تا شش بشمر", "توی هفت آسمون یک ستاره هم نداره",
            "هیچکس انگشتها رو مثل آن هشت انگشتی نمیشناسد",
            "مهم هست که برای ما نه نفر معنی داره",
            "لطفا ده تا یا هیچ کدام را به جزیره بیاورید"
        ]

    @property
    def datetime(self):
        return [
            "امروز", "دوشنبه ۱۸ مارش", "اول مارش", "11:45 صبح", "سه هفته بعد", "ده دقیقه بعد",
            "20 مارش ساعت 22:00", "بیستم مارش ساعت 10 صبح"
        ]

    @property
    def person_name(self):
        return [
            "علی", "فاطمه", "آرمان", "شیوا", "فرناز", "آریا", "رویا",
            "فرناز عطایی", "سعید صادقپور", "حامد زاهدی", "آرمان بحری"
        ]

    @property
    def yes(self):
        return [
            "بله", "آره", "مطمئن", "مطمئنم", "اوکی", "البته", "خیلی خوب", "خوبه", "درست", "درسته", "عالی",
            "عالیه", "من اینطور فکر میکنم"
        ]

    @property
    def no(self):
        return [
            "نه", "نه متشکرم", "نه ممنون", "نه خیلی ممنون", "منفی", "اینو نمیخوام", "نیمخوام", "نکن", "لطفا نکن"
        ]

    @property
    def top(self):
        return [
            "فراموش کن", "ولش کن", "منو از اینجا بیرون ببر", "دوباره شورع کن", "ابتدا", "اینو ولش کن", "شروع دوباره"
        ]

    @property
    def up(self):
        return [
            "برو عقب", "عقب", "قبلی", "برو به عقب", "برو به قبلی", "قبلیه"
        ]

    @property
    def answer_negation_templates(self):
        yield Template('not {{ name }}')
