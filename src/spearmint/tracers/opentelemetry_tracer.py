from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

from .trace import TraceEvent, Tracer


class InMemoryOpenTelemetryTracer(Tracer):
    def __init__(self) -> None:
        self._span_exporter = InMemorySpanExporter()
        span_processor = SimpleSpanProcessor(self._span_exporter)
        provider = TracerProvider()
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        if provider != trace.get_tracer_provider():
            raise RuntimeError(
                "Failed to set InMemoryTracerProvider. A different provider is already set elsewhere."
            )
        self._tracer = trace.get_tracer(__name__)

    @contextmanager
    def trace(self, event: TraceEvent, context: dict[str, Any]) -> Generator[Any, None, None]:
        """
        Start a span nested under an existing parent (if any) and yield control.
        Parent precedence: context["span"] / context["parent_span"] > current active span.
        """
        parent = context.get("span") or context.get("parent_span") or trace.get_current_span()
        maybe_ctx = None
        if parent and parent.get_span_context().is_valid:
            maybe_ctx = trace.set_span_in_context(parent)

        with self._tracer.start_as_current_span(event.value, context=maybe_ctx) as span:
            for key, value in context.items():
                span.set_attribute(key, str(value))
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def get_traces(self) -> Generator[dict[str, Any], None, None]:
        spans = self._span_exporter.get_finished_spans()
        for span in spans:
            yield {
                "name": span.name,
                "context": span.context or {},
                "start_time": span.start_time,
                "end_time": span.end_time,
                "attributes": span.attributes,
                "status": span.status,
                "parent": span.parent,
            }

    # def get_nested_traces(self) -> list[dict[str, Any]]:
    #     """
    #     Build a nested span structure by linking children to their parents.
    #     Returns a list of root spans (those with no parent), each containing
    #     their children recursively.
    #     """
    #     spans = self._span_exporter.get_finished_spans()

    #     # Build a dictionary of spans by their span_id for quick lookup
    #     span_dict: dict[int, dict[str, Any]] = {}
    #     for span in spans:
    #         span_id = span.context.span_id if span.context else id(span)
    #         span_dict[span_id] = {
    #             "name": span.name,
    #             "context": span.context or {},
    #             "start_time": span.start_time,
    #             "end_time": span.end_time,
    #             "attributes": span.attributes,
    #             "status": span.status,
    #             "parent": span.parent,
    #             "children": [],
    #         }

    #     # Link children to their parents
    #     roots = []
    #     for _span_id, span_data in span_dict.items():
    #         parent = span_data["parent"]
    #         if parent is None:
    #             # This is a root span
    #             roots.append(span_data)
    #         else:
    #             # Find the parent and add this span as a child
    #             parent_span_id = parent.span_id if hasattr(parent, "span_id") else None
    #             if parent_span_id and parent_span_id in span_dict:
    #                 span_dict[parent_span_id]["children"].append(span_data)
    #             else:
    #                 # Parent not found in our span collection, treat as root
    #                 roots.append(span_data)

    #     return roots


__all__ = ["InMemoryOpenTelemetryTracer"]
