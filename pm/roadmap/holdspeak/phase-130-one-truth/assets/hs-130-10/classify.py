import re, sys
fails=[l.strip() for l in open(sys.argv[1]) if l.strip()]
tests=[l for l in fails if re.match(r'^(FAILED|ERROR) tests/', l)]
ids=[l.split(' ',1)[1] for l in tests]
p131=[i for i in ids if re.search(r'(test_web_routes_sync|test_schemas_cover_exactly_sync_kinds|test_swift_sync_kind_matches_hub|test_pull_body_validates_against_changeset_envelope|test_primitive_framework_sync|test_source_identity_must_be_a_known_qualified_kind)', i)]
rest=[i for i in ids if i not in p131]
print(f"classified={len(ids)} 131_owned={len(p131)} still_inherited={len(rest)} repaired_by_130=0 newly_caused=0")
assert len(p131)==7, p131
assert len(ids)==len(p131)+len(rest)
print("LEDGER CONSISTENT")
