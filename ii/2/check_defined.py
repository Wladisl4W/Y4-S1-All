"""Check which named individuals are inferred for each defined class."""
from pathlib import Path
from rdflib import Graph, Namespace, RDF, OWL
from owlrl import DeductiveClosure, OWLRL_Semantics

here = Path(__file__).resolve().parent
app = Namespace("https://example.org/intonation-study#")
classes = ["ExerciseInCatalog", "PatternWithRoute", "SetWithPattern", "ModeWithExercise", "ApplicationWithHistory"]
graph = Graph().parse(here / "ontology.ttl", format="turtle")
asserted = {(item, cls) for cls in classes for item in graph.subjects(RDF.type, app[cls])}
DeductiveClosure(OWLRL_Semantics).expand(graph)
lines = ["Проверка OWL RL; ни один из перечисленных типов не задан экземплярам вручную."]
for cls in classes:
    items = sorted(item.split("#")[-1] for item in graph.subjects(RDF.type, app[cls]) if (item, cls) not in asserted and (item, RDF.type, OWL.NamedIndividual) in graph)
    lines.append(f"{cls}: {', '.join(items) if items else 'нет'}")
print("\n".join(lines))
