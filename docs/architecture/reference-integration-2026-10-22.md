# Reference integration — 22 October 2026

## Adopted

The local educational reference inspired separating file scoring from collection/state and putting thresholds in a JSON rule file. BehEDR already has modular collectors and YAML rules; replacing those with the reference's simpler system would lose functionality.

- New `backend/server/core/file_behavior.py`: pure scoring and strict configuration validation.
- New `rules/file_behavior.json`: file behavior window, evidence counts, thresholds and scores.
- Active detector calls the scorer and validates its configuration at startup.
- Distinct paths prevent repeated observations of one file from becoming a bulk-file signal.
- A README/note-like filename alone adds no score. It contributes only with bulk modifications or multiple suspicious-extension paths, and matching uses the basename rather than parent directories.
- File scores are bounded at 100 and wording describes evidence rather than declaring a ransom note confirmed.
- Tests cover benign look-alikes, preserved suspicious signals, malformed configuration, window/process filtering and ingestion integration.

## Removed or replaced

The old inline L7 scoring implementation, filename-only ransom-note rule and repeated hardcoded file thresholds were replaced. The misleading detector header claiming automatic response was corrected. No archived or downloaded reference files were deleted.

## Not adopted

The reference's global-history score accumulation, unreachable ML training condition, fixed-RSS injection claim, name-only Windows process scoring, unauthenticated dashboard and fragile relative storage paths were not integrated. No packet-capture or ML dependency was added.

## Remaining limits

This change is not a new malware-accuracy benchmark. File events can still have unknown writers, and the existing collection/window infrastructure still uses server processing time. Legitimate builds/backups can exceed volume thresholds. Network timing, authentication/session lifecycle, restart recovery and other earlier findings remain separate open work. Advanced ML and automatic containment remain disabled.

## Verification

On 22 October 2026, the complete regression suite passed: **78 tests in 45.53 seconds**. After improving isolation of the ingestion test's in-memory file state, all **15 focused file-behavior tests passed in 6.13 seconds**. Ruff checks passed for backend, endpoint, manage.py and tests. The initial sandbox run failed on Windows temporary-directory permissions; the approved retry completed successfully. The existing Dockerfile copies both backend and rules, including the new files; a container build was not run.

These are inert regression tests, not live-malware experiments or evidence of a measured detection rate.

## Attribution

Design reference: Atharva Vidhate, [behavior-based-malware-detection-engine](https://github.com/atharvavidhate12-oss/behavior-based-malware-detection-engine), local copy under `gthb/behavior-based-malware-detection-engine-main/behavior-based-malware-detection-engine-main`, carrying an MIT license and copyright (c) 2025 Atharva Vidhate. Its supplied LICENSE remains with the reference. No source implementation was copied into the active project; the scorer is original BehEDR code informed by the reviewed separation of concerns.
