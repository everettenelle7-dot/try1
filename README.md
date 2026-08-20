# try1 — Game Bridge Lab

A small, inspectable bridge for letting an AI assistant interact with a locally running game through an explicit action allowlist.

## Skyrim: fastest path first

The first target is Skyrim Special Edition / Anniversary Edition using **Skyrim Platform**. Two transports are included.

### 1. GitHub mailbox mode — no Codex/local agent required

This is the quickest way to prove that the assistant can touch the game from chat.

1. Install Skyrim Platform for your Skyrim version.
2. Copy `skyrim/axun-github-bridge.js` into:
   `Skyrim Special Edition/Data/Platform/Plugins/axun-github-bridge.js`
3. Start Skyrim and load a save.
4. Open the `~` console. You should see:
   `[AxunGitHubBridge] online; polling GitHub mailbox`
5. Tell Axun that the game is ready. The assistant can update `game-live/runtime/command.json` through the connected GitHub account.

Current live actions:

- `notify` — show a Skyrim notification.
- `turn` — rotate the player by a requested number of degrees.

The plugin checks the public GitHub mailbox about every five seconds and ignores command IDs it has already seen.

**Kill switch:** remove/rename `axun-github-bridge.js`, or simply stop using the `game-live` mailbox.

### 2. Local bridge mode — faster and designed for two-way state later

Run the local server:

```powershell
python bridge/server.py
```

Copy `skyrim/axun-bridge.js` into Skyrim Platform's `Data/Platform/Plugins` directory and load a save.

Useful test commands:

```powershell
python bridge/cli.py status
python bridge/cli.py notify "Axun bridge online"
python bridge/cli.py turn 15
```

The local server binds only to `127.0.0.1:8765`. `Ctrl+C` stops it immediately.

## What is already working

- Local HTTP command queue and state endpoint.
- Mock Skyrim adapter used for end-to-end testing.
- Skyrim Platform adapter that reports player position/angles and consumes commands.
- GitHub mailbox adapter for one-way chat → GitHub → Skyrim control without Codex.
- Explicit action allowlist (`notify`, `turn`) rather than arbitrary console execution.

## Next steps

1. Prove the GitHub mailbox path inside a real Skyrim session.
2. Add nearby/crosshair state and safer interaction actions.
3. Add a proper two-way remote transport so the assistant can see game state without a local coding agent.
4. Reuse the bridge protocol for other games such as The Sims and Disco Elysium.
