#!/bin/bash
# One-time setup of a Raspberry Pi (64-bit Raspberry Pi OS / Debian 12) as
# OpenThread Border Router + Matter controller.
#
# Installs Docker, pulls the OTBR image that matches nRF Connect SDK v3.3.4,
# installs chip-tool, and registers the otbr systemd service.
# Safe to run again.

set -euo pipefail

cd "$(dirname "$0")"

OTBR_IMAGE="openthread/border-router:latest"
CHIP_TOOL_URL="https://github.com/nrfconnect/sdk-connectedhomeip/releases/download/v3.3.0/chip-tool_arm64"

echo "== packages"
sudo apt-get update -qq
sudo apt-get install -y -qq curl ca-certificates procps

if ! command -v docker >/dev/null; then
	echo "== docker"
	curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
	sudo sh /tmp/get-docker.sh
	sudo usermod -aG docker "$USER"
fi
sudo systemctl enable --now docker

echo "== otbr image"
sudo docker pull "$OTBR_IMAGE"

echo "== chip-tool"
if ! command -v chip-tool >/dev/null; then
	curl -fsSL -o /tmp/chip-tool "$CHIP_TOOL_URL"
	sudo install -m 755 /tmp/chip-tool /usr/local/bin/chip-tool
fi
mkdir -p "$HOME/chip-tool-storage"

echo "== otbr service"
mkdir -p "$HOME/otbr/data"
install -m 755 otbr/start.sh "$HOME/otbr/start.sh"
sed "s|/home/devfive|$HOME|g" otbr/otbr.service | sudo tee /etc/systemd/system/otbr.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable otbr

# The OTBR container runs its own mDNS responder on the host network.
# The host's avahi would fight it for port 5353.
sudo systemctl disable --now avahi-daemon.socket avahi-daemon.service 2>/dev/null || true

echo
echo "Done. Plug in the RCP dongle (Thread Co-Processor firmware) and run:"
echo "  sudo systemctl start otbr && ./thread-up.sh"
