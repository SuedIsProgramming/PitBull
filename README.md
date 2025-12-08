# PitBull

PitBull is a Python-based autonomous PvP bot for Hypixel’s The Pit gamemode (Minecraft).
It uses the Minescript mod to read real-time game data (player positions, health, gear, etc.) and control the client via Python. The goal of the project is to showcase an implementation that targets and fights weaker players in real time to maximize survival time — this repository is a personal storage, not intended for public reuse.

The term _pitbull_ is a play on words of the game mode (**pit**) and the, arguable, "menacing" dog breed **pitbull**.

## Features

**Real-time gear evaluation** — inspects nearby players' equipment and computes a simple strength score.

**Autonomous targeting** — prioritizes weaker players (lower gear/health) to increase survival chances.

**Automated movement & combat** — strafing, aiming and attack timing implemented with Minescript commands.

**Status feedback** — prints status updates (current target, health, kills) to in-game chat/console.

**Lightweight** — written in plain Python and uses only the Minescript API and standard Python libraries.

## Technologies Used

* Python 3

* Minescript (Minecraft mod that exposes a Python API to the client)

* Standard Python libraries (no additional pip packages required)

## Usage (high-level)

Once started, PitBull will scan for nearby players, evaluate their gear/health, select a target, and attempt to engage with movement and attack logic implemented via Minescript calls. Pitbull will also detect the player's own health and consume appropriate items to maintain their health.

The script outputs status updates to a logging file for monitoring (target name, health, kills, gold, xp, etc.)

The code is intended to showcase techniques for reading game state via Minescript and implementing simple autonomous behavior in Python.

If you are reviewing the repository to learn, focus on the structure, the way Minescript APIs are used to obtain game state, and how decision logic for targeting and movement is implemented.
