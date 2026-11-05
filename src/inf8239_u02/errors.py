"""Categorizacion transparente de errores de clasificacion de sentimiento.

Las reglas son lexicales y explicitas: cada categoria se dispara por senales
observables en el texto (negaciones, contrastes, ironia, etc.). No se usa
aprendizaje automatico para etiquetar los errores, de modo que cualquier
persona pueda revisar y corregir las reglas. La categoria asignada es una
HIPOTESIS sobre la causa del error, no una verdad: por eso cada fila guarda
tambien las senales que la activaron.
"""

from __future__ import annotations

import re

import pandas as pd

NEGATION_WORDS = {
    "not", "no", "never", "nobody", "nothing", "neither", "none", "nowhere",
    "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't",
    "can't", "cannot", "won't", "wouldn't", "shouldn't", "couldn't", "hasn't",
    "haven't", "hadn't", "ain't", "w/out", "without", "hardly", "scarcely",
    "rarely", "barely",
}

POSITIVE_LEXICON = {
    "accessible", "affordable", "amazing", "authentic", "attractive", "awesome",
    "bargain", "best", "better", "big", "blissful", "bold", "brilliant",
    "bright", "bustling", "charming", "cheap", "cheerful", "clean", "clear",
    "comfortable", "consistent", "convenient", "cool", "courteous", "cozy",
    "creative", "crispy", "crunchy", "cute", "delicious", "delightful",
    "dependable", "divine", "easy", "efficient", "enjoy", "enjoyable",
    "enjoyed", "enjoys", "equally", "excellent", "exciting", "fabricated",
    "fantastic", "favorite", "favourite", "favors", "fine", "flavorful",
    "flavourful", "flavorsome", "fond", "fresh", "friendly", "fun", "generous",
    "gem", "glad", "good", "gorgeous", "great", "handcrafted", "happy",
    "helpful", "hottest", "hotter", "impeccable", "impressed", "impressive",
    "inexpensive", "intuitive", "incredible", "joy", "knowledgeable",
    "lifetime", "like", "liked", "likes", "lip", "lovely", "love", "loved",
    "loves", "luxurious", "masterful", "memorable", "mesmerising", "mesmerizing",
    "moist", "mouthwatering", "nice", "outstanding", "perfect", "pleasant",
    "pleased", "pleasing", "plus", "premium", "prompt", "quality", "quick",
    "reasonable", "refreshing", "regular", "reliable", "rich", "satisfying",
    "savoury", "scrumptious", "sexy", "solid", "sound", "sparkling", "speedy",
    "splendid", "stellar", "superb", "tasty", "tender", "terrific", "thorough",
    "thoughtful", "timely", "treat", "treated", "trustworthy", "valuable",
    "worth", "wow", "yummy", "satisfied", "secure", "simple", "smooth",
    "spacious", "speaks", "special", "steady", "sturdy", "surprising",
    "warm", "works", "working", "worked", "wonderful", "wrapped",
    "satisfies", "solves", "fixed", "fixes", "hook", "hooked", "flawless",
    "top", "tremendous", "unique", "versatile", "vibrant",
    "victory", "warmly", "worthwhile",
}

NEGATIVE_LEXICON = {
    "afraid", "annoyance", "annoying", "appalling", "artless", "avoid",
    "awful", "bad", "bitter", "bland", "boring", "bother", "broke", "broken",
    "buggy", "burned", "burnt", "clunky", "complaint", "confusing", "costly",
    "cramped", "crap", "crappy", "crushed", "damaged", "defective", "delay",
    "delayed", "denied", "depressing", "desired", "desire", "disappointed",
    "disappointing", "disappointment", "disgusting", "dissatisfied", "dreadful",
    "dull", "error", "failure", "fail", "failed", "fails", "flimsy", "flaws",
    "forced", "garbage", "glitch", "glitchy", "gross", "hard", "hate", "hated",
    "horrible", "hostile", "hurt", "inadequate", "inattentive", "incompetent",
    "junk", "lame", "lousy", "mediocre", "moldy", "messy", "mistake", "morons",
    "mushy", "nasty", "noise", "noisy", "overcooked", "overrated",
    "overpriced", "painful", "pathetic", "poor", "pricey", "problem",
    "refuse", "regret", "rejected", "rotten", "rough", "rubbery", "rude",
    "sad", "salty", "sggy", "soggy", "sour", "spoiled", "stale", "stingy",
    "subpar", "sucks", "tasteless", "terrible", "theft", "tough", "trash",
    "ugliest", "ugly", "unable", "unacceptable", "unavailable", "uncomfortable",
    "undisappointing", "underwhelming", "unfair", "unfriendly", "unhelpful",
    "uninspiring", "unpleasant", "unprofessional", "unusable", "upset",
    "useless", "waste", "watery", "weak", "weird", "wet", "worse", "worst",
    "boobs", "slurs", "faint", "hook", "squeaky", "squealing", "lukewarm",
    "skimpy", "flavorless", "flavourless", "chewy",
    "conspicuous", "foul", "spilled", "spill", "greasy", "rancid", "undercooked", "hassle", "wait", "waited", "waiting", "forever", "misses",
    "missing", "lost", "refund", "wrong", "incorrect", "inaccurate", "glitches",
    "unsupported", "incompatible", "scratch", "scratches",
    "drops", "dropped", "crash", "crashes", "crashed", "disconnect",
    "disconnects", "stain", "stains", "dirty", "filthy", "sticky", "unclean",
    "smelly", "odor", "odour", "expensive",
    "unimpressed", "unimpressive", "ridiculous", "steep", "horrendous", "neglect", "poorly", "lazy", "hassles",
    "not", "never",
}

EMPHASIS_WORDS = {
    "way", "so", "too", "very", "not", "no", "nothing", "never", "really",
    "just", "must", "should", "well", "look", "yes", "still", "even", "only",
    "most", "much", "more", "less", "quite", "highly", "totally", "absolutely",
}

DOMAIN_KEYWORDS = {
    "accessory", "accessories", "app", "appearance", "bag", "bar", "batteries",
    "battery", "bathroom", "bed", "beer", "beverage", "book", "breakfast", "brunch",
    "burger", "bus", "buyer", "cake", "camera", "car", "care", "cashier", "cast",
    "cable", "cell", "charger", "charge", "chicken", "chocolate", "cocktail",
    "coffee", "computer", "condition", "cook", "coupon", "customer", "deal",
    "delivery", "dessert", "device", "dinner", "dining", "director", "dishes",
    "dish", "drink", "driver", "ear", "earbuds", "eat", "employees", "employee",
    "episode", "experience", "featured", "film", "films", "flavor", "flavors",
    "food", "foot", "fork", "furniture", "game", "gaming", "graphics", "headphone",
    "headset", "headphones", "hotel", "interface", "internet", "item", "keyboard",
    "laptop", "layout", "level", "lunch", "manager", "margarita", "meal", "meals",
    "menu", "microphone", "monitor", "movie", "movies", "music", "noodles",
    "package", "packaging", "pasta", "payment", "performance", "performances",
    "phone", "phones", "pizza", "place", "plan", "plans", "plot", "portion",
    "portions", "price", "prices", "product", "purchased", "quality", "restaurant",
    "rib", "rice", "room", "sauce", "screen", "seat", "seats", "servers",
    "service", "shoes", "shop", "shopping", "side", "sides", "software", "soup",
    "specs", "spice", "spicy", "staff", "steak", "story", "subscription",
    "tablet", "tacos", "tea", "temperature", "texture", "theater", "ticket",
    "tv", "value", "waiter", "waitress", "watch", "website", "wifi", "wine",
    "warranty", "brand", "model", "color", "colour", "size", "material",
    "design", "style", "look", "instructions", "manual", "features", "sandwich",
    "sushi", "salmon", "seafood", "juice", "soda", "water", "milk", "seasoning", "parking", "access", "customer service", "shows", "season",
    "script", "actors", "series", "mouse", "shipping",
    "ordering", "ordered", "call", "calls", "grip", "commercials",
    "description", "signal", "soon", "again", "everything",
}

ASPECT_KEYWORDS = {
    "acting", "atmosphere", "battery", "breakfast", "burger", "camera",
    "characters", "coffee", "customer service", "decor", "delivery", "dessert",
    "dinner", "effects", "ending", "food", "hotel", "menu", "movie", "packaging",
    "plot", "price", "product", "quality", "room", "screen", "seats", "selection",
    "service", "shipping", "soundtrack", "staff", "story", "wait", "waiter",
    "waitress",
}

INFORMAL_MARKERS = {
    "lol", "lmao", "btw", "omg", "smh", "irl", "tbh", "ive", "idk", "ur", "thx",
    "wanna", "gonna", "gotta", "kinda", "sorta", "yep", "nope", "nah", "cuz",
    "cause", "w/out", "aint", "alot", "stuff", "dude", "guys", "meh", "yuck",
    "fyi", "afaik", "rofl", "coz", "nite", "yall", "dat", "deez", "sum",
}

TYPO_TOKENS = {
    "teh", "thier", "recieve", "recieved", "seperate", "definately", "occured",
    "untill", "wich", "becuase", "becasue", "reccommend", "recomend",
    "restarant", "restaraunt", "shure", "truely", "wont", "wouldnt", "couldnt",
    "shouldnt", "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent",
    "hasnt", "havent", "dissapointed", "dissapointing", "dissappointed",
    "accessable", "acessable", "reciept", "wierd", "freind", "goverment",
    "grammer", "occassion", "priviledge", "refered", "relevent", "similer",
    "publically", "gramatically", "immediatly", "knowlege", "noticable",
    "occassionally", "refering", "responsability", "succesfully", "unfortunatly",
    "proffesional", "accomodation", "adversting", "begining", "calender",
    "catagory", "collegue", "comming", "concious", "curiousity", "dilema",
    "embarass", "enviroment", "existance", "familar", "foriegn", "garantee",
    "independant", "neccessary", "personell", "posession", "prefered",
    "sucessful", "tommorow", "vaccum", "writen", "happend",
    "dissapoint", "suppper", "tast", "fliped", "fufilled", "grateful",
}

IDIOM_PATTERNS = (
    r"\bkill(?:s|ed)? me\b", r"\bmade my day\b", r"\bbroke the bank\b",
    r"\bworth every penny\b", r"\bno big deal\b", r"\bpiece of cake\b",
    r"\bon the fence\b", r"\bunder the weather\b", r"\bon the house\b",
    r"\bhit the spot\b", r"\bcould ?n'?t care less\b", r"\bwhat a shame\b",
    r"\bhidden gem\b", r"\bnot my cup of tea\b", r"\bfood for thought\b",
    r"\bthumbs up\b", r"\bhands down\b", r"\bgo-to\b", r"\bmust try\b",
    r"\bwill be back\b", r"\bnever again\b", r"\bworth a try\b",
    r"\ba whole different story\b", r"\bto die for\b",
)

CATEGORY_DESCRIPTIONS = {
    "negacion": "Negacion explicita que invierte o matiza el sentimiento",
    "ironia": "Ironia o sarcasmo marcado por marcadores discursivos",
    "enfasis_mayusculas": "Enfasis por mayusculas, tipico de-intensity o de rechazo",
    "contraste": "Contraste explicito entre una valoracion positiva y otra negativa",
    "atribucion_tercero": "Opinion atribuida a un tercero o cita ajena",
    "condicion_o_recomendacion": "Condicion, hipotesis o recomendacion pendiente",
    "comparacion": "Comparacion explicita entre productos, peliculas o relaciones",
    "hiperbole": "Exageracion o intensificacion del juicio",
    "duda_hedging": "Incertidumbre o matiz del autor sobre su juicio",
    "lang_indice_tecnico": "Valoracion numerica o indice que no expresa sentimiento",
    "dialecto_registro_informal": "Registro coloquial, dialectal o grafia no estandar",
    "modismo_expresion": "Expresion idiomatica o formula cultural",
    "formato_precios": "Menciones de precio, envio o compra",
    "multiples_aspectos": "Menciona varios aspectos evaluables del producto o del servicio",
    "experiencia_personal": "Relato en primera persona con vivencia concreta",
    "texto_corto": "Texto demasiado corto para una inferencia fiable",
    "etiqueta_discutible": "Presencia simultanea de indicadores de ambos signos",
    "fuera_de_dominio": "Texto ajeno al dominio de resenas del corpus",
    "hecho_sin_valoracion": "Hecho objetivo sin valoracion emocional detectable",
    "senal_no_cubierta": "Hay senal de sentimiento pero ninguna regla la modela",
}

CATEGORY_NAMES = (
    "negacion",
    "ironia",
    "enfasis_mayusculas",
    "contraste",
    "atribucion_tercero",
    "condicion_o_recomendacion",
    "comparacion",
    "hiperbole",
    "duda_hedging",
    "lang_indice_tecnico",
    "dialecto_registro_informal",
    "modismo_expresion",
    "formato_precios",
    "multiples_aspectos",
    "experiencia_personal",
    "texto_corto",
    "etiqueta_discutible",
    "fuera_de_dominio",
    "hecho_sin_valoracion",
    "senal_no_cubierta",
)

PRIORITY = CATEGORY_NAMES

PATTERNS = {
    "ironia": r"\b(?:yeah,?\s*right|sure thing|as if|great,?\s*another|oh,?\s*(?:another|"
              r"fantastic|great|perfect|lovely)|what a joke|biggest joke|total joke|"
              r"no kidding|oh,? joy|shocking)\b",
    "contraste": r"\b(?:but|however|although|though|yet|despite|nevertheless|nonetheless|"
                r"whereas|even so|on the other hand)\b",
    "atribucion_tercero": r"(?:\"|\u201c|\u00ab)[^\"\u201d\u00bb]{12,}(?:\"|\u201d|\u00bb)|"
                           r"\b(?:my|his|her|their)\s+(?:friend|wife|husband|boss|brother|"
                           r"sister|partner|girlfriend|boyfriend|roommate|mother|father|mom|"
                           r"dad|customer|employee|neighbor|neighbour)\b|"
                           r"\b(?:he|she|they)\s+(?:said|says|told|mentioned|thinks|thought|"
                           r"wrote)\b|\baccording to\b|\bsome(?:one|body)\s+(?:said|told)\b",
    "condicion_o_recomendacion": r"\b(?:would recommend|would buy|would order|would watch|"
                                 r"would try|would return|would stay|would give|would "
                                 r"definitely|will buy|will order|will watch|will return|"
                                 r"will stay|highly recommend|definitely recommend|"
                                 r"can ?n'?t wait|cannot wait|looking forward to going back|"
                                 r"would have|would've|should have|should've|could have|"
                                 r"could've|were to|had been|otherwise|unless)\b|"
                                 r"\bif\b[^.?!]{0,40}\b(?:you|we|they|it|there)\b",
    "comparacion": r"\b(?:better|worse|superior|inferior|instead of|compared (?:to|with)|"
                    r"as \w+ as|more \w+ than|less \w+ than|different from|similar to)\b",
    "hiperbole": r"\b(?:absolutely|completely|totally|entirely|utterly|extremely|"
                 r"insanely|ridiculously|the best|the worst|best ever|worst ever|"
                 r"highly|by far|without a doubt|life[- ]changing|out of this world)\b",
    "duda_hedging": r"\b(?:maybe|perhaps|not sure|unsure|i think|i guess|i suppose|"
                    r"probably|possibly|might be|kind of|sort of|seems like|feels like|"
                    r"who knows|hard to say|arguably|more or less)\b",
    "lang_indice_tecnico": r"\b\d+\s*/\s*\d+\b|\b\d+(?:\.\d+)?\s*(?:stars?|star|out of)\b|"
                             r"\b(?:one|two|three|four|five)\s+stars?\b|\b\d{1,3}\s?%",
    "formato_precios": r"\b(?:price|pricing|prices|cheap|cheaper|expensive|cost|costs|"
                        r"shipping|delivery|coupon|discount|refund|money|dollars?|order|"
                        r"ordered|purchase|purchased|bought|worth the money|paid)\b",
}

FIRST_PERSON_PATTERN = r"\b(?:i|we|my|our|me|us)\b"
PAST_ACTION_PATTERN = (
    r"\b(?:bought|ordered|watched|ate|tried|paid|returned|shipped|received|used|"
    r"visited|tasted|installed|tested|drove|flew|booked|read|grabbed|went|came|"
    r"got|took|made|saw|heard|found|spent|dined|eaten|worked|played|checked)\b"
)

INFORMAL_PATTERN = (
    r"\b(?:lol|lmao|btw|omg|smh|irl|tbh|ive|idk|ur|thx|wanna|gonna|gotta|"
    r"kinda|sorta|yep|nope|nah|cuz|cause|w/out|aint|alot|stuff|dude|guys|meh|"
    r"yuck|fyi|afaik|rofl|yall|dat|deez|sum)\b"
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z']+", str(text).lower())


def _hits(text: str, pattern: str) -> list[str]:
    return [
        match.group(0).strip().lower()
        for match in re.finditer(pattern, str(text), re.IGNORECASE)
    ]


def _lexicon_hits(text: str, lexicon: set[str]) -> list[str]:
    words = set(_tokens(text))
    return sorted(words & lexicon)


def _informal_hits(text: str) -> list[str]:
    hits = _hits(text, INFORMAL_PATTERN)
    for token in _tokens(text):
        if token in TYPO_TOKENS or len(token) > 3 and re.search(r"(.)\1\1", token) or re.search(r"[a-z]\d|\d[a-z]", token):
            hits.append(token)
    return sorted(set(hits))


def _emphasis_hits(text: str) -> list[str]:
    """Palabras en mayusculas que actuan como enfasis del autor."""
    findings = []
    words = str(text).split()
    for position, word in enumerate(words):
        clean = re.sub(r"[^A-Za-z]", "", word)
        if len(clean) < 3 or position == 0:
            continue
        if clean.isupper():
            lowered = clean.lower()
            if lowered in (POSITIVE_LEXICON | NEGATIVE_LEXICON | EMPHASIS_WORDS):
                findings.append(clean)
    return sorted(set(findings))


def _negation_evidence(text: str) -> list[str]:
    """Negaciones acompanadas de una palabra de sentimiento en la ventana siguiente."""
    tokens = _tokens(text)
    evidence = []
    for position, token in enumerate(tokens):
        if token not in NEGATION_WORDS:
            continue
        window = tokens[position + 1: position + 7]
        for word in window:
            if word in (POSITIVE_LEXICON | NEGATIVE_LEXICON):
                evidence.append(f"{token} ... {word}")
                break
    return evidence


def _is_out_of_domain(text: str) -> bool:
    """Texto que no pertenece al dominio de resenas del corpus.

    Se considera fuera de dominio cuando no hay ninguna palabra de sentimiento,
    ninguna palabra del ambito de resenas (producto, pelicula, restaurante) y
    tampoco una experiencia en primera persona.
    """
    tokens = set(_tokens(text))
    if tokens & (POSITIVE_LEXICON | NEGATIVE_LEXICON):
        return False
    if tokens & DOMAIN_KEYWORDS:
        return False
    if _hits(text, FIRST_PERSON_PATTERN):
        return False
    return len(tokens) >= 6


def _signals(category: str, text: str) -> list[str]:
    value = str(text)
    tokens = _tokens(value)
    if category == "negacion":
        return _negation_evidence(value)
    if category == "enfasis_mayusculas":
        return _emphasis_hits(value)
    if category == "dialecto_registro_informal":
        return _informal_hits(value)
    if category == "modismo_expresion":
        found = []
        for pattern in IDIOM_PATTERNS:
            found.extend(_hits(value, pattern))
        return sorted(set(found))
    if category == "multiples_aspectos":
        return sorted({word for word in ASPECT_KEYWORDS if word in value.lower()})
    if category == "experiencia_personal":
        return _hits(value, FIRST_PERSON_PATTERN) + _hits(value, PAST_ACTION_PATTERN)
    if category == "texto_corto":
        return [f"{len(tokens)} palabras"]
    if category == "etiqueta_discutible":
        positive = _lexicon_hits(value, POSITIVE_LEXICON)
        negative = _lexicon_hits(value, NEGATIVE_LEXICON)
        return [f"positivo:{word}" for word in positive] + [f"negativo:{word}" for word in negative]
    if category == "hecho_sin_valoracion":
        return [f"{len(tokens)} palabras", "sin lexico de sentimiento"]
    if category == "senal_no_cubierta":
        return _lexicon_hits(value, POSITIVE_LEXICON) + _lexicon_hits(value, NEGATIVE_LEXICON)
    if category == "fuera_de_dominio":
        return [f"{len(tokens)} palabras", "sin dominio"]
    if category in PATTERNS:
        return _hits(value, PATTERNS[category])
    return []


def categorize_error(text: str) -> tuple[str, list[str]]:
    """Devuelve la categoria hipotetizada y las senales que la activaron."""
    value = str(text)
    tokens = _tokens(value)
    for name in PRIORITY:
        if name == "negacion":
            evidence = _negation_evidence(value)
            if evidence:
                return name, evidence
            continue
        if name == "enfasis_mayusculas":
            emphasis = _emphasis_hits(value)
            if emphasis:
                return name, emphasis
            continue
        if name == "dialecto_registro_informal":
            informal = _informal_hits(value)
            if informal:
                return name, informal
            continue
        if name == "modismo_expresion":
            found = []
            for pattern in IDIOM_PATTERNS:
                found.extend(_hits(value, pattern))
            if found:
                return name, sorted(set(found))
            continue
        if name == "multiples_aspectos":
            found = {word for word in ASPECT_KEYWORDS if word in value.lower()}
            if len(found) >= 2:
                return name, sorted(found)
            continue
        if name == "experiencia_personal":
            if _hits(value, FIRST_PERSON_PATTERN) and _hits(value, PAST_ACTION_PATTERN):
                return name, _signals(name, value)
            continue
        if name == "texto_corto":
            if len(tokens) <= 3:
                return name, _signals(name, value)
            continue
        if name == "etiqueta_discutible":
            positive = _lexicon_hits(value, POSITIVE_LEXICON)
            negative = _lexicon_hits(value, NEGATIVE_LEXICON)
            if positive and negative:
                return name, _signals(name, value)
            continue
        if name == "fuera_de_dominio":
            if _is_out_of_domain(value):
                return name, _signals(name, value)
            continue
        if name == "hecho_sin_valoracion":
            if not (set(tokens) & (POSITIVE_LEXICON | NEGATIVE_LEXICON)):
                return name, _signals(name, value)
            continue
        if name == "senal_no_cubierta":
            return name, _signals(name, value)
        if _hits(value, PATTERNS[name]):
            return name, _signals(name, value)
    return "senal_no_cubierta", []


def annotate_errors(errors: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    """Agrega las columnas `category`, `category_description` y `signals`."""
    annotated = errors.copy().reset_index(drop=True)
    categories: list[str] = []
    descriptions: list[str] = []
    signals: list[str] = []
    fuera_de_dominio: list[bool] = []
    for value in annotated[text_column]:
        category, evidence = categorize_error(value)
        categories.append(category)
        descriptions.append(CATEGORY_DESCRIPTIONS[category])
        signals.append("; ".join(evidence))
        fuera_de_dominio.append(_is_out_of_domain(value))
    annotated["category"] = categories
    annotated["category_description"] = descriptions
    annotated["signals"] = signals
    annotated["fuera_de_dominio"] = fuera_de_dominio
    return annotated


def summarize_by_category(errors: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    """Reparto de errores por categoria, con el porcentaje sobre el total."""
    annotated = errors if "category" in errors.columns else annotate_errors(errors, text_column)
    grouped = (
        annotated.groupby(["category", "category_description"])
        .agg(errores=("category", "size"))
        .reset_index()
        .sort_values("errores", ascending=False)
        .reset_index(drop=True)
    )
    total = int(grouped["errores"].sum())
    grouped["porcentaje"] = (100 * grouped["errores"] / total).round(2) if total else 0.0
    grouped["errores"] = grouped["errores"].astype(int)
    return grouped


def sample_errors(
    errors: pd.DataFrame, text_column: str = "text", size: int = 20, random_state: int = 42
) -> pd.DataFrame:
    """Muestra aleatoria reproducible de errores para revision manual."""
    annotated = errors if "category" in errors.columns else annotate_errors(errors, text_column)
    if annotated.empty:
        return annotated
    return annotated.sample(n=min(size, len(annotated)), random_state=random_state).reset_index(drop=True)
