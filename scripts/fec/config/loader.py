"""Configuration loading and management."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CombineDataset:
    """Configuration for a combine-strategy dataset."""

    name: str
    output_file: str
    fec_prefix: str
    start_year: int
    description: str
    columns: list[str]


@dataclass
class SummarizeDataset:
    """Configuration for a summarize-strategy dataset."""

    name: str
    output_file: str
    fec_prefix: str
    start_year: int
    description: str
    group_by: list[str]
    column_mapping: dict[str, str]
    amount_field: str
    date_field: str
    memo_field: str
    amendment_field: str
    sub_id_field: str
    input_columns: list[str]


@dataclass
class Config:
    """Full configuration for FEC update workflow."""

    fec_base_url: str
    combine_datasets: dict[str, CombineDataset]
    summarize_datasets: dict[str, SummarizeDataset]
    data_dir: Path
    state_file: Path

    @classmethod
    def load(cls, config_path: Path, data_dir: Path) -> "Config":
        """Load configuration from YAML file."""
        with open(config_path) as f:
            raw = yaml.safe_load(f)

        combine_datasets = {}
        for name, cfg in raw.get("combine_datasets", {}).items():
            combine_datasets[name] = CombineDataset(
                name=name,
                output_file=cfg["output_file"],
                fec_prefix=cfg["fec_prefix"],
                start_year=cfg["start_year"],
                description=cfg["description"],
                columns=cfg["columns"],
            )

        summarize_datasets = {}
        for name, cfg in raw.get("summarize_datasets", {}).items():
            summarize_datasets[name] = SummarizeDataset(
                name=name,
                output_file=cfg["output_file"],
                fec_prefix=cfg["fec_prefix"],
                start_year=cfg["start_year"],
                description=cfg["description"],
                group_by=cfg["group_by"],
                column_mapping=cfg["column_mapping"],
                amount_field=cfg["amount_field"],
                date_field=cfg["date_field"],
                memo_field=cfg["memo_field"],
                amendment_field=cfg["amendment_field"],
                sub_id_field=cfg["sub_id_field"],
                input_columns=cfg["input_columns"],
            )

        state_file = data_dir.parent / ".fec_update_state.json"

        return cls(
            fec_base_url=raw["fec_base_url"],
            combine_datasets=combine_datasets,
            summarize_datasets=summarize_datasets,
            data_dir=data_dir,
            state_file=state_file,
        )


@dataclass
class CycleState:
    """State for a single election cycle."""

    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    last_updated: str | None = None


@dataclass
class UpdateState:
    """Tracks state of FEC data updates."""

    cycles: dict[str, dict[str, CycleState]] = field(default_factory=dict)
    last_check: str | None = None

    @classmethod
    def load(cls, state_file: Path) -> "UpdateState":
        """Load state from JSON file."""
        if not state_file.exists():
            return cls()

        with open(state_file) as f:
            raw = json.load(f)

        cycles = {}
        for dataset, dataset_cycles in raw.get("cycles", {}).items():
            cycles[dataset] = {}
            for cycle, state in dataset_cycles.items():
                cycles[dataset][cycle] = CycleState(
                    etag=state.get("etag"),
                    last_modified=state.get("last_modified"),
                    content_length=state.get("content_length"),
                    last_updated=state.get("last_updated"),
                )

        return cls(
            cycles=cycles,
            last_check=raw.get("last_check"),
        )

    def save(self, state_file: Path) -> None:
        """Save state to JSON file."""
        data: dict[str, Any] = {
            "last_check": self.last_check,
            "cycles": {},
        }

        for dataset, dataset_cycles in self.cycles.items():
            data["cycles"][dataset] = {}
            for cycle, state in dataset_cycles.items():
                data["cycles"][dataset][cycle] = {
                    "etag": state.etag,
                    "last_modified": state.last_modified,
                    "content_length": state.content_length,
                    "last_updated": state.last_updated,
                }

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_cycle(
        self,
        dataset: str,
        cycle: int,
        etag: str | None,
        last_modified: str | None,
        content_length: int | None,
    ) -> None:
        """Update state for a cycle."""
        if dataset not in self.cycles:
            self.cycles[dataset] = {}

        self.cycles[dataset][str(cycle)] = CycleState(
            etag=etag,
            last_modified=last_modified,
            content_length=content_length,
            last_updated=datetime.now().isoformat(),
        )

    def get_cycle_state(self, dataset: str, cycle: int) -> CycleState | None:
        """Get state for a cycle."""
        if dataset not in self.cycles:
            return None
        return self.cycles[dataset].get(str(cycle))


def get_current_cycle() -> int:
    """Get the current election cycle (even year)."""
    year = datetime.now().year
    return year if year % 2 == 0 else year + 1


def get_cycles_to_check() -> list[int]:
    """Get cycles to check for updates (current + 2 prior for amendment window)."""
    current = get_current_cycle()
    return [current, current - 2, current - 4]


def get_fec_zip_url(base_url: str, prefix: str, cycle: int) -> str:
    """Build FEC zip file URL for a dataset and cycle."""
    # FEC uses 2-digit year suffix for filenames
    year_suffix = str(cycle)[2:]
    return f"{base_url}/{cycle}/{prefix}{year_suffix}.zip"
