const {
  Debug,
  Game,
  HttpClient,
  on,
  printConsole,
} = require("skyrimPlatform");

const github = new HttpClient("https://raw.githubusercontent.com:443");
const COMMAND_PATH = "/everettenelle7-dot/try1/game-live/runtime/command.json";

let lastCommandId = null;
let pendingCommand = null;
let requestInFlight = false;
let lastPollAt = 0;

function execute(player, command) {
  if (!command || command.action === "noop") return;
  const args = command.args || {};

  if (command.action === "notify") {
    const text = String(args.text || "Axun says hi");
    Debug.notification(text);
    printConsole(`[AxunGitHubBridge] notify: ${text}`);
    return;
  }

  if (command.action === "turn") {
    const degrees = Number(args.degrees || 0);
    const nextZ = ((player.getAngleZ() + degrees) % 360 + 360) % 360;
    player.setAngle(player.getAngleX(), player.getAngleY(), nextZ);
    printConsole(`[AxunGitHubBridge] turn ${degrees} -> ${nextZ}`);
    return;
  }

  printConsole(`[AxunGitHubBridge] ignored unknown action: ${String(command.action)}`);
}

printConsole("[AxunGitHubBridge] online; polling GitHub mailbox");

on("update", () => {
  const player = Game.getPlayer();
  if (!player) return;

  // Run Skyrim/Papyrus calls only in the update context.
  if (pendingCommand) {
    const command = pendingCommand;
    pendingCommand = null;
    try {
      execute(player, command);
    } catch (error) {
      printConsole(`[AxunGitHubBridge] command failed: ${String(error)}`);
    }
  }

  const now = Date.now();
  if (requestInFlight || now - lastPollAt < 5000) return;

  lastPollAt = now;
  requestInFlight = true;
  const cacheBustPath = `${COMMAND_PATH}?t=${now}`;

  github.get(cacheBustPath, {}, (response) => {
    requestInFlight = false;
    if (!response || !response.body) return;

    try {
      const command = JSON.parse(response.body);
      if (command && command.id !== undefined && command.id !== lastCommandId) {
        lastCommandId = command.id;
        if (command.action !== "noop") {
          pendingCommand = command;
        }
      }
    } catch (error) {
      printConsole(`[AxunGitHubBridge] bad command JSON: ${String(error)}`);
    }
  });
});
