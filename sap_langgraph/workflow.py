from __future__ import annotations

from typing import Any

from sap_agents import (
    BankIntelligenceAgent,
    EnrichmentAgent,
    MappingAgent,
    PipelineState,
    ValidatorAgent,
)


def _run_validator(state: PipelineState) -> PipelineState:
    return state.apply_result(ValidatorAgent().run(state.data))


def _run_enrichment(state: PipelineState) -> PipelineState:
    if state.halted:
        return state
    return state.apply_result(EnrichmentAgent().run(state.data))


def _run_mapping(state: PipelineState) -> PipelineState:
    if state.halted:
        return state
    return state.apply_result(MappingAgent().run(state.data))


def _run_bank_intelligence(state: PipelineState) -> PipelineState:
    if state.halted:
        return state
    return state.apply_result(BankIntelligenceAgent().run(state.data))


def build_graph() -> Any:
    """Build a LangGraph graph when langgraph is installed."""

    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "langgraph is not installed. Install the optional dependency with "
            "`python -m pip install langgraph` or use run_pipeline()."
        ) from exc

    graph = StateGraph(PipelineState)
    graph.add_node("validator", _run_validator)
    graph.add_node("enrichment", _run_enrichment)
    graph.add_node("mapping", _run_mapping)
    graph.add_node("bank_intelligence", _run_bank_intelligence)

    graph.set_entry_point("validator")
    graph.add_conditional_edges(
        "validator",
        lambda state: "halt" if state.halted else "continue",
        {"halt": END, "continue": "enrichment"},
    )
    graph.add_edge("enrichment", "mapping")
    graph.add_edge("mapping", "bank_intelligence")
    graph.add_edge("bank_intelligence", END)
    return graph.compile()


def run_pipeline(payload: dict[str, Any], use_langgraph: bool = False) -> PipelineState:
    """Run the vendor-to-SAP agent pipeline.

    The default path is dependency-light and mirrors the LangGraph node order.
    Pass use_langgraph=True to execute the compiled graph.
    """

    initial_state = PipelineState.from_payload(payload)
    if use_langgraph:
        result = build_graph().invoke(initial_state)
        return result if isinstance(result, PipelineState) else PipelineState.model_validate(result)

    state = _run_validator(initial_state)
    state = _run_enrichment(state)
    state = _run_mapping(state)
    state = _run_bank_intelligence(state)
    return state
