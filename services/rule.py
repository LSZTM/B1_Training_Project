from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Rule:
    table: str
    column: str
    rule_code: str
    rule_params: str
    allow_null: bool
    is_active: bool
    error_code: str
    comparison_column: Optional[str]
    category: str
    description: str
    is_implemented: bool

    @classmethod
    def from_db_row(cls, row: Any, rule_signal_map: dict[str, dict], implementation_map: dict[str, bool]):
        data = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        rule_code = str(data.get("rule_code", ""))
        meta = rule_signal_map.get(rule_code, {})
        return cls(
            table=str(data.get("table_name", data.get("table", ""))),
            column=str(data.get("column_name", data.get("column", ""))),
            rule_code=rule_code,
            rule_params=str(data.get("rule_params") or ""),
            allow_null=bool(data.get("allow_null", False)),
            is_active=bool(data.get("is_active", True)),
            error_code=str(data.get("error_code", "E000")),
            comparison_column=data.get("comparison_column"),
            category=str(meta.get("category", "general")),
            description=str(meta.get("description", "")),
            is_implemented=bool(implementation_map.get(rule_code, True)),
        )

    @classmethod
    def from_signal_map(
        cls,
        table: str,
        column: str,
        rule_code: str,
        rule_signal_map: dict[str, dict],
        implementation_map: dict[str, bool],
        rule_params: str = "",
        allow_null: bool = False,
        is_active: bool = True,
        error_code: str = "E000",
        comparison_column: Optional[str] = None,
    ):
        meta = rule_signal_map.get(rule_code, {})
        return cls(
            table=table,
            column=column,
            rule_code=rule_code,
            rule_params=rule_params or "",
            allow_null=bool(allow_null),
            is_active=bool(is_active),
            error_code=error_code or "E000",
            comparison_column=comparison_column,
            category=str(meta.get("category", "general")),
            description=str(meta.get("description", "")),
            is_implemented=bool(implementation_map.get(rule_code, True)),
        )

    def to_insert_params(self):
        return (
            self.table,
            self.column,
            self.rule_code,
            self.rule_params,
            int(self.allow_null),
            int(self.is_active),
            self.error_code,
            self.comparison_column,
        )
