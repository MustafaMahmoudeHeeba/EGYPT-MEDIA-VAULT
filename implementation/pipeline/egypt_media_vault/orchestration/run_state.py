"""
Durable, run-scoped checkpoint store used to hand data between Airflow tasks.

Why this exists
---------------
PipelineResults holds live Python objects and several maps keyed by id(obj)
(staging_record_ids, normalized_staging_ids, duplicate_matches). Those keys are
only meaningful inside one process, so they can never be passed through XCom or
rebuilt from a different process. Each Airflow task is a separate process.

Each task therefore:

    1. rebuilds PipelineResults from the checkpoint documents of the stages
       that already finished (stage_runner.rebuild_results),
    2. calls the EXISTING stage function unchanged,
    3. writes exactly one checkpoint document describing what it produced,
       expressed only with STABLE identifiers (list positions, staging_record_id,
       article_id, story_id, cluster_id), never id(obj).

Layout   <base_dir>/<run_id>/<stage>.json.gz

Rules
-----
* One writer per stage document. Parallel branches (bronze / dwh / silver) write
  different files, so they can never overwrite each other.
* Writes are atomic (temp file + fsync + os.replace); a crashed task can never
  leave a half-written document behind.
* A stage that (re-)starts first deletes its own document and the documents of
  every stage that depends on it, so a retry or a manual "clear" can never mix
  old and new data.
* Only small values go through XCom. Article payloads live here.

The base directory defaults to /opt/airflow/run_state and can be changed with
the EMV_RUN_STATE_DIR environment variable. With LocalExecutor every task runs
inside the same Airflow container, so a Docker volume mounted at that path makes
checkpoints survive container restarts (see README).
"""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1

DEFAULT_BASE_DIR = "/opt/airflow/run_state"
BASE_DIR_ENV_VAR = "EMV_RUN_STATE_DIR"

# Stage names (checkpoint documents).
SCRAPE = "scrape"
STAGE_RAW = "stage_raw"
PROCESS = "process"          # validation + normalization
DEDUP = "dedup"
CLUSTER = "cluster"
STORY_IDS = "story_ids"
BRONZE = "bronze"
DWH = "dwh"
SILVER = "silver"
INTEGRITY = "integrity"

# Direct dependencies: a stage's document is only valid for the exact upstream
# documents it was produced from.
DEPENDS_ON: dict[str, tuple[str, ...]] = {
    SCRAPE: (),
    STAGE_RAW: (SCRAPE,),
    PROCESS: (STAGE_RAW,),
    DEDUP: (PROCESS,),
    CLUSTER: (DEDUP,),
    STORY_IDS: (CLUSTER,),
    BRONZE: (SCRAPE,),
    DWH: (STORY_IDS,),
    SILVER: (STORY_IDS,),
    INTEGRITY: (DWH, SILVER, BRONZE),
}

MANIFEST = "manifest"

_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class RunStateError(RuntimeError):
    """The checkpoint store is missing, unreadable or inconsistent."""


class MissingStageError(RunStateError):
    """A required upstream checkpoint document does not exist."""


# ---------------------------------------------------------------------
# JSON codec (lossless for timezone-aware AND naive datetimes)
# ---------------------------------------------------------------------


def _encode_default(value):
    if isinstance(value, datetime):
        return {"$dt": value.isoformat()}

    raise TypeError(
        f"Value of type {type(value).__name__} is not checkpoint-serializable."
    )


def _decode_hook(value: dict):
    if len(value) == 1 and "$dt" in value:
        return datetime.fromisoformat(value["$dt"])

    return value


def dumps(document) -> bytes:
    return json.dumps(
        document,
        default=_encode_default,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def loads(payload: bytes):
    return json.loads(payload.decode("utf-8"), object_hook=_decode_hook)


def downstream_of(stage: str) -> list[str]:
    """Every stage that (transitively) depends on ``stage``."""

    if stage not in DEPENDS_ON:
        raise KeyError(f"Unknown stage: {stage!r}")

    found: list[str] = []
    changed = True

    while changed:
        changed = False

        for candidate, dependencies in DEPENDS_ON.items():
            if candidate in found or candidate == stage:
                continue

            if stage in dependencies or any(d in found for d in dependencies):
                found.append(candidate)
                changed = True

    return found


# ---------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------


class RunState:
    """Checkpoint documents of one pipeline run."""

    def __init__(self, run_id: str, base_dir: str | os.PathLike | None = None):
        if not isinstance(run_id, str) or not _RUN_ID_SAFE.match(run_id):
            raise ValueError(f"Unsafe or empty run_id: {run_id!r}")

        self.run_id = run_id
        self.base_dir = Path(
            base_dir
            or os.environ.get(BASE_DIR_ENV_VAR)
            or DEFAULT_BASE_DIR
        )
        self.directory = self.base_dir / run_id

    # -- paths -----------------------------------------------------------

    def _path(self, stage: str) -> Path:
        return self.directory / f"{stage}.json.gz"

    def ensure(self) -> Path:
        try:
            self.directory.mkdir(parents=True, exist_ok=True)

            probe = self.directory / ".write-test"
            probe.write_bytes(b"ok")
            probe.unlink()

        except OSError as exc:
            raise RunStateError(
                f"Run state directory {self.directory} is not writable: "
                f"{exc}. Set {BASE_DIR_ENV_VAR} or mount a volume there."
            ) from exc

        return self.directory

    # -- documents -------------------------------------------------------

    def has(self, stage: str) -> bool:
        return self._path(stage).is_file()

    def save(self, stage: str, document: dict) -> Path:
        """Atomically write the checkpoint document of one stage."""

        if stage not in DEPENDS_ON and stage != MANIFEST:
            raise KeyError(f"Unknown stage: {stage!r}")

        self.ensure()

        envelope = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "stage": stage,
            "saved_at": datetime.now().astimezone(),
            "data": document,
        }

        path = self._path(stage)
        temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")

        try:
            with open(temporary, "wb") as handle:
                with gzip.GzipFile(
                    fileobj=handle,
                    mode="wb",
                    compresslevel=5,
                    mtime=0,
                ) as compressed:
                    compressed.write(dumps(envelope))

                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temporary, path)

        finally:
            if temporary.exists():
                temporary.unlink()

        return path

    def load(self, stage: str, required: bool = False) -> dict | None:
        path = self._path(stage)

        if not path.is_file():
            if required:
                raise MissingStageError(
                    f"Checkpoint '{stage}' of run {self.run_id} does not "
                    "exist. Clear the task that produces it (and everything "
                    "downstream) and run it again."
                )

            return None

        try:
            with gzip.open(path, "rb") as handle:
                envelope = loads(handle.read())

        except (OSError, ValueError) as exc:
            raise RunStateError(
                f"Checkpoint '{stage}' of run {self.run_id} is unreadable: "
                f"{exc}"
            ) from exc

        if envelope.get("run_id") != self.run_id:
            raise RunStateError(
                f"Checkpoint '{stage}' belongs to run "
                f"{envelope.get('run_id')!r}, not {self.run_id!r}."
            )

        if envelope.get("schema_version") != SCHEMA_VERSION:
            raise RunStateError(
                f"Checkpoint '{stage}' has schema version "
                f"{envelope.get('schema_version')!r}; expected "
                f"{SCHEMA_VERSION}."
            )

        return envelope["data"]

    def require(self, *stages: str) -> None:
        for stage in stages:
            self.load(stage, required=True)

    # -- invalidation ----------------------------------------------------

    def begin_stage(self, stage: str) -> list[str]:
        """
        Called when a stage (re-)starts: drop its own document and every
        document that depends on it. Returns the removed stage names.
        """

        removed = []

        for name in [stage, *downstream_of(stage)]:
            path = self._path(name)

            if path.is_file():
                path.unlink()
                removed.append(name)

        return removed

    # -- housekeeping ----------------------------------------------------

    def purge_old_runs(self, retention_days: float) -> list[str]:
        """Delete workspaces of other runs older than the retention period."""

        if retention_days is None or retention_days <= 0:
            return []

        if not self.base_dir.is_dir():
            return []

        cutoff = time.time() - retention_days * 86400
        removed = []

        for child in self.base_dir.iterdir():
            if (
                child.is_dir()
                and child.name != self.run_id
                and _RUN_ID_SAFE.match(child.name)
                and child.stat().st_mtime < cutoff
            ):
                shutil.rmtree(child, ignore_errors=True)
                removed.append(child.name)

        return removed
