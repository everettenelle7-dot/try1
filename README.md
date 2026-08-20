# try1 — Game Bridge Lab

This repository is the starting point for a local game-control bridge project.

## Goal

Build a small, inspectable bridge between an AI assistant and a locally running game, with the game side exposing only explicit, safe actions.

## First design

- **Game adapter**: reads game state and executes a limited action set.
- **Local bridge**: translates structured commands into game-adapter calls.
- **Tool interface**: exposes those commands to an AI/tool client.
- **Logs + kill switch**: every action is visible, reversible where possible, and easy to stop.

## Status

Repository initialized. Next step: choose the exact Skyrim runtime/mod interface and scaffold the local bridge.
