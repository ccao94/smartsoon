import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

class VirtualPostgresDB:
    def __init__(self):
        self._table_logs: List[Dict[str, Any]] = []
        self._table_dossiers: List[Dict[str, Any]] = []
        self._next_log_id = 1

    def insert_log(self, user_id: str, document_id: str, action: str, status: str, metadata_hash: str) -> Dict[str, Any]:
        log_entry = {
            "id": self._next_log_id,
            "user_id": user_id,
            "document_id": document_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            "metadata_hash": metadata_hash
        }
        self._table_logs.append(log_entry)
        self._next_log_id += 1
        return log_entry

    def link_document_to_dossier(self, dossier_id: str, document_id: str, filename: str):
        mapping = {
            "dossier_id": str(dossier_id),
            "document_id": str(document_id),
            "filename": filename,
            "linked_at": datetime.now(timezone.utc).isoformat()
        }
        self._table_dossiers.append(mapping)
        return mapping

    def get_documents_by_dossier(self, dossier_id: str) -> List[str]:
        return [row["document_id"] for row in self._table_dossiers if row["dossier_id"] == dossier_id]

    def select_all_logs(self) -> List[Dict[str, Any]]:
        return self._table_logs

virtual_db = VirtualPostgresDB()