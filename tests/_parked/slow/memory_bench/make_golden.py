"""Write ``keyword_golden.json`` with the search code of ANOTHER tree.

The golden file is the answer of ``memory.search`` before the memory index
existed (origin/main at bacf8308a).  Make it again only when the corpus or
the questions change, and only with a tree that has no memory index:

    PYTHONPATH=<a checkout of the old tree> uv run python \
        tests/memory_bench/make_golden.py tests/memory_bench \
        tests/memory_bench/keyword_golden.json
"""
import importlib.util, json, sys, tempfile
from pathlib import Path
bench_dir=Path(sys.argv[1])
def load(name):
    spec=importlib.util.spec_from_file_location(name, bench_dir/f"{name}.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
import holdspeak; print("holdspeak from", holdspeak.__file__, file=sys.stderr)
from holdspeak.db import Database
corpus=load("corpus"); bench=load("bench")
db=Database(Path(tempfile.mkdtemp())/"g.db"); refs=corpus.build_corpus(db)
snap=bench.keyword_snapshot(db, refs)
Path(sys.argv[2]).write_text(json.dumps(snap, indent=1, sort_keys=True, ensure_ascii=False)+"\n")
print(len(snap), "answers", file=sys.stderr)
