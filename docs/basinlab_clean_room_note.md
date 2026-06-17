# BasinLab Clean-Room And License Note

- SpatialClaw primary sources were reviewed directly on 2026-06-17. The repository license is a non-commercial research license, and the arXiv paper is published under `CC BY 4.0`.
- VibeThinker primary sources were reviewed directly on 2026-06-17. The repository license is `MIT`, and the arXiv paper is published under `CC0 1.0`.
- This repository does not vendor, import, or derive from SpatialClaw source code. BasinLab uses a clean-room implementation of general ideas only: persistent state, one bounded code action per step, intermediate feedback, replayable trajectories, and explicit commit governance.
- VibeThinker remains optional future adapter surface only. The current vertical slice does not download model weights, does not require external models in CI, and does not grant any model direct execution or commit authority.
