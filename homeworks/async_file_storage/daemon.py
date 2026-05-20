import argparse
import asyncio
import json
from pathlib import Path

import aiofiles
import aiohttp
import yaml
from aiohttp import web

root_path = Path(__file__).parent.resolve()


class DaemonAsyncHttpServer:
    def __init__(self, config):
        self.config = config
        self.port = config["port"]
        self.directory = config["directory"]
        self.to_save_locally = config["to_save_locally"]
        self.nodes = config["nodes"]
        self.file_lifetime = config["file_lifetime"]

    async def read_file(self, filename):
        async with aiofiles.open(filename, "r") as f:
            content = await f.read()
        return content

    async def write_file(self, text, file_lifetime):
        async with aiofiles.tempfile.NamedTemporaryFile(delete=True) as temp_file:
            await temp_file.write(text)
            await asyncio.sleep(file_lifetime)

    async def fetch(self, session, url):
        async with session.get(url) as response:
            return await response.text()

    async def upload_file(self, reqeust):
        request_body = await reqeust.json()

        async with aiohttp.ClientSession() as session:
            for filename, content in request_body.items():
                tasks = [
                    self.fetch(session=session, url=f"http://{daemon_socket}/{filename}?redirected=True")
                    for daemon_socket in (*self.nodes, f"localhost:{self.port}")
                ]

                results = await asyncio.gather(*tasks)

                if "".join(results):
                    return web.Response(text="Файл с таким названием уже существует!")

                await self.write_file(content, file_lifetime=self.file_lifetime)

                return web.Response(status=201)

    async def handle(self, request):
        query_params = request.rel_url.query
        redirected = query_params.get("redirected", False)
        filename = request.match_info.get("filename")
        filepath = Path(root_path / self.directory / f"{filename}.txt")

        if filepath.is_file():
            text = await self.read_file(filepath)
            if redirected:
                return web.json_response({"text": text, "port": self.port})
            return web.Response(text=text)

        if not redirected:
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self.fetch(session=session, url=f"http://{daemon_socket}/{filename}?redirected=True")
                    for daemon_socket in self.nodes
                ]

                results = await asyncio.gather(*tasks)

                results = "".join(results)
                if results:
                    results = json.loads(results)
                    text = results.get("text")
                    if self.to_save_locally[f"localhost:{results['port']}"]:
                        await self.write_file(text=text, file_lifetime=self.file_lifetime)

                    return web.Response(text=text)
                return web.Response(status=404)

    def run(self):
        app = web.Application()
        app.add_routes([
            web.get(r"/{filename:[^\.]+}", self.handle),
            web.post("/upload", self.upload_file),
        ])
        web.run_app(
            app=app,
            port=self.port,
        )


def parse_config(config_path: str) -> dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("daemon_config", type=str, nargs="?", help="An optional str positional argument")
    args: argparse.Namespace = parser.parse_args()

    config: dict = parse_config(str(root_path / "config.yaml"))["daemons"][args.daemon_config]
    daemon_server_a = DaemonAsyncHttpServer(config=config)
    daemon_server_a.run()


if __name__ == "__main__":
    main()
