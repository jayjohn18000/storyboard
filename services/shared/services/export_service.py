"""Export service for legal simulation platform."""

import json
import zipfile
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import uuid

from ..database_service import DatabaseService
from ..evidence_service import EvidenceService
from ..render_service import RenderService
from ...models.case import Case
from ...models.evidence import Evidence
from ...models.storyboard import Storyboard
from ...models.render import RenderJob


class ExportService:
    """Service for exporting case data in various formats."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.evidence_service = EvidenceService(db_service)
        self.render_service = RenderService(db_service)
    
    async def create_export_job(
        self,
        case_id: str,
        format: str,
        include_evidence: bool = True,
        include_storyboards: bool = True,
        include_renders: bool = True,
        include_metadata: bool = True,
        include_chain_of_custody: bool = True,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """Create a new export job."""
        export_id = str(uuid.uuid4())
        
        # Create export job record
        export_job = {
            "id": export_id,
            "case_id": case_id,
            "format": format,
            "status": "processing",
            "include_evidence": include_evidence,
            "include_storyboards": include_storyboards,
            "include_renders": include_renders,
            "include_metadata": include_metadata,
            "include_chain_of_custody": include_chain_of_custody,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "file_size_bytes": 0,
            "download_url": f"/api/v1/export/{export_id}/download",
            "checksum": "",
        }
        
        # Store export job in database
        await self.db_service.create_export_job(export_job)
        
        # Process export asynchronously
        # In production, this would be queued for background processing
        await self._process_export_job(export_job)
        
        return export_job
    
    async def _process_export_job(self, export_job: Dict[str, Any]) -> None:
        """Process an export job."""
        try:
            case_id = export_job["case_id"]
            format = export_job["format"]
            
            # Get case data
            case = await self.db_service.get_case(case_id)
            if not case:
                await self._update_export_status(export_job["id"], "failed", "Case not found")
                return
            
            # Collect data based on export options
            export_data = await self._collect_export_data(export_job, case)
            
            # Generate export file
            file_path, file_size, checksum = await self._generate_export_file(
                export_data, format, export_job["id"]
            )
            
            # Update export job with completion details
            await self._update_export_status(
                export_job["id"],
                "completed",
                None,
                file_size,
                checksum,
                file_path
            )
            
        except Exception as e:
            await self._update_export_status(export_job["id"], "failed", str(e))
    
    async def _collect_export_data(
        self, 
        export_job: Dict[str, Any], 
        case: Case
    ) -> Dict[str, Any]:
        """Collect data for export based on job options."""
        export_data = {
            "case": {
                "id": str(case.id),
                "title": case.title,
                "status": case.status,
                "metadata": case.metadata,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
                "created_by": case.created_by,
            }
        }
        
        if export_job["include_metadata"]:
            export_data["case"]["metadata"] = case.metadata
        
        if export_job["include_evidence"]:
            evidence_list = await self.evidence_service.list_evidence(case_id=str(case.id))
            export_data["evidence"] = [
                {
                    "id": evidence.id,
                    "filename": evidence.metadata.filename,
                    "content_type": evidence.metadata.content_type,
                    "size_bytes": evidence.metadata.size_bytes,
                    "checksum": evidence.metadata.checksum,
                    "status": evidence.status.value,
                    "worm_locked": evidence.worm_locked,
                    "created_at": evidence.metadata.created_at.isoformat(),
                    "uploaded_by": evidence.metadata.uploaded_by,
                }
                for evidence in evidence_list
            ]
        
        if export_job["include_storyboards"]:
            storyboards = await self.db_service.list_storyboards(case_id=str(case.id))
            export_data["storyboards"] = [
                {
                    "id": str(storyboard.id),
                    "title": storyboard.title,
                    "content": storyboard.content,
                    "validation_result": storyboard.validation_result,
                    "created_at": storyboard.created_at.isoformat(),
                    "updated_at": storyboard.updated_at.isoformat(),
                    "created_by": storyboard.created_by,
                }
                for storyboard in storyboards
            ]
        
        if export_job["include_renders"]:
            renders = await self.render_service.list_renders_by_case(str(case.id))
            export_data["renders"] = [
                {
                    "id": str(render.id),
                    "status": render.status.value,
                    "quality": render.quality,
                    "profile": render.profile,
                    "deterministic": render.deterministic,
                    "output_format": render.output_format,
                    "file_size_bytes": render.file_size_bytes,
                    "duration_seconds": render.duration_seconds,
                    "created_at": render.created_at.isoformat(),
                    "completed_at": render.completed_at.isoformat() if render.completed_at else None,
                }
                for render in renders
            ]
        
        if export_job["include_chain_of_custody"]:
            export_data["chain_of_custody"] = await self._get_chain_of_custody(str(case.id))
        
        return export_data
    
    async def _generate_export_file(
        self, 
        export_data: Dict[str, Any], 
        format: str, 
        export_id: str
    ) -> tuple[str, int, str]:
        """Generate export file in specified format."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
            if format == "json":
                json.dump(export_data, temp_file, indent=2, default=str)
            elif format == "xml":
                # Convert to XML format
                xml_content = self._dict_to_xml(export_data)
                temp_file.write(xml_content.encode('utf-8'))
            elif format == "zip":
                # Create ZIP with multiple files
                with zipfile.ZipFile(temp_file, 'w') as zip_file:
                    # Add JSON data
                    zip_file.writestr("case_data.json", json.dumps(export_data, indent=2, default=str))
                    
                    # Add evidence files if present
                    if "evidence" in export_data:
                        for evidence in export_data["evidence"]:
                            # In production, would copy actual files
                            zip_file.writestr(f"evidence/{evidence['filename']}", "Evidence file content")
            
            file_path = temp_file.name
        
        # Calculate file size and checksum
        file_size = Path(file_path).stat().st_size
        checksum = self._calculate_checksum(file_path)
        
        return file_path, file_size, checksum
    
    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = "export") -> str:
        """Convert dictionary to XML format."""
        def dict_to_xml_recursive(d, root):
            xml = f"<{root}>"
            for key, value in d.items():
                if isinstance(value, dict):
                    xml += self._dict_to_xml(value, key)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            xml += self._dict_to_xml(item, key[:-1] if key.endswith('s') else key)
                        else:
                            xml += f"<{key}>{item}</{key}>"
                else:
                    xml += f"<{key}>{value}</{key}>"
            xml += f"</{root}>"
            return xml
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{dict_to_xml_recursive(data, root_name)}'
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file."""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _get_chain_of_custody(self, case_id: str) -> List[Dict[str, Any]]:
        """Get chain of custody for case."""
        # Get all evidence for case
        evidence_list = await self.evidence_service.list_evidence(case_id=case_id)
        
        chain_entries = []
        for evidence in evidence_list:
            chain_entries.extend(evidence.chain_of_custody)
        
        # Sort by timestamp
        chain_entries.sort(key=lambda x: x.get("timestamp", ""))
        
        return chain_entries
    
    async def _update_export_status(
        self,
        export_id: str,
        status: str,
        error_message: Optional[str] = None,
        file_size: int = 0,
        checksum: str = "",
        file_path: Optional[str] = None
    ) -> None:
        """Update export job status."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }
        
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
            update_data["file_size_bytes"] = file_size
            update_data["checksum"] = checksum
            if file_path:
                update_data["file_path"] = file_path
        
        if error_message:
            update_data["error_message"] = error_message
        
        await self.db_service.update_export_job(export_id, update_data)
    
    async def get_export_job(self, export_id: str) -> Optional[Dict[str, Any]]:
        """Get export job by ID."""
        return await self.db_service.get_export_job(export_id)
    
    async def get_export_file(self, export_id: str) -> bytes:
        """Get export file data."""
        export_job = await self.get_export_job(export_id)
        if not export_job or export_job["status"] != "completed":
            raise ValueError("Export not found or not completed")
        
        file_path = export_job.get("file_path")
        if not file_path or not Path(file_path).exists():
            raise ValueError("Export file not found")
        
        with open(file_path, "rb") as f:
            return f.read()
    
    async def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """Get case summary for export."""
        case = await self.db_service.get_case(case_id)
        if not case:
            raise ValueError("Case not found")
        
        evidence_list = await self.evidence_service.list_evidence(case_id=case_id)
        storyboards = await self.db_service.list_storyboards(case_id=case_id)
        renders = await self.render_service.list_renders_by_case(case_id)
        
        total_duration = sum(render.duration_seconds or 0 for render in renders)
        
        return {
            "case_id": case_id,
            "title": case.title,
            "status": case.status,
            "evidence_count": len(evidence_list),
            "storyboard_count": len(storyboards),
            "render_count": len(renders),
            "total_duration": total_duration,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        }
    
    async def get_evidence_summary(self, case_id: str) -> Dict[str, Any]:
        """Get evidence summary for case."""
        evidence_list = await self.evidence_service.list_evidence(case_id=case_id)
        
        by_type = {}
        total_size = 0
        processed_count = 0
        worm_locked_count = 0
        
        for evidence in evidence_list:
            evidence_type = evidence.evidence_type.value
            by_type[evidence_type] = by_type.get(evidence_type, 0) + 1
            
            total_size += evidence.metadata.size_bytes
            
            if evidence.status.value == "processed":
                processed_count += 1
            
            if evidence.worm_locked:
                worm_locked_count += 1
        
        return {
            "case_id": case_id,
            "total_evidence": len(evidence_list),
            "by_type": by_type,
            "total_size_bytes": total_size,
            "processed_count": processed_count,
            "worm_locked_count": worm_locked_count,
        }
    
    async def get_storyboard_summary(self, case_id: str) -> Dict[str, Any]:
        """Get storyboard summary for case."""
        storyboards = await self.db_service.list_storyboards(case_id=case_id)
        
        total_scenes = 0
        total_duration = 0.0
        by_status = {}
        
        for storyboard in storyboards:
            # Parse storyboard content to count scenes
            try:
                content = json.loads(storyboard.content)
                scenes = content.get("scenes", [])
                total_scenes += len(scenes)
                
                # Calculate total duration
                for scene in scenes:
                    total_duration += scene.get("duration_seconds", 0)
            except (json.JSONDecodeError, KeyError):
                pass
            
            status = storyboard.validation_result.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "case_id": case_id,
            "total_storyboards": len(storyboards),
            "total_scenes": total_scenes,
            "total_duration": total_duration,
            "by_status": by_status,
            "evidence_coverage": 0.0,  # Would need to calculate based on evidence coverage
        }
    
    async def get_render_summary(self, case_id: str) -> Dict[str, Any]:
        """Get render summary for case."""
        renders = await self.render_service.list_renders_by_case(case_id)
        
        total_duration = sum(render.duration_seconds or 0 for render in renders)
        total_file_size = sum(render.file_size_bytes or 0 for render in renders)
        
        by_status = {}
        by_quality = {}
        deterministic_count = 0
        
        for render in renders:
            status = render.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            quality = render.quality
            by_quality[quality] = by_quality.get(quality, 0) + 1
            
            if render.deterministic:
                deterministic_count += 1
        
        return {
            "case_id": case_id,
            "total_renders": len(renders),
            "total_duration": total_duration,
            "total_file_size_bytes": total_file_size,
            "by_status": by_status,
            "by_quality": by_quality,
            "deterministic_count": deterministic_count,
        }
