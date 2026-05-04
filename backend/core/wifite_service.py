import asyncio
import subprocess
import time
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from utils.logging import get_logger

logger = get_logger(__name__)


class ToolStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ToolProcessInfo:
    pid: int
    command: str
    start_time: float
    status: ToolStatus
    output_lines: int = 0


class WifiteService:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.process: Optional[subprocess.Popen] = None
        self.status = ToolStatus.IDLE
        self.process_info: Optional[ToolProcessInfo] = None
        self.monitor_task: Optional[asyncio.Task] = None
        # For tracking the last command we ran (for status)
        self.last_command: str = ""
        # Braille animation state for visual feedback
        self._braille_index = 0
        self._braille_chars = [chr(0x2800 + i) for i in range(256)]  # All Braille patterns

    async def handle_command(self, command: str, websocket):
        """Handle incoming WebSocket commands to control the tool"""
        if command == "start":
            await self.start_tool()
        elif command == "stop":
            await self.stop_tool()
        elif command == "status":
            await self.send_status(websocket)
        else:
            await self.websocket_manager.send_error(
                "unknown_command", f"Unknown command: {command}", websocket=websocket
            )

    async def send_status(self, websocket):
        """Send current status to a specific websocket"""
        if self.process_info:
            running_time = time.time() - self.process_info.start_time
            status_data = {
                "status": self.status.value,
                "pid": self.process_info.pid if self.process else None,
                "output_lines": self.process_info.output_lines,
                "running_time": running_time,
                "command": self.process_info.command,
            }
        else:
            status_data = {
                "status": self.status.value,
                "pid": None,
                "output_lines": 0,
                "running_time": 0.0,
                "command": "",
            }
        await self.websocket_manager.send_personal_message(
            {"type": "status", "data": status_data}, websocket
        )

    async def start_tool(self):
        """Start the wifite2 subprocess"""
        if self.status == ToolStatus.RUNNING:
            logger.warning("Tool is already running")
            return

        # Build the wifite2 command
        # We'll run wifite2 with the arguments we want for continuous scanning
        # For now, we'll use a simple command that scans and captures handshakes
        # In a real scenario, we might want to make this configurable
        command = ["wifite", "-i", "wlan0mon", "--pow", "25", "--dict", "/usr/share/dict/rockyou.txt"]
        # Note: We assume the interface is already in monitor mode. In production, we might need to handle that.

        logger.info(f"Starting wifite2 with command: {' '.join(command)}")

        try:
            # Start the process with pipes for stdout and stderr
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            # Update process info
            self.process_info = ToolProcessInfo(
                pid=self.process.pid,
                command=" ".join(command),
                start_time=time.time(),
                status=ToolStatus.RUNNING,
            )
            self.status = ToolStatus.RUNNING
            self._braille_index = 0  # Reset animation when starting

            # Start monitoring task
            self.monitor_task = asyncio.create_task(self._monitor_process())

            # Broadcast system event
            await self.websocket_manager.send_system_event(
                "tool_started",
                {"pid": self.process.pid, "command": self.process_info.command},
            )

        except Exception as e:
            logger.error(f"Failed to start wifite2: {e}")
            self.status = ToolStatus.ERROR
            await self.websocket_manager.send_error(
                "start_failed", f"Failed to start wifite2: {str(e)}"
            )

    async def stop_tool(self):
        """Stop the running wifite2 subprocess"""
        if self.status != ToolStatus.RUNNING:
            logger.warning("Tool is not running")
            return

        logger.info(f"Stopping wifite2 (PID: {self.process.pid})")
        self.status = ToolStatus.STOPPED

        # Terminate the process
        if self.process:
            self.process.terminate()
            try:
                # Wait for the process to terminate (with timeout)
                await asyncio.wait_for(
                    self._wait_for_process(), timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate gracefully, killing")
                self.process.kill()
                await self._wait_for_process()

        # Update process info
        if self.process_info:
            self.process_info.status = ToolStatus.STOPPED

        # Cancel the monitor task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        # Broadcast system event
        await self.websocket_manager.send_system_event(
            "tool_stopped",
            {"pid": self.process_info.pid if self.process_info else None},
        )

        # Clean up the process reference
        self.process = None

    async def _wait_for_process(self):
        """Wait for the process to terminate"""
        while self.process.poll() is None:
            await asyncio.sleep(0.1)

    async def _monitor_process(self):
        """Monitor process output and broadcast via WebSocket"""
        logger.info(f"Starting output monitoring for PID {self.process.pid}")

        # Create tasks to monitor stdout and stderr
        stdout_task = asyncio.create_task(
            self._monitor_stream(self.process.stdout, "stdout")
        )
        stderr_task = asyncio.create_task(
            self._monitor_stream(self.process.stderr, "stderr")
        )

        # Wait for the process to complete
        return_code = await asyncio.create_subprocess_exec(
            *self.process.args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).wait()

        # Wait for the monitoring tasks to finish (they will when the streams are closed)
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

        # Update final status
        if self.status != ToolStatus.STOPPED:
            if return_code == 0:
                self.status = ToolStatus.COMPLETED
                if self.process_info:
                    self.process_info.status = ToolStatus.COMPLETED
            else:
                self.status = ToolStatus.ERROR
                if self.process_info:
                    self.process_info.status = ToolStatus.ERROR

        # Broadcast system event
        await self.websocket_manager.send_system_event(
            "tool_completed",
            {
                "pid": self.process.pid if self.process else None,
                "return_code": return_code,
                "status": self.status.value,
            },
        )

        # Clean up
        self.process = None

    async def _monitor_stream(self, stream, stream_name: str):
        """Monitor a stream (stdout/stderr) and broadcast lines"""
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, stream.readline
                )
                if not line:
                    break  # Stream closed

                line = line.rstrip("\n\r")
                if line:
                    # Update output lines count
                    if self.process_info:
                        self.process_info.output_lines += 1

                    # === VISUAL POLISH: Braille Activity Indicator ===
                    # Prepend Braille spinner to every log line for visual feedback
                    braille_char = self._braille_chars[self._braille_index]
                    self._braille_index = (self._braille_index + 1) % 256
                    braille_prefixed_line = f"{braille_char} {line}"

                    # Broadcast the line with Braille indicator
                    await self.websocket_manager.send_process_output(
                        pid=self.process.pid if self.process else 0,
                        command=self.process_info.command if self.process_info else "",
                        line=braille_prefixed_line,
                        stream=stream_name,
                    )

                    # TODO: Parse the line for specific events (e.g., handshake captured, attack started)
                    # For now, we just broadcast the raw line with Braille indicator.

        except Exception as e:
            logger.error(f"Error monitoring {stream_name}: {e}")
        finally:
            logger.info(f"Finished monitoring {stream_name}")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up WifiteService")
        if self.status == ToolStatus.RUNNING:
            await self.stop_tool()
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass