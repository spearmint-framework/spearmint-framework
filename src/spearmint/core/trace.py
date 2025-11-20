from __future__ import annotations

import uuid
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


@dataclass
class Trace:
    """Represents a logical execution segment in the experiment pipeline."""

    name: str
    trace_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    parent: "Trace | None" = None
    children: list["Trace"] = field(default_factory=list)
    _token: Token["Trace"] | None = field(init=False, default=None, repr=False)

    @property
    def attributes(self) -> dict[str, Any]:
        """Human-friendly alias for metadata, kept for backwards compatibility."""

        return self.data

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        self.data = value

    def __enter__(self) -> "Trace":
        self._token = trace_manager._enter(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        trace_manager._exit(self, self._token, exc if exc_type else None)
        self._token = None


class RootTrace(Trace):
    def __init__(self) -> None:
        super().__init__(name="root", parent=None)


@runtime_checkable
class TraceExporter(Protocol):
    def on_start(self, trace: Trace) -> None:  # pragma: no cover - protocol definition
        ...

    def on_end(self, trace: Trace, error: BaseException | None) -> None:  # pragma: no cover
        ...


class TraceManager:
    """Coordinates trace hierarchy and exporter lifecycle events."""

    def __init__(self) -> None:
        self._root = RootTrace()
        self._current: ContextVar[Trace] = ContextVar("spearmint_trace", default=self._root)
        self._exporters: list[TraceExporter] = []

    @property
    def current(self) -> Trace:
        return self._current.get()

    @property
    def context_var(self) -> ContextVar[Trace]:
        return self._current

    def register_exporter(self, exporter: TraceExporter) -> None:
        if exporter not in self._exporters:
            self._exporters.append(exporter)

    def unregister_exporter(self, exporter: TraceExporter) -> None:
        if exporter in self._exporters:
            self._exporters.remove(exporter)

    def _enter(self, trace: Trace) -> Token[Trace]:
        if trace.parent is None:
            trace.parent = self.current

        if trace.parent is not None:
            trace.parent.children.append(trace)

        if trace.trace_id is None:
            trace.trace_id = uuid.uuid4().hex

        token = self._current.set(trace)

        for exporter in self._exporters:
            exporter.on_start(trace)

        return token

    def _exit(self, trace: Trace, token: Token[Trace] | None, error: BaseException | None) -> None:
        for exporter in self._exporters:
            exporter.on_end(trace, error)

        if token is not None:
            self._current.reset(token)

    @contextmanager
    def start_trace(
        self,
        *,
        name: str,
        trace_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ):
        trace = Trace(name=name, trace_id=trace_id, data=dict(attributes or {}))
        with trace:
            yield trace


class OpenTelemetryTraceExporter:
    """Maps Trace lifecycle events to OpenTelemetry spans."""

    def __init__(self, tracer: "Any | None" = None) -> None:
        try:
            from opentelemetry import trace as otel_trace
            from opentelemetry.trace import Span, Tracer
            from opentelemetry.trace.status import Status, StatusCode
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise ModuleNotFoundError(
                "OpenTelemetry is not installed. Install 'opentelemetry-api' to use OpenTelemetryTraceExporter."
            ) from exc

        self._tracer: Tracer = tracer or otel_trace.get_tracer("spearmint.trace")
        self._Status = Status
        self._StatusCode = StatusCode
        self._span_managers: dict[int, AbstractContextManager[Any]] = {}
        self._spans: dict[int, Span] = {}

    def on_start(self, trace: Trace) -> None:
        cm = self._tracer.start_as_current_span(trace.name)
        span = cm.__enter__()

        if trace.trace_id:
            span.set_attribute("spearmint.trace_id", trace.trace_id)

        for key, value in trace.attributes.items():
            self._set_attribute(span, key, value)

        trace_key = id(trace)
        self._span_managers[trace_key] = cm
        self._spans[trace_key] = span

    def on_end(self, trace: Trace, error: BaseException | None) -> None:
        trace_key = id(trace)
        span = self._spans.pop(trace_key, None)
        cm = self._span_managers.pop(trace_key, None)

        if span is not None and error is not None:
            span.record_exception(error)
            span.set_status(self._Status(self._StatusCode.ERROR, str(error)))

        if cm is not None:
            exc_type = type(error) if error else None
            cm.__exit__(exc_type, error, getattr(error, "__traceback__", None))

    @staticmethod
    def _set_attribute(span: Any, key: str, value: Any) -> None:
        try:
            span.set_attribute(key, value)
        except Exception:  # pragma: no cover - defensive fallback for serialization issues
            span.set_attribute(key, str(value))


trace_manager = TraceManager()
current_trace: ContextVar[Trace] = trace_manager.context_var

fn_memo: ContextVar[dict[Any, Any]] = ContextVar("spearmint_memo", default={})

__all__ = [
    "Trace",
    "TraceManager",
    "TraceExporter",
    "trace_manager",
    "current_trace",
    "fn_memo",
    "OpenTelemetryTraceExporter",
]
