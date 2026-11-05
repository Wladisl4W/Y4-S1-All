"""Independent checks of rule conditions. This does not execute SWRL."""
from pathlib import Path
from rdflib import Graph, Namespace, RDF
from rdflib.collection import Collection
from decimal import Decimal

here = Path(__file__).resolve().parent
app = Namespace("https://example.org/intonation-study#")
swrl = Namespace("http://www.w3.org/2003/11/swrl#")
g = Graph().parse(here / "ontology.ttl", format="turtle")
rules = list(g.subjects(RDF.type, swrl.Imp))
assert len(rules) == 7
for rule in rules:
    assert list(Collection(g, g.value(rule, swrl.body)))
    assert list(Collection(g, g.value(rule, swrl.head)))

def number(item, prop):
    return Decimal(str(g.value(item, app[prop])))

patterns = list(g.objects(app.warmup, app.hasExercise))
routes = list(g.subjects(RDF.type, app.Route))
checks = {
    "Число нот <= 0": [x for x in patterns if number(x, "noteCount") <= 0],
    "Длительность ноты <= 0": [x for x in patterns if number(x, "secondsPerNote") <= 0],
    "Опора ниже MIDI 36": [x for x in routes if number(x, "rootMidi") < 36],
    "Опора выше MIDI 72": [x for x in routes if number(x, "rootMidi") > 72],
    "Подъём вне 0, 2, 4": [x for x in routes if number(x, "climbSemitones") not in {0, 2, 4}],
    "Расчётная и заданная длительность различаются": [x for x in patterns if number(x, "noteCount") * number(x, "secondsPerNote") != number(x, "durationSeconds")],
}
print(f"RDF-структура: {len(rules)} правил, у всех есть тело и заключение.")
print("Расчёт длительности: количество нот × секунд на ноту.")
for name, items in checks.items():
    print(f"{name}: {len(items)}" + ("; " + ", ".join(str(x) for x in items) if items else ""))
print("Проверены условия по исходным данным Python. SWRL-движок не запускался.")
