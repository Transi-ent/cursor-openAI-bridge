from __future__ import annotations


class ModelAliasResolver:
    def __init__(self, aliases: dict[str, str]) -> None:
        self._aliases = aliases
        self._lower_to_upstream: dict[str, str] = {
            k.lower(): v for k, v in aliases.items()
        }

    @property
    def cursor_names(self) -> list[str]:
        return list(self._aliases.keys())

    def resolve(self, model: str) -> str:
        name = (model or "").strip()
        if not name:
            raise ValueError("model is required")

        if name in self._aliases:
            return self._aliases[name]

        lower = name.lower()
        if lower in self._lower_to_upstream:
            return self._lower_to_upstream[lower]

        # 已是九天格式则透传，便于调试
        if "/" in name and not name.startswith("gpt-"):
            return name

        available = ", ".join(self._aliases.keys())
        raise ValueError(
            f"Unknown model '{model}'. Available aliases: {available}"
        )
