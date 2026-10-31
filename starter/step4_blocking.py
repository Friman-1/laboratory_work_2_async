"""Шаг 4 (дополнительный). Блокировка event loop.

Ниже готовый асинхронный сервер из шага 3б. Но теперь клиент "bob"
прислал не запрос в базу, а задачу на тяжёлые вычисления: функция
heavy_compute. Она синхронная и работает 1-3 секунды в зависимости от машины.

Задание 4а:
  В handle_request для клиента "bob" вызовите heavy_compute()
  вместо await asyncio.sleep(duration). Остальные клиенты по-прежнему
  ждут через asyncio.sleep. Запустите.
  Что произошло с остальными клиентами? Почему, ведь всё написано на async?

Задание 4б:
  Исправьте так, чтобы остальные клиенты не ждали bob. Два инструмента:
    await asyncio.to_thread(heavy_compute)
    await loop.run_in_executor(pool, heavy_compute)
  где loop = asyncio.get_running_loop(), а pool — это ProcessPoolExecutor
  из concurrent.futures, открытый через with в main.
  Попробуйте оба. Порядок строк в выводе должен стать как в шаге 3б,
  время bob зависит от машины.

Задание 4в (если осталось время):
  Сделайте тяжёлыми трёх клиентов: bob, dave и eve. Сравните общее время
  для to_thread и для пула процессов. Почему оно отличается? Вспомните GIL.
"""

import argparse
import asyncio
from concurrent.futures import ProcessPoolExecutor

from timer import log, print_time

CLIENTS = [
    ("alice", 0.5),
    ("bob", 5.0),
    ("carol", 0.5),
    ("dave", 0.5),
    ("eve", 0.5),
]


def heavy_compute() -> int:
    """Синхронные тяжёлые вычисления, 1-3 секунды."""
    h = 0
    for i in range(30_000_000):
        h = (h * 31 + i) & 0xFFFFFFFF
    return h


async def handle_request(
        client: str,
        duration: float,
        mode: str,
        heavy_clients: set[str],
        pool: ProcessPoolExecutor | None = None,
) -> None:
    log(f"{client}: запрос принят")
    if client in heavy_clients:
        if mode == "block":
            # 4а: синхронный вызов, внутри нет ни одного await —
            # event loop не может переключиться, пока вычисление не закончится.
            heavy_compute()
        elif mode == "thread":
            # 4б: вычисление уходит в отдельный поток, корутина ждёт его через await.
            await asyncio.to_thread(heavy_compute)
        elif mode == "process":
            # 4б: вычисление уходит в отдельный процесс из пула.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(pool, heavy_compute)
    else:
        await asyncio.sleep(duration)
    log(f"{client}: ответ отправлен")


async def main(mode: str, heavy_clients: set[str]) -> None:
    if mode == "process":
        with ProcessPoolExecutor() as pool:
            coroutines = [
                handle_request(client, duration, mode, heavy_clients, pool)
                for client, duration in CLIENTS
            ]
            await asyncio.gather(*coroutines)
    else:
        coroutines = [
            handle_request(client, duration, mode, heavy_clients)
            for client, duration in CLIENTS
        ]
        await asyncio.gather(*coroutines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="process", choices=["block", "thread", "process"])
    parser.add_argument("--many", action="store_true", help="4в: тяжёлые bob, dave и eve")
    args = parser.parse_args()

    heavy = {"bob", "dave", "eve"} if args.many else {"bob"}
    with print_time():
        asyncio.run(main(args.mode, heavy))
