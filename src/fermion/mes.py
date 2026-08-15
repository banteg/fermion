"""Probe external MES tools without treating a zero exit code as compatibility."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class MESProbeError(RuntimeError):
    """Raised when an MES round-trip probe cannot run."""


@dataclass(frozen=True)
class Variant:
    name: str
    decompile_args: tuple[str, ...]


@dataclass(frozen=True)
class ProbeResult:
    variant: str
    decompile_returncode: int
    compile_returncode: int | None
    input_size: int
    output_size: int | None
    exact: bool
    diagnostic: str


VARIANTS = (
    Variant("auto", ("--auto-engine",)),
    Variant("ai5", ("-e", "AI5")),
    Variant("ai5-d0", ("-e", "AI5", "-D", "D0")),
    Variant("ai5-d0-extra", ("-e", "AI5", "-D", "D0", "-E")),
)


def probe_roundtrip(
    source: Path, juice: Path, output_dir: Path, variants: tuple[Variant, ...] = VARIANTS
) -> list[ProbeResult]:
    """Decompile and recompile a MES file under several configurations."""
    if not source.is_file():
        raise MESProbeError(f"MES input does not exist: {source}")
    resolved_juice = juice if juice.is_file() else None
    if resolved_juice is None and len(juice.parts) == 1:
        found = shutil.which(str(juice))
        resolved_juice = Path(found) if found else None
    if resolved_juice is None:
        raise MESProbeError(f"juice executable does not exist: {juice}")
    output_dir.mkdir(parents=True, exist_ok=True)
    original = source.read_bytes()
    results = []

    for variant in variants:
        rkt = output_dir / f"{source.stem}.{variant.name}.rkt"
        rebuilt = output_dir / f"{source.stem}.{variant.name}.MES"
        decompile = subprocess.run(
            [
                str(resolved_juice),
                "-d",
                "-f",
                *variant.decompile_args,
                "-o",
                str(rkt),
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        diagnostic = (decompile.stdout + decompile.stderr).strip()
        if decompile.returncode != 0 or not rkt.is_file():
            results.append(
                ProbeResult(
                    variant=variant.name,
                    decompile_returncode=decompile.returncode,
                    compile_returncode=None,
                    input_size=len(original),
                    output_size=None,
                    exact=False,
                    diagnostic=diagnostic,
                )
            )
            continue

        compile_process = subprocess.run(
            [str(resolved_juice), "-c", "-f", "-o", str(rebuilt), str(rkt)],
            capture_output=True,
            text=True,
            check=False,
        )
        compile_diagnostic = (compile_process.stdout + compile_process.stderr).strip()
        if compile_diagnostic:
            diagnostic = f"{diagnostic}\n{compile_diagnostic}".strip()
        rebuilt_data = rebuilt.read_bytes() if rebuilt.is_file() else None
        results.append(
            ProbeResult(
                variant=variant.name,
                decompile_returncode=decompile.returncode,
                compile_returncode=compile_process.returncode,
                input_size=len(original),
                output_size=len(rebuilt_data) if rebuilt_data is not None else None,
                exact=rebuilt_data == original,
                diagnostic=diagnostic,
            )
        )
    return results
