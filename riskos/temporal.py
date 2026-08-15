"""Temporal sequence features for account-takeover and monetization behavior."""

from dataclasses import dataclass

from riskos.simulator import SyntheticCase


@dataclass(frozen=True)
class Event:
    minute: int
    name: str


def events_for_case(case: SyntheticCase) -> list[Event]:
    """Derive an observable event sequence from synthetic feature state."""
    f = case.features
    events = [Event(0, "session_start")]
    minute = 2
    if f.new_device:
        events.append(Event(minute, "new_device"))
        minute += 3
    if f.bank_change_24h:
        events.append(Event(minute, "bank_change"))
        minute += 4
    if f.velocity_ratio >= 2.5:
        events.append(Event(minute, "velocity_spike"))
        minute += 4
    if f.suspicious_sequence:
        events.extend(
            [
                Event(minute, "counterparty_spike"),
                Event(minute + 3, "high_value_action"),
            ]
        )
    return events


def _contains_ordered(events: list[Event], pattern: tuple[str, ...], max_window: int = 20) -> bool:
    names = [event.name for event in events]
    positions: list[int] = []
    start = 0
    for target in pattern:
        try:
            pos = names.index(target, start)
        except ValueError:
            return False
        positions.append(pos)
        start = pos + 1
    if not positions:
        return False
    return events[positions[-1]].minute - events[positions[0]].minute <= max_window


def temporal_risk(case: SyntheticCase) -> float:
    """Score suspicious ordered behavior without consulting the fraud label."""
    events = events_for_case(case)
    score = 0.0
    patterns = [
        (("new_device", "bank_change", "velocity_spike"), 0.45),
        (("bank_change", "velocity_spike", "high_value_action"), 0.45),
        (("velocity_spike", "counterparty_spike", "high_value_action"), 0.40),
        (("new_device", "high_value_action"), 0.20),
    ]
    for pattern, weight in patterns:
        if _contains_ordered(events, pattern):
            score += weight
    return min(score, 1.0)
