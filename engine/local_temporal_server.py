"""Local Temporal Server Runner.

Starts an official local Temporal Server with:
- gRPC Port: 127.0.0.1:7233
- Web UI: http://localhost:8233
No Docker required. Uses Temporal's official dev server embedded in the Python SDK.
"""
import asyncio
import signal
import sys
from temporalio.testing import WorkflowEnvironment


async def start_server():
    print("=" * 60)
    print("[*] Launching Local Temporal Dev Server...")
    print("=" * 60)

    try:
        env = await WorkflowEnvironment.start_local(
            ip="127.0.0.1",
            port=7233,
            ui=True,
            ui_port=8233,
            dev_server_log_level="warn"
        )
    except Exception as e:
        print(f"[!] Could not bind to 7233/8233, falling back to auto-allocated ports: {e}")
        env = await WorkflowEnvironment.start_local(ui=True, dev_server_log_level="warn")

    print("\n" + "=" * 60)
    print("[+] Temporal Server is LIVE and READY!")
    print(f"    - gRPC Server: {env.client.service_client.config.target_host}")
    print("    - Web UI:      http://localhost:8233")
    print("=" * 60)
    print("Keep this terminal open while running the backend & frontend.\n")

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass  # Windows event loop doesn't always support add_signal_handler

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        print("\n[*] Shutting down Temporal server...")
        await env.shutdown()
        print("[+] Temporal server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n[+] Exited.")
