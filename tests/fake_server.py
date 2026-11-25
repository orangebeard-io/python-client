"""A tiny in-process fake of the Orangebeard listener API (v3) used by the client tests."""
import asyncio
import json
import threading
import time
import uuid

from aiohttp import web


class FakeOrangebeardServer:
    def __init__(self, delay: float = 0.0):
        self.delay = delay
        self.requests = []  # dicts: method, path, body, content_type, time
        self._runner = None
        self._loop = None
        self._thread = None
        self.url = None

    # --- request handling -------------------------------------------------
    async def _record(self, request: web.Request):
        raw = await request.read()
        ctype = request.content_type
        body = None
        if raw and ctype == 'application/json':
            body = json.loads(raw)
        elif raw:
            body = raw
        self.requests.append({
            'method': request.method,
            'path': request.path,
            'body': body,
            'content_type': ctype,
            'time': time.monotonic(),
        })
        if self.delay:
            await asyncio.sleep(self.delay)

    async def _handle(self, request: web.Request):
        await self._record(request)
        path = request.path
        body = self.requests[-1]['body']
        if path.endswith('/test-run/start') or path.endswith('/test/start') or path.endswith('/step/start') \
                or path.endswith('/log'):
            return web.json_response(str(uuid.uuid4()))
        if path.endswith('/suite/start'):
            return web.json_response([{'suiteUUID': str(uuid.uuid4())} for _ in body['suiteNames']])
        if path.endswith('/log/batch'):
            return web.Response(status=204)
        if path.endswith('/attachment'):
            return web.Response(text=str(uuid.uuid4()))
        return web.Response(status=204)  # finish calls

    # --- lifecycle --------------------------------------------------------
    def start(self):
        ready = threading.Event()

        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            app = web.Application(client_max_size=50 * 1024 ** 2)
            app.router.add_route('*', '/{tail:.*}', self._handle)
            self._runner = web.AppRunner(app)
            self._loop.run_until_complete(self._runner.setup())
            site = web.TCPSite(self._runner, '127.0.0.1', 0)
            self._loop.run_until_complete(site.start())
            port = site._server.sockets[0].getsockname()[1]
            self.url = f'http://127.0.0.1:{port}'
            ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        ready.wait(10)
        return self

    def stop(self):
        async def shutdown():
            await self._runner.cleanup()

        asyncio.run_coroutine_threadsafe(shutdown(), self._loop).result(10)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(5)

    # --- helpers ----------------------------------------------------------
    def paths(self):
        return [(r['method'], r['path'].split('/v3/proj/', 1)[-1]) for r in self.requests]

    def of(self, suffix: str):
        return [r for r in self.requests if r['path'].endswith(suffix)]
