#!/bin/zsh
cd "$(dirname "$0")"
chmod +x launcher_mac.command
chmod +x run_mac.command
chmod +x stop_mac.command
chmod +x build_mac_dmg.command
./launcher_mac.command
