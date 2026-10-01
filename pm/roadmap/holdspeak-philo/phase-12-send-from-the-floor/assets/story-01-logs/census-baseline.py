import json
from pathlib import Path
import subprocess
import sys

root = Path.cwd()
sys.path.insert(0, str(root / 'scripts'))
import holdspeak.web.routes.monday_brief as brief_routes
base = '27d8bf1acffa2a93637e42724949f0426b1dd9b6'
def committed(path):
    return subprocess.check_output(['git', 'show', f'{base}:{path}'], text=True)
exec(compile(committed('holdspeak/web/routes/monday_brief.py'), 'base:monday_brief.py', 'exec'), brief_routes.__dict__)
import holdspeak.web.routes as route_exports
route_exports.build_monday_brief_router = brief_routes.build_monday_brief_router
import philo_graph_reference as graph
base_openapi = json.loads(committed('docs/generated/openapi.json'))
graph.openapi_routes = lambda root: {(method.upper(), path) for path, operations in base_openapi['paths'].items() for method in operations if method.upper() in graph.HTTP_METHODS}
lines = graph.census(json.loads(committed('docs/generated/graph.json')), root)
print(f'BASELINE {base}: committed brief router, graph and OpenAPI; same environment; no working-tree change.')
print('\n'.join(lines))
print('COUNTS', {kind:sum(line.startswith(kind+':') for line in lines) for kind in ['new','removed','changed','stale','miscited','unread']})
current = Path('.tmp/philo-12-01/graph-census.log').read_text().splitlines()
base_facts = {line for line in lines if line.split(':')[0] in {'new','removed','changed','stale','miscited','unread'}}
current_facts = {line for line in current if line.split(':')[0] in {'new','removed','changed','stale','miscited','unread'}}
print('ADDED', sorted(current_facts-base_facts))
print('REMOVED', sorted(base_facts-current_facts))
assert current_facts-base_facts == {'new: http GET /api/brief/{brief_id} has no edge (read_by_id)'}
assert not base_facts-current_facts
