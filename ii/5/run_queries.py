from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph


folder = Path(__file__).parent
graph = Graph().parse(folder.parent / "4" / "ontology.ttl", format="turtle")
DeductiveClosure(OWLRL_Semantics).expand(graph)

lines = []
for query_file in sorted((folder / "queries").glob("*.rq")):
    lines.append(query_file.name)
    rows = list(graph.query(query_file.read_text()))
    for row in rows:
        lines.append("  " + " | ".join(str(value) for value in row))
    lines.append(f"  Строк: {len(rows)}")
    lines.append("")

output = "\n".join(lines)
(folder / "results.txt").write_text(output)
print(output)
