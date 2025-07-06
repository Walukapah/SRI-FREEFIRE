from http.server import BaseHTTPRequestHandler
from functools import wraps
from urllib.parse import urlparse, parse_qs
from cachetools import TTLCache
import lib.lib2 as lib2
import json
import asyncio

cache = TTLCache(maxsize=100, ttl=300)

def cached_endpoint(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = args[0]
            query = parse_qs(urlparse(handler.path).query)
            cache_key = (handler.path, tuple(query.items()))
            
            if cache_key in cache:
                return cache[cache_key]
            else:
                result = func(*args, **kwargs)
                cache[cache_key] = result
                return result
        return wrapper
    return decorator

class handler(BaseHTTPRequestHandler):
    @cached_endpoint()
    def do_GET(self):
        if not self.path.startswith('/api/account'):
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return

        query = parse_qs(urlparse(self.path).query)
        region = query.get('region', [None])[0]
        uid = query.get('uid', [None])[0]

        if not uid:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Invalid request",
                "message": "Empty 'uid' parameter. Please provide a valid 'uid'."
            }).encode())
            return

        if not region:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Invalid request",
                "message": "Empty 'region' parameter. Please provide a valid 'region'."
            }).encode())
            return

        try:
            return_data = asyncio.run(lib2.GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow"))
            formatted_json = json.dumps(return_data, indent=2, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(formatted_json.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Server error",
                "message": str(e)
            }).encode())
