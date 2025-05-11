#!/usr/bin/env python3
import docker
from docker.errors import NotFound, APIError

# Prefix used in your launch script
CONTAINER_PREFIX = "codeserver_dev_"
RENDER_IDS = [128, 136, 144, 152, 160, 168, 176, 184]  # Adjust to match what you launch

def cleanup_code_server_containers():
    client = docker.from_env()

    for rid in RENDER_IDS:
        name = f"{CONTAINER_PREFIX}{rid}"
        try:
            container = client.containers.get(name)
            print(f"🛑 Stopping container: {name}")
            container.stop(timeout=5)

            print(f"🗑️ Removing container: {name}")
            container.remove()
        except NotFound:
            print(f"⚠️  Container {name} not found, skipping.")
        except APIError as e:
            print(f"❌ Docker API error for '{name}':\n{e.explanation}")

    print("✅ Cleanup complete.")

if __name__ == "__main__":
    cleanup_code_server_containers()