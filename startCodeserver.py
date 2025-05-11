#!/usr/bin/env python3
import time
import subprocess
import docker
import secrets
import string
import csv
from docker.errors import APIError, ContainerError, ImageNotFound

# ----------------------------------------
# Get public IP (fallback to localhost)
# ----------------------------------------
try:
    public_ip = subprocess.check_output(
        ["curl", "--silent", "ifconfig.me"], text=True, timeout=10
    ).strip()
except Exception as e:
    print(f"Warning: could not fetch public IP ({e}), defaulting to localhost")
    public_ip = "127.0.0.1"

# ----------------------------------------
# Generate strong random password
# ----------------------------------------
def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    safe_alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '')
    return ''.join(secrets.choice(safe_alphabet) for _ in range(length))

# ----------------------------------------
# Save details to CSV
# ----------------------------------------
def save_container_info_to_csv(records, filename="code_server_containers.csv"):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Container Name", "Password", "Access URL"])
        writer.writerows(records)
    print(f"\n📁 Container info saved to {filename}")

# ----------------------------------------
# Main container launch logic
# ----------------------------------------
def launch_code_server_containers():
    client = docker.from_env()
    render_ids     = [128, 136, 144, 152, 160, 168, 176, 184]
    base_port      = 8080
    image          = "code-server"  # Local image name
    volume_mounts  = {"/home/shepande/models": {"bind": "/models", "mode": "rw"}}
    container_records = []

    for idx, rid in enumerate(render_ids):
        name       = f"codeserver_dev_{rid}"
        bind_port  = base_port + idx*100
        password   = generate_strong_password()

        devices = [
            {"PathOnHost": "/dev/kfd", "PathInContainer": "/dev/kfd", "CgroupPermissions": "rwm"},
            {"PathOnHost": f"/dev/dri/renderD{rid}", "PathInContainer": f"/dev/dri/renderD{rid}", "CgroupPermissions": "rwm"}
        ]

        try:
            print(f"[{name}] launching container...")
            container = client.containers.run(
                image=image,
                name=name,
                detach=True,
                tty=True,
                devices=devices,
                volumes=volume_mounts,
                environment={"PASSWORD": password},
                group_add=["video"],
                security_opt=["seccomp=unconfined"],
                ipc_mode="host",
                network_mode="host",
                cap_add=["SYS_PTRACE"],
                working_dir="/workspace"
            )

            print(f"[{name}] installing code-server if not already present...")
            container.exec_run("bash -c 'which code-server || curl -fsSL https://code-server.dev/install.sh | sh'", workdir="/workspace")

            print(f"[{name}] starting code-server on port {bind_port}...")
            start_cmd = (
                f"nohup code-server --bind-addr 0.0.0.0:{bind_port} "
                f"--auth password > /workspace/code-server-{bind_port}.log 2>&1 &"
            )
            container.exec_run(["bash", "-c", start_cmd], detach=True, workdir="/workspace")

            url = f"http://{public_ip}:{bind_port}"
            print(f"[{name}] Access URL: {url}")
            print(f"[{name}] Password: {password}\n")
            container_records.append([name, password, url])

        except ImageNotFound:
            print(f"ERROR: local image '{image}' not found.")
        except ContainerError as e:
            print(f"ERROR: container '{name}' failed:\n{e.stderr.decode()}")
        except APIError as e:
            print(f"ERROR: Docker API error for '{name}':\n{e.explanation}")

    print("✅ All code-server containers launched:")
    for rec in container_records:
        print(f"  {rec[0]} → {rec[2]} (pass: {rec[1]})")

    save_container_info_to_csv(container_records)

# ----------------------------------------
if __name__ == "__main__":
    launch_code_server_containers()