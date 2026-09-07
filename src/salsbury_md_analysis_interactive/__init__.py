"""Optional interactive results browser for Salsbury MD Analysis."""

__version__ = "0.1.4rc1"

from .report import InteractiveReportError, build_interactive_report

__all__ = ["InteractiveReportError", "build_interactive_report"]
