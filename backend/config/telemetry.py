"""OpenTelemetry setup and privacy-safe weekly journal workflow metrics."""

from __future__ import annotations

import os
from time import time_ns

from opentelemetry import metrics, trace
from opentelemetry._logs import SeverityNumber, get_logger, set_logger_provider
from opentelemetry.context import get_current
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_configured = False
_workflow_events = None
_workflow_logger = None


def _privacy_safe_request_hook(span, _request) -> None:
    """Avoid exporting raw request paths and query strings from Django spans."""
    span.set_attribute("url.path", "/redacted")
    span.set_attribute("url.query", "")
    span.set_attribute("http.target", "/redacted")


def configure_telemetry() -> None:
    """Export traces, metrics, and correlated logs when an OTLP endpoint exists."""
    global _configured, _workflow_events, _workflow_logger
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if _configured or not endpoint or os.environ.get("OTEL_SDK_DISABLED", "").lower() == "true":
        return

    resource = Resource.create(
        {
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "weekly-growth-journal-api"),
            "deployment.environment.name": os.environ.get("APP_ENV", "development"),
            "service.version": os.environ.get("APP_VERSION", "unknown"),
        }
    )
    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint)))
    set_logger_provider(logger_provider)
    _workflow_logger = get_logger("weekly_growth_journal.workflow")

    DjangoInstrumentor().instrument(
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        excluded_urls=r"^/api/health/?$",
        request_hook=_privacy_safe_request_hook,
    )
    _workflow_events = metrics.get_meter("weekly_growth_journal.workflow").create_counter(
        "journal.workflow.events",
        description="Privacy-safe counts of weekly journal workflow events.",
    )
    _configured = True


def record_workflow_event(event: str, outcome: str = "success") -> None:
    """Count named workflow milestones without user IDs or reflection content."""
    if _workflow_events is not None:
        _workflow_events.add(1, {"workflow.event": event, "outcome": outcome})
        _workflow_logger.emit(
            body="journal workflow event",
            attributes={"workflow.event": event, "outcome": outcome},
            context=get_current(),
            severity_number=SeverityNumber.INFO,
            severity_text="INFO",
            timestamp=time_ns(),
            observed_timestamp=time_ns(),
        )
