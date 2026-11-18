#!/usr/bin/env python3
"""Offline UAT gate model. This module has no live execution adapter.

The simulated backend and its inputs are test data, not authorization evidence.
The command-line interface cannot authenticate dispatch or instruction chronology.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class State(str, Enum):
    BLOCKED = 'BLOCKED'
    SIMULATED_PASS = 'SIMULATED_PASS'
    SIMULATED_FAIL = 'SIMULATED_FAIL'


@dataclass(frozen=True)
class Report:
    state: State
    stage: str
    reason: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Fixture:
    """Untrusted synthetic data; deliberately incapable of live authorization."""
    candidate: str
    current_candidate: str
    clean: bool
    spec_hash: str
    evidence_refs: tuple[str, ...]
    newer_stop: bool
    wrapper: str
    expected_wrapper: str
    accepted_cases: tuple[str, ...]
    mapped_cases: tuple[str, ...]
    runtime: tuple[str, str, str, str, str]
    expected_runtime: tuple[str, str, str, str, str]
    ledger_count: int
    ledger_limit: int
    ledger_locked: bool
    reset_requested: bool
    owned: bool
    occupied: bool
    snapshot: bool


# Explicit, limited config sources. Values stay internal; never print them.
def resolve_config(sources: Mapping[str, Mapping[str, str]], keys: tuple[str, ...]) -> dict[str, str]:
    """Resolve first present key: instruction, accepted, profile, then default.

    This only selects values; it does not verify their origin or authorize anything.
    """
    result = {}
    for key in keys:
        for source in ('instruction', 'accepted', 'profile', 'default'):
            if key in sources.get(source, {}):
                result[key] = sources[source][key]
                break
    return result


def _digest(value: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-f]{64}', value))


def simulate(fixture: Fixture, backend: 'FakeBackend') -> Report:
    """Run a model against exactly the built-in fake, never a live adapter.

    Checks and events illustrate required ordering, not real-world verification.
    References are not returned: fixture strings are untrusted and may be secret.
    """
    if type(backend) is not FakeBackend:
        return Report(State.BLOCKED, 'adapter', 'only the built-in fake is permitted')
    f = fixture
    def blocked(stage: str, reason: str) -> Report:
        return Report(State.BLOCKED, stage, reason)
    if not _digest(f.candidate) or not _digest(f.spec_hash) or not f.evidence_refs:
        return blocked('candidate/spec', 'missing or invalid candidate, spec hash, or evidence')
    if not f.clean or f.candidate != f.current_candidate:
        return blocked('candidate/spec', 'dirty or changed candidate')
    if f.newer_stop:
        return blocked('policy', 'newer stop')
    if not f.wrapper or f.wrapper != f.expected_wrapper:
        return blocked('policy', 'wrapper mismatch')
    if not f.accepted_cases or len(set(f.accepted_cases)) != len(f.accepted_cases) or set(f.accepted_cases) != set(f.mapped_cases) or len(f.accepted_cases) != len(f.mapped_cases):
        return blocked('cases', 'missing or mismatched accepted cases')
    if f.runtime != f.expected_runtime or f.runtime != ('synthetic', 'denied', 'disabled', 'disposable', 'exact-run-owned-only'):
        return blocked('runtime', 'unsafe or changed runtime')
    if type(f.ledger_count) is not int or type(f.ledger_limit) is not int or f.ledger_count < 0 or f.ledger_limit <= 0 or f.ledger_count >= f.ledger_limit or not f.ledger_locked or f.reset_requested:
        return blocked('ledger', 'unavailable, exhausted, unlocked, or reset requested')
    if not f.owned or f.occupied:
        return blocked('resources', 'ownership or occupancy not established')
    if not f.snapshot:
        return blocked('snapshot', 'snapshot missing')
    try:
        count, success = backend.launch()
    except Exception:
        try:
            backend.cleanup()
        except Exception:
            return Report(State.SIMULATED_FAIL, 'cleanup', 'simulated launch and cleanup failed')
        return Report(State.SIMULATED_FAIL, 'launch', 'simulated launch failed')
    try:
        cleaned = backend.cleanup()
    except Exception:
        cleaned = False
    if not cleaned:
        return Report(State.SIMULATED_FAIL, 'cleanup', 'simulated cleanup failed')
    if type(count) is not int or count <= 0 or not success:
        return Report(State.SIMULATED_FAIL, 'results', 'zero tests or simulated test failure')
    return Report(State.SIMULATED_PASS, 'complete', 'fake-only simulation; no UAT executed')


class FakeBackend:
    """An inert in-memory test double. Never accepts callables or external objects."""
    def __init__(self, count: int = 1, success: bool = True, cleanup_ok: bool = True):
        self.count = count
        self.success = success
        self.cleanup_ok = cleanup_ok
        self.events: list[str] = []

    def launch(self) -> tuple[int, bool]:
        self.events.append('launch')
        return self.count, self.success

    def cleanup(self) -> bool:
        self.events.append('cleanup')
        return self.cleanup_ok


def main() -> int:
    parser = argparse.ArgumentParser(description='Fail-closed UAT controller entry; no live dispatcher is integrated.')
    parser.add_argument('task', nargs='?', help='task identifier (not authenticated)')
    parser.parse_args()
    print(json.dumps({'state': 'BLOCKED', 'stage': 'authorization', 'reason': 'No authenticated dispatcher or live execution adapter; real UAT NOT RUN.'}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
