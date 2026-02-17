"""Legacy compatibility layer for membridge sync operations.

Wraps sqlite_minio_sync.py via subprocess so both legacy hooks
and the new agent API can coexist without modification.
"""

from membridge.compat.sync_wrapper import push_project, pull_project, doctor_project

__all__ = ["push_project", "pull_project", "doctor_project"]
