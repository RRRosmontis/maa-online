# Third-party notices

This repository contains modified files derived from third-party projects and installs additional components at runtime.

## Modified and vendored source

### NetEase Cloud Game API Server for MAA

- Upstream: https://github.com/Tokisaki-Galaxy/netease_cloud_game_server
- Base revision used during development: `5fabe39055e7d918830773fa38c53af27494b449`
- License: Apache License 2.0
- Local copy: `backend/`
- Changes include Linux/headless login bootstrap, connection readiness handling, PNG screenshots, validation, timeout/error handling, real frame dimensions and lifecycle fixes.
- Original license is preserved in `backend/LICENSE`.

### NetEase Cloud Game SDK

- Upstream: https://github.com/Tokisaki-Galaxy/netease_cloud_game_sdk
- SDK revision used during development: `3829b4933fafded6ec8c275ae352f4e9774a699b`
- Original project: https://github.com/wupco/netease_cloud_game_sdk
- License: Apache License 2.0
- Local copy: `backend/sdk/wsconnect.py`
- Changes include non-blocking HTTP calls, request timeouts, safe token handling, resolution/codec propagation, corrected exit URL and structured protocol errors.
- Original license is preserved in `backend/sdk/LICENSE`.

## Runtime dependencies (not vendored)

The installation process downloads these components from their official upstreams. Their own licenses apply:

- MAA: https://github.com/MaaAssistantArknights/MaaAssistantArknights — AGPL-3.0-only and project terms
- maa-cli: https://github.com/MaaAssistantArknights/maa-cli — see upstream license
- MaaResource: https://github.com/MaaAssistantArknights/MaaResource — see upstream license and game-asset notices
- aiohttp: https://github.com/aio-libs/aiohttp
- aiortc: https://github.com/aiortc/aiortc
- PyAV: https://github.com/PyAV-Org/PyAV
- NumPy: https://github.com/numpy/numpy
- Pillow: https://github.com/python-pillow/Pillow
- Requests: https://github.com/psf/requests
- websockets: https://github.com/python-websockets/websockets

This project is not affiliated with or endorsed by NetEase, Hypergryph, Studio Montagne, MAA Team, or the maintainers of the upstream prototypes. Product names and trademarks belong to their respective owners.
