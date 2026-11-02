"""Read live resource properties and normalize them for InfraFix."""

from typing import Dict, Protocol
import json

from glitch.repr.inter import String, ElementInfo
from glitch.tech import Tech
from glitch.repair.interactive.system import State, SystemState
from glitch.repair.interactive.compiler.names_database import NamesDatabase
from glitch.repair.interactive.compiler.compiler import DeltaPCompiler


class CloudControlClient(Protocol):
    def get_resource(self, type_name: str, identifier: str) -> Dict:
        """Return a resource type and its live properties."""
        ...


class MockCloudControlClient:
    """In-memory client keyed by ``"TypeName:Identifier"`` (for tests)."""

    def __init__(self, resources: Dict[str, Dict]) -> None:
        self._resources = resources

    def get_resource(self, type_name: str, identifier: str) -> Dict:
        key = f"{type_name}:{identifier}"
        if key not in self._resources:
            raise KeyError(f"No live resource for {key}")
        return self._resources[key]


class BotoCloudControlClient:
    """Cloud Control ``GetResource`` client backed by boto3."""

    def __init__(self, region_name: str = "us-east-1") -> None:
        import boto3

        self._client = boto3.client("cloudcontrol", region_name=region_name)

    def get_resource(self, type_name: str, identifier: str) -> Dict:
        response = self._client.get_resource(
            TypeName=type_name, Identifier=identifier
        )
        description = response["ResourceDescription"]
        raw_properties = description.get("Properties")
        return {
            "TypeName": response.get("TypeName", type_name),
            "Properties": json.loads(raw_properties) if raw_properties else {},
        }


def build_system_state(
    type_name: str, identifier: str, properties: Dict, tech: Tech
) -> SystemState:
    """Convert Cloud Control properties to the solver's normalized state."""
    au_type = NamesDatabase.get_au_type(type_name, tech)
    if au_type not in DeltaPCompiler.AU_TYPE_ATTRIBUTES:
        raise ValueError(f"Unsupported resource type: {au_type}")

    supported = set(DeltaPCompiler.AU_TYPE_ATTRIBUTES[au_type])

    state = State()
    state.attrs["state"] = "present"

    for prop_name, prop_value in properties.items():
        norm_name, norm_expr = NamesDatabase.get_attr_pair(
            String(str(prop_value), ElementInfo.get_sketched()),
            prop_name,
            au_type,
            tech,
        )
        if norm_name in supported:
            state.attrs[norm_name] = (
                norm_expr.value
                if isinstance(norm_expr, String)
                else str(prop_value)
            )

    system_state = SystemState()
    system_state.state[f"{au_type}:{identifier}"] = state
    return system_state
