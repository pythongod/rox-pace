# Rox Pace: HYROX pacing skill

The **hyrox-pacing** agent skill brings the split model and race-result percentiles behind [rox-pace.com](https://rox-pace.com) to AI assistants that support Agent Skills, such as Claude Code and OpenClaw.

- **Goal splits.** Ask for a 1:25:00 plan and get all 8 runs and 8 stations, including the Roxzone.
- **Rankings.** Ask whether a finish or station time is good for your division: Open, Pro, Elite, Doubles or Relay.
- **Targets.** Ask what splits a top-25 % finish needs.
- **No account or API key.** The skill runs locally with Python's standard library and the data in `skills/hyrox-pacing/references/benchmarks.json`.

## Install

Claude Code:

```
/plugin install hyrox-pacing --marketplace pythongod/rox-pace
```

Other agents: copy `skills/hyrox-pacing` into your agent's skills folder.

## Use it directly

```bash
python3 skills/hyrox-pacing/scripts/hyrox_pace.py plan 1:25:00
python3 skills/hyrox-pacing/scripts/hyrox_pace.py percentile 1:25:00 --division women
python3 skills/hyrox-pacing/scripts/hyrox_pace.py station wall-balls 6:30 --division men
python3 skills/hyrox-pacing/scripts/hyrox_pace.py target 25 --division doublesMen
python3 skills/hyrox-pacing/scripts/hyrox_pace.py divisions
```

## Data

The percentiles come from public HYROX results and are aggregated only, with no individual athletes. rox-pace.com refreshes them every week. The **Sync benchmarks** workflow then pulls them from `https://rox-pace.com/data/skill-benchmarks.json` and commits any change with a new patch version.

Not affiliated with or endorsed by HYROX. HYROX is a trademark of its owner.

## License

MIT
