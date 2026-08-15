"""Entity-link graph analytics for marketplace trust and safety."""

from dataclasses import dataclass
from math import log2

from riskos.simulator import SyntheticCase


@dataclass(frozen=True)
class GraphSignal:
    entity_id: str
    component_size: int
    peer_count: int
    shared_resource_count: int
    graph_score: float


def _resource_groups(cases: list[SyntheticCase]) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for case in cases:
        entity = case.features.entity_id
        for resource in (case.device_id, case.bank_id, case.ip_id):
            groups.setdefault(resource, set()).add(entity)
    return groups


def graph_signals(cases: list[SyntheticCase]) -> dict[str, GraphSignal]:
    """Calculate label-free connected-component and shared-resource risk signals."""
    entity_ids = [case.features.entity_id for case in cases]
    adjacency = {entity_id: set() for entity_id in entity_ids}
    shared_counts = {entity_id: 0 for entity_id in entity_ids}

    for members in _resource_groups(cases).values():
        if len(members) < 2:
            continue
        for entity in members:
            shared_counts[entity] += 1
            adjacency[entity].update(members - {entity})

    component_size: dict[str, int] = {}
    visited: set[str] = set()
    for start in entity_ids:
        if start in visited:
            continue
        stack = [start]
        component: list[str] = []
        visited.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        for node in component:
            component_size[node] = len(component)

    output: dict[str, GraphSignal] = {}
    for entity_id in entity_ids:
        peers = len(adjacency[entity_id])
        size = component_size[entity_id]
        shared = shared_counts[entity_id]
        score = min(1.0, 0.18 * shared + 0.06 * peers + 0.10 * log2(max(1, size)))
        output[entity_id] = GraphSignal(entity_id, size, peers, shared, score)
    return output


def suspicious_components(cases: list[SyntheticCase], min_size: int = 3) -> list[list[str]]:
    """Return connected entity clusters without consulting synthetic fraud labels."""
    signals = graph_signals(cases)
    groups = _resource_groups(cases)
    adjacency = {entity_id: set() for entity_id in signals}
    for members in groups.values():
        if len(members) > 1:
            for entity in members:
                adjacency[entity].update(members - {entity})

    visited: set[str] = set()
    components: list[list[str]] = []
    for start in adjacency:
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        component: list[str] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        if len(component) >= min_size:
            components.append(sorted(component))
    return sorted(components, key=len, reverse=True)
