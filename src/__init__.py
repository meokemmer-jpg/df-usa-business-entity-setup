# LAZY-IMPORT-PATTERN [CRUX-MK]
__version__ = "0.1.0-skeleton"

def get_main():
    from .usa_llc_main import USABusinessEntitySetup
    return USABusinessEntitySetup

def get_orchestrator():
    from .adapter_orchestrator import AdapterOrchestrator
    return AdapterOrchestrator

def get_audit_logger():
    from .audit_logger import AuditLogger
    return AuditLogger
