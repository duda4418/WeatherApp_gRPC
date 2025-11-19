"""Shared Pydantic configuration utilities.

Provides camelCase aliasing while keeping internal snake_case attribute names.
Clients can send either camelCase or snake_case. Responses default to camelCase.
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["CamelModel", "to_camel"]


def to_camel(s: str) -> str:
	#Convert a snake_case string to a camelCase string.
	parts = s.split("_")
	if not parts:
		return s
	return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
	"""Base model enabling camelCase aliases and dual input support.

	Internal attribute names remain snake_case for Pythonic usage while
	external representations (e.g., JSON sent to clients) default to camelCase..
	"""

	model_config = ConfigDict(
		alias_generator=to_camel,
		populate_by_name=True,
	)

	def model_dump(self, *args, **kwargs): 
		"""Override to default to using field aliases (camelCase) in dumps.

		Allows callers to still opt-out by passing by_alias=False explicitly.
		"""
		kwargs.setdefault("by_alias", True)
		return super().model_dump(*args, **kwargs)

	def model_dump_json(self, *args, **kwargs): 
		"""JSON dump defaulting to camelCase aliases."""
		kwargs.setdefault("by_alias", True)
		return super().model_dump_json(*args, **kwargs)

