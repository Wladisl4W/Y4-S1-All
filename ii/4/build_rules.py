"""Serialize the seven readable SWRL rules into ontology.ttl."""
from pathlib import Path
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection
from rdflib.namespace import XSD

HERE = Path(__file__).resolve().parent
APP = Namespace("https://example.org/intonation-study#")
SWRL = Namespace("http://www.w3.org/2003/11/swrl#")
SWRLB = Namespace("http://www.w3.org/2003/11/swrlb#")
graph = Graph().parse(HERE.parent / "2" / "ontology.ttl", format="turtle")
for exercise in graph.objects(APP.warmup, APP.hasExercise):
    graph.add((exercise, RDF.type, APP.Exercise))
for prefix, uri in [("", APP), ("swrl", SWRL), ("swrlb", SWRLB)]:
    graph.bind(prefix, uri)
graph.add((APP.SuspiciousDescription, RDF.type, OWL.Class))
graph.add((APP.SuspiciousDescription, RDFS.label, Literal("Сомнительное описание", lang="ru")))
graph.add((APP.estimatedDurationSeconds, RDF.type, OWL.DatatypeProperty))

def var(name):
    uri = APP["var_" + name]
    graph.add((uri, RDF.type, SWRL.Variable))
    return uri

def class_atom(name, value):
    node = BNode()
    graph.add((node, RDF.type, SWRL.ClassAtom))
    graph.add((node, SWRL.classPredicate, APP[name]))
    graph.add((node, SWRL.argument1, var(value)))
    return node

def property_atom(name, subject, value):
    node = BNode()
    graph.add((node, RDF.type, SWRL.DatavaluedPropertyAtom))
    graph.add((node, SWRL.propertyPredicate, APP[name]))
    graph.add((node, SWRL.argument1, var(subject)))
    graph.add((node, SWRL.argument2, var(value)))
    return node

def builtin(name, *args):
    node, members = BNode(), BNode()
    graph.add((node, RDF.type, SWRL.BuiltinAtom))
    graph.add((node, SWRL.builtin, SWRLB[name]))
    graph.add((node, SWRL.arguments, members))
    Collection(graph, members, [var(a) if isinstance(a, str) else Literal(a, datatype=XSD.integer) for a in args])
    return node

def rule(name, body, head):
    node, body_list, head_list = APP[name], BNode(), BNode()
    graph.add((node, RDF.type, SWRL.Imp))
    graph.add((node, SWRL.body, body_list))
    graph.add((node, SWRL.head, head_list))
    Collection(graph, body_list, body)
    Collection(graph, head_list, head)

rule("invalidNoteCount", [class_atom("Exercise", "e"), property_atom("noteCount", "e", "n"), builtin("lessThanOrEqual", "n", 0)], [class_atom("SuspiciousDescription", "e")])
rule("invalidPace", [class_atom("Exercise", "e"), property_atom("secondsPerNote", "e", "s"), builtin("lessThanOrEqual", "s", 0)], [class_atom("SuspiciousDescription", "e")])
rule("rootBelowLimit", [class_atom("Route", "r"), property_atom("rootMidi", "r", "m"), builtin("lessThan", "m", 36)], [class_atom("SuspiciousDescription", "r")])
rule("rootAboveLimit", [class_atom("Route", "r"), property_atom("rootMidi", "r", "m"), builtin("greaterThan", "m", 72)], [class_atom("SuspiciousDescription", "r")])
rule("unsupportedClimb", [class_atom("Route", "r"), property_atom("climbSemitones", "r", "c"), builtin("notEqual", "c", 0), builtin("notEqual", "c", 2), builtin("notEqual", "c", 4)], [class_atom("SuspiciousDescription", "r")])
rule("estimateDuration", [class_atom("Exercise", "e"), property_atom("noteCount", "e", "n"), property_atom("secondsPerNote", "e", "s"), builtin("multiply", "d", "n", "s")], [property_atom("estimatedDurationSeconds", "e", "d")])
rule("durationMismatch", [class_atom("Exercise", "e"), property_atom("durationSeconds", "e", "actual"), property_atom("estimatedDurationSeconds", "e", "estimated"), builtin("notEqual", "actual", "estimated")], [class_atom("SuspiciousDescription", "e")])
(HERE / "ontology.ttl").write_text(graph.serialize(format="turtle").rstrip() + "\n", encoding="utf-8")
print(f"Serialized 7 SWRL rules; {len(graph)} triples")
