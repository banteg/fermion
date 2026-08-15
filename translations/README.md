# Translation catalog

`fermion.toml` is the checked-in source of truth for Fermion's translated text
and the reasoning behind it. It intentionally contains text and metadata, not
compiled MES files or original game media.

Each `[[files]]` table identifies one pristine MES file by basename and
SHA-256. Each `[[entries]]` table records:

- a stable, descriptive `id`;
- the pristine file, text-opcode offset, and source mode;
- the exact original Japanese and current English translation;
- the target encoding mode and optional dialogue-box width;
- a progress `status` and free-form translator `notes`.

Offsets always refer to the pristine file named by the enclosing catalog, not a
rebuilt or relocated MES. Notes should retain useful alternatives, speaker and
scene context, tone decisions, technical compromises, and anything worth
revisiting. Do not erase an unresolved nuance merely because the current probe
uses shorter wording.

The current statuses are:

- `draft`: recorded but not yet exercised in the game;
- `runtime-proof`: renderer or control-flow proof whose wording is still
  provisional;
- `runtime-verified`: the current wording and layout have been exercised in the
  game. This is not necessarily final editorial approval.

Validate structure and encodability after every edit:

```sh
uv run fermion translation check translations/fermion.toml
```

When the pristine extraction is available, also verify every file hash and
every source offset, mode, and Japanese string:

```sh
uv run fermion translation check translations/fermion.toml \
  --source-dir working/archives/disk-a \
  --verbose
```

For an incremental batch:

1. Add or revise catalog entries while preserving stable IDs.
2. Record translation alternatives and uncertainties in `notes`.
3. Validate against the pristine sources.
4. Build only into ignored `working/` paths.
5. Add or update a named route in `runtime/routes.toml` when the text is
   reachable automatically, then promote its status after the runtime check.
