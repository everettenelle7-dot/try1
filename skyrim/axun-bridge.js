const {
  Debug,
  Game,
  HttpClient,
  on,
  printConsole,
} = require("skyrimPlatform");

const BRIDGE = "http://127.0.0.1:8765";
const http = new HttpClient(BRIDGE);

let pendingCommand = null;
let pollInFlight = false;
let stateInFlight = false;
let lastPollAt = 0;
let lastStateAt = 0;

function postJson(path, payload, done) {
  http.post(
    path,
    {
      body: JSON.stringify(payload),
      contentType: "application/json",
    },
    (response) => {
      if (done) done(response);
    }
  );
}

function ack(command, result) {
  postJson("/event", {
    type: "command_executed",
    command_id: command.id,
    action: command.action,
    result,
  });
}

function executeCommand(player, command) {
  const args = command.args || {};

  if (command.action === "notify") {
    const text = String(args.text || "Axun bridge online");
    Debug.notification(text);
    printConsole(`[AxunBridge] notify: ${text}`);
    ack(command, { ok: true });
    return;
  }

  if (command.action === "turn") {
    const degrees = Number(args.degrees || 0);
    const nextZ = ((player.getAngleZ() + degrees) % 360 + 360) % 360;
    player.setAngle(player.getAngleX(), player.getAngleY(), nextZ);
    printConsole(`[AxunBridge] turn ${degrees} -> ${nextZ}`);
    ack(command, { ok: true, angle_z: nextZ });
    return;
  }

  ack(command, { ok: false, error: "unsupported_action" });
}

printConsole("[AxunBridge] plugin loaded; waiting for bridge on 127.0.0.1:8765");

on("update", () => {
  const player = Game.getPlayer();
  if (!player) return;

  // HTTP callbacks may happen outside the game-function context. We only
  // stash data in callbacks and execute Skyrim calls here on update.
  if (pendingCommand) {
    const command = pendingCommand;
    pendingCommand = null;
    try {
      executeCommand(player, command);
    } catch (error) {
      printConsole(`[AxunBridge] command failed: ${String(error)}`);
      ack(command, { ok: false, error: String(error) });
    }
  }

  const now = Date.now();

  if (!stateInFlight && now - lastStateAt >= 1000) {
    lastStateAt = now;
    stateInFlight = true;

    const state = {
      game: "skyrim-se-ae",
      player: {
        x: player.getPositionX(),
        y: player.getPositionY(),
        z: player.getPositionZ(),
        angle_x: player.getAngleX(),
        angle_y: player.getAngleY(),
        angle_z: player.getAngleZ(),
      },
    };

    postJson("/state", state, () => {
      stateInFlight = false;
    });
  }

  if (!pollInFlight && now - lastPollAt >= 400) {
    lastPollAt = now;
    pollInFlight = true;

    http.get("/commands/next", {}, (response) => {
      pollInFlight = false;
      if (!response || !response.body) return;
      try {
        const packet = JSON.parse(response.body);
        if (packet && packet.command && !pendingCommand) {
          pendingCommand = packet.command;
        }
      } catch (error) {
        printConsole(`[AxunBridge] bad bridge response: ${String(error)}`);
      }
    });
  }
});
