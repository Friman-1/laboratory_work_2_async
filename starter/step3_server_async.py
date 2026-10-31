import asyncio
from timer import log, print_time

CLIENTS = [
    ("alice", 0.5),
    ("bob", 5.0),
    ("carol", 0.5),
    ("dave", 0.5),
    ("eve", 0.5),
]


async def handle_request(client: str, duration: float) -> None:
    log(f"{client}: запрос принят")
    await asyncio.sleep(duration)
    log(f"{client}: ответ отправлен")


async def main() -> None:
    coroutines = [handle_request(client, duration) for client, duration in CLIENTS]
    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    with print_time():
        asyncio.run(main())