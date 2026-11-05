"""Run the saved queries on the asserted graph, as Protégé SPARQL Query does."""
from pathlib import Path
from rdflib import Graph

here = Path(__file__).resolve().parent
graph = Graph().parse(here / "ontology.ttl", format="turtle")
lines = [f"Исходных троек: {len(graph)}", "Вывод OWL перед запросами не запускался."]
for path in sorted((here / "queries").glob("*.rq")):
    result = graph.query(path.read_text(encoding="utf-8"))
    lines.extend(["", path.name, " | ".join(str(v) for v in result.vars)])
    rows = list(result)
    lines.extend(" | ".join(str(x) if x is not None else "—" for x in row) for row in rows)
    lines.append(f"Строк: {len(rows)}")
print("\n".join(lines))
