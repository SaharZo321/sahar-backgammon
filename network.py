import ipaddress
import queue
import socket
from threading import Thread
from typing import Callable, Any
import pickle
import time

import psutil
from backgammon import OnlineBackgammon, Backgammon
from models import OnlineGameState, ServerFlags
from models import Move
from pydantic_extra_types.color import Color
import asyncio


class BGServer:
    server: asyncio.Server
    loop: asyncio.AbstractEventLoop

    def __init__(
        self,
        local_color: Color,
        online_color: Color,
        port: int,
        buffer_size=2048,
        timeout: float = 10,
    ) -> None:
        self._ip = self.ip4_addresses()
        self._stop_event = asyncio.Event()
        self._buffer_size = buffer_size
        self.online_backgammon = OnlineBackgammon(
            local_color=local_color, online_color=online_color
        )
        self._timeout = timeout
        self._port = port
        self.connected = False
        self._game_started_event = asyncio.Event()
        self.server_thread: Thread | None = None

    def ip4_addresses(self) -> list[str]:
        ip_list = []
        interfaces = psutil.net_if_addrs()
        for if_name in interfaces:
            interface = interfaces[if_name]
            for s in interface:
                if (
                    s.family == socket.AF_INET
                    and ipaddress.ip_address(s.address).is_private
                ):
                    ip_list.append(s.address)

        return ip_list

    def _get_game(self) -> Backgammon:
        return self.online_backgammon.game

    def local_get_game_state(self) -> OnlineGameState:
        return self.online_backgammon.get_online_game_state()

    async def close_connection(writer: asyncio.StreamWriter, address: str):
        print(f"Closing connection to {address}")
        writer.close()
        await writer.wait_closed()
    
    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        address = writer.get_extra_info(name="peername")
        print(f"{address} connected to the server")

        if self._game_started_event.is_set():
            print(f"{address} joined to an active game")
            await self.close_connection(writer=writer, address=address)
            return
        
        self._game_started_event.set()
        self.connected = True

        while not self._stop_event.is_set():
            try:
                raw_data = await asyncio.wait_for(
                    reader.read(self._buffer_size), timeout=self._timeout
                )
                if not raw_data:
                    print(f"Received no data from {address}")
                    break
                request = pickle.loads(raw_data)
                print(f"Received data from {address}: {request}")
                if request == ServerFlags.get_current_state:
                    pass
                elif request == ServerFlags.undo:
                    self.local_undo()
                elif request == ServerFlags.done:
                    self.local_done()
                elif request == ServerFlags.leave:
                    print(f"Player2 ({address}) left the game.")
                    self.connected = False
                    response = self.online_backgammon.manipulate_board()
                    writer.write(pickle.dumps(response))
                    self.online_backgammon.is_player2_connected = False
                    break
                elif type(request) is Move:
                    manipulated_move: Move = request
                    move = self.online_backgammon.manipulate_move(move=manipulated_move)
                    self.local_move(move)
                elif type(request) is Color:
                    self.online_backgammon.online_color = request

                response = self.online_backgammon.manipulate_board()
                await self.send_data(writer=writer, data=response)
                print(f"Data sent back to: {address}: {response}")

            except TimeoutError:
                print(f"Lost connection to {address}: waiting for connection")
                self.connected = False
                break
            except asyncio.CancelledError:
                self.connected = False
                print(f"Connection to {address} cancelled")
                break

        await self.close_connection(writer=writer, address=address)
    
    async def send_data(self, writer: asyncio.StreamWriter, data):
        writer.write(pickle.dumps(data))
        await writer.drain()

    def run_server(self):
        if self._stop_event.is_set():
            self._stop_event = asyncio.Event()
            print("Starting again.")

        async def start_server():
            self.server = await asyncio.start_server(
                host=self._ip,
                port=self._port,
                client_connected_cb=self.handle_client,
                limit=self._buffer_size,
            )
            addresses = ", ".join(
                str(sock.getsockname()) for sock in self.server.sockets
            )
            print(f"Serving on {addresses}")

            async with self.server:
                try:
                    await self.server.serve_forever()
                except asyncio.CancelledError:
                    print("Server stopped.")

        def start():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(start_server())

        if self.server_thread is None:
            self.server_thread = Thread(target=start)
            self.server_thread.start()

    def stop_server(self):
        print("Server shutting down")
        self._stop_event.set()
        async def close_server():
            if self.server:
                self.server.close()
                await self.server.wait_closed()

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(close_server(), self.loop)

        if self.server_thread is not None:
            self.server_thread.join()
            self.server_thread = None

    def has_started(self) -> bool:
        return self._game_started_event.is_set()

    def local_move(self, move: Move) -> OnlineGameState:
        backgammon = self._get_game()
        backgammon.handle_move(move=move)
        return self.local_get_game_state()

    def local_done(self) -> OnlineGameState:
        backgammon = self._get_game()
        if not backgammon.is_turn_done():
            return self.local_get_game_state()

        if backgammon.is_game_over():
            self.online_backgammon.new_game()
        else:
            backgammon.switch_turn()

        return self.local_get_game_state()

    def local_undo(self) -> OnlineGameState:
        backgammon = self._get_game()
        backgammon.undo()
        return self.local_get_game_state()

    def is_alive(self) -> bool:
        return self.server.is_serving()


class NetworkClient:
    def __init__(
        self,
        host_ip: str,
        port: int,
        buffer_size=2048,
        timeout: float = 10,
    ) -> None:
        self.host = host_ip
        self.port = port
        self._buffer_size = buffer_size
        self._timeout = timeout
        self._timed_out_event = asyncio.Event()
        self._started_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self.request_queue: queue.Queue[tuple[Any, Callable[[Any], None]]] = (
            queue.Queue()
        )
        self.time_on_receive = 0

        def connect_threaded():
            asyncio.run(self.handle_connection())
            print("Client disconnected")

        self.client_thread = Thread(target=connect_threaded)

    async def handle_connection(self):
        try:
            reader, writer = await asyncio.wait_for(
                fut=asyncio.open_connection(host=self.host, port=self.port),
                timeout=self._timeout,
            )
            self._started_event.set()
            print(f"Connected to {self.host}")
        except ConnectionRefusedError:
            print(f"{self.host} refused to connect")
            self._stop_event.set()
            return
        except:
            print(f"Could not establish connection to {self.host}")
            self._stop_event.set()
            return
        # loop to send messages

        while not self._stop_event.is_set():
            try:
                data, on_recieve = self.request_queue.get(timeout=1)
                await self.handle_send_data(data=data, writer=writer)
                self.request_queue.task_done()
                await self.handle_recieved_data(on_recieve=on_recieve, reader=reader)
            except queue.Empty:
                print("Empty queue...")
                continue

        writer.close()
        await writer.wait_closed()
        print("closed writer")

    async def handle_send_data(self, data, writer: asyncio.StreamWriter):
        writer.write(pickle.dumps(data))
        await writer.drain()
        print(f"Data sent: {data}")
        

    async def handle_recieved_data(
        self, on_recieve: Callable[[Any], None], reader: asyncio.StreamReader
    ):
        try:
            raw_data = await asyncio.wait_for(
                reader.read(self._buffer_size), timeout=self._timeout
            )
            if not raw_data:
                self.disconnect(threaded=True)
                print("Received no data, closing client")
                return
            print("Data recieved.")
            data = pickle.loads(raw_data)
            on_recieve(data)
            self.time_on_receive = time.time()
        except TimeoutError:
            self.disconnect(threaded=True)
            print("Timed out... Closing client")
            
    def send(self, data, on_recieve: Callable[[Any], None] = lambda x: None):
        if not self._started_event.is_set() or self._stop_event.is_set():
            print("Not connected, cannot send")
            return
        request = (data, on_recieve)
        self.request_queue.put(request)

    def connect(self):
        if self._started_event.is_set():
            print("Already connected connect again.")
            return
        self.request_queue = queue.Queue()
        self._started_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self.client_thread.start()

    def disconnect(self, data=None, threaded=False):
        if data is not None:
            self.send(data=data)
            self.request_queue.join()
        self._stop_event.set()
        if not threaded:
            self.client_thread.join()
        print(f"Disconnected from: {self.host}")

    def is_connected(self):
        return not self._stop_event.is_set()

    def has_started(self):
        return self._started_event.is_set()

    def time_from_last_recieve(self):
        return time.time() - self.time_on_receive
