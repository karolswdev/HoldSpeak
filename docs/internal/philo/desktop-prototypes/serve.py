#!/usr/bin/env python3
"""Serve the existing production bundle without starting HoldSpeak or a DB."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
BUILD=ROOT/'holdspeak/static/_built'
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith(('/api/','/ws')):
            body=json.dumps({'code':'philo_static_probe','message':'No runtime in host rendering probe'}).encode()
            self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body);return
        super().do_GET()
    def translate_path(self,path):
        rel=path.split('?',1)[0].removeprefix('/_built/').lstrip('/')
        candidate=(BUILD/rel).resolve()
        if not candidate.is_relative_to(BUILD.resolve()):return str(BUILD/'missing')
        return str(candidate if candidate.is_file() else BUILD/'index.html')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=18789);a=p.parse_args()
    if not (BUILD/'index.html').exists():raise SystemExit('Build web first')
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
