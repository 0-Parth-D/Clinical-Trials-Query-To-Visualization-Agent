from app.config import Settings
from app.intent.heuristic import (
    interpret_heuristic,
    merge_country_breakdown_request,
    promote_structured_pair_to_grouped,
)
from app.intent.llm import interpret_llm
from app.intent.models import QueryIntent
from app.schemas.request import QueryRequest


def interpret_intent(body: QueryRequest, settings: Settings) -> QueryIntent:
    llm = interpret_llm(body, settings)
    if llm is not None:
        base = (llm.notes or "").strip()
        merged = f"{base} [llm]" if base else "[llm]"
        intent = llm.model_copy(update={"notes": merged})
        intent = promote_structured_pair_to_grouped(body, intent)
        return merge_country_breakdown_request(body, intent)
    return interpret_heuristic(body)


__all__ = [
    "QueryIntent",
    "interpret_intent",
    "interpret_heuristic",
    "interpret_llm",
    "merge_country_breakdown_request",
    "promote_structured_pair_to_grouped",
]
