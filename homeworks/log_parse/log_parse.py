from collections import defaultdict
from datetime import datetime as dt
from pathlib import Path

LOG_PATH = Path(__file__).parent / "log.log"
ALLOWED_METHODS: tuple[str] = ("GET", "PUT", "POST")  # ty:ignore[invalid-assignment]
FILE_EXTENSIONS: tuple[str] = (".jpg", "png", ".svg", ".css", ".js", ".gif")  # ty:ignore[invalid-assignment]


def _has_request_method(line: str, allowed_methods: tuple[str]) -> list[str] | bool:
    if any(method in line for method in allowed_methods):
        return line.split()

    return False


def _parse_log_data(log_list: list[str]) -> str:
    return (log_list[0] + " " + log_list[1]).strip("[").strip("]")


def parse(
    ignore_files=False,
    ignore_urls=[],
    start_at=None,
    stop_at=None,
    request_type: str | None = None,
    ignore_www=False,
    slow_queries=False,
):
    most_requested_urls = defaultdict(lambda: defaultdict(int))

    if start_at:
        start_at = dt.strptime(start_at, "%d/%b/%Y %H:%M:%S")

    if stop_at:
        stop_at = dt.strptime(stop_at, "%d/%b/%Y %H:%M:%S")

    with open(LOG_PATH, "r") as f:
        for log_line in f:
            try:
                allowed_methods = tuple(request_type) if request_type is not None else ALLOWED_METHODS
                log_list = _has_request_method(line=log_line, allowed_methods=allowed_methods)
                if not log_list:
                    continue

                log_dt = dt.strptime(_parse_log_data(log_list), "%d/%b/%Y %H:%M:%S")

                if start_at is not None and log_dt < start_at:
                    continue

                if stop_at is not None and log_dt > stop_at:
                    continue

                request_url: str = log_list[3]

                if any(ignore_url in request_url for ignore_url in ignore_urls):
                    continue

                if ignore_www:
                    request_url = request_url.replace("www.", "")

                if ignore_files and any(extension in request_url for extension in FILE_EXTENSIONS):
                    continue

                if slow_queries:
                    most_requested_urls[request_url]["request_time"] += int(log_list[-1])

                most_requested_urls[request_url]["cnt"] += 1

            except Exception:
                print(f"{log_line=}")
                continue

    if slow_queries:
        return sorted((item["request_time"] // item["cnt"] for item in most_requested_urls.values()), reverse=True)[:5]

    return sorted((item["cnt"] for item in most_requested_urls.values()), reverse=True)[:5]
