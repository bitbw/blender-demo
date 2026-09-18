# Codex + Blender MCP local setup

## Installed and verified

- Blender: `5.1.0` (meets Blender Lab MCP's `5.1+` requirement)
- Codex CLI: `0.154.0`
- uv / uvx: `0.7.13`
- Official Blender Lab MCP extension: `mcp 1.0.3`, installed and enabled
- Official MCP Python service: `.tools/blender-mcp/bundle/.venv`
- Codex MCP server: globally registered as `blender`

## Local files

- Official extension: `.tools/blender-mcp/mcp-1.0.3.zip`
- Official MCP bundle: `.tools/blender-mcp/blender-1.0.3.mcpb`
- Extracted official service: `.tools/blender-mcp/bundle`

Codex runs the server with this equivalent configuration:

```toml
[mcp_servers.blender]
command = "C:\\Users\\18211132604_64538\\.local\\bin\\uv.exe"
args = ["--directory", "D:\\bowen\\demo\\blender-demo\\.tools\\blender-mcp\\bundle", "run", "blender-mcp"]
```

## One Blender restart remains

Blender was already running before the extension was installed. Save and fully restart Blender once so the MCP extension loads. It should automatically start its local bridge at `127.0.0.1:9876`.

If it does not start: open `Edit > Preferences > Extensions`, search for `MCP`, confirm it is enabled, then set Host to `localhost` and Port to `9876` and start the service.

Restart Codex, then run this non-mutating verification prompt:

```text
Use Blender MCP. Read the current scene only, then list every object name, type, and the total count. Do not modify or save anything.
```

## Reference-image modeling workflow

1. Put references in `references/`. A single image cannot determine unseen geometry; use front, side, back, and 45-degree views when possible.
2. Confirm a greybox and proportions first; detail bevels, UVs, and materials second.
3. Require front, side, and 45-degree preview renders for each correction pass; stop after three passes.
4. Export `.blend` and `.glb` only after approval.

Recommended prompt:

```text
Use Blender MCP to create an editable low-poly chair from references/chair-front.png.
First state which details a single image cannot determine, then create only the main silhouette and proportions.
Put new objects in an AI_Model collection and do not delete existing objects.
Render front, side, and 45-degree previews; compare against the reference and self-correct for at most three passes.
After approval, save output/chair.blend and export output/chair.glb.
```

## Safety boundary

MCP executes model-generated Blender Python. Work from a copy of each `.blend`, save first, and keep the bridge on `localhost`; do not expose port `9876` to a LAN or the internet.
