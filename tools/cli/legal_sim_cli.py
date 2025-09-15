#!/usr/bin/env python3
"""Legal-Sim CLI tool for system administration and debugging.

Provides commands for case debugging, evidence verification, render troubleshooting,
system health checks, and backup verification.
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.shared.models.case import Case
from services.shared.models.evidence import Evidence
from services.shared.models.render import RenderJob
from services.shared.security.audit import AuditLogger, AuditEventType
from services.shared.services.database_service import DatabaseService
from services.shared.implementations.storage.local_storage import LocalStorage


class LegalSimCLI:
    """Main CLI class for Legal-Sim administration."""
    
    def __init__(self):
        self.setup_logging()
        self.db_service = None
        self.storage_service = None
        self.audit_logger = None
    
    def setup_logging(self):
        """Setup logging for CLI."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize_services(self):
        """Initialize database and storage services."""
        try:
            # Initialize database service
            self.db_service = DatabaseService()
            await self.db_service.connect()
            
            # Initialize storage service
            self.storage_service = LocalStorage()
            
            # Initialize audit logger
            self.audit_logger = AuditLogger(self.storage_service)
            
            self.logger.info("Services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            sys.exit(1)
    
    async def case_debug(self, case_id: str, verbose: bool = False):
        """Debug a specific case."""
        self.logger.info(f"Debugging case: {case_id}")
        
        try:
            # Get case details
            case = await self.db_service.get_case(case_id)
            if not case:
                self.logger.error(f"Case {case_id} not found")
                return
            
            print(f"\n=== Case Debug Information ===")
            print(f"Case ID: {case.id}")
            print(f"Title: {case.title}")
            print(f"Status: {case.status}")
            print(f"Created: {case.created_at}")
            print(f"Mode: {case.mode}")
            
            # Get evidence
            evidence_items = await self.db_service.get_evidence_by_case(case_id)
            print(f"\nEvidence Items: {len(evidence_items)}")
            
            for evidence in evidence_items:
                print(f"  - {evidence.filename} ({evidence.evidence_type})")
                if verbose:
                    print(f"    Status: {evidence.status}")
                    print(f"    Processed: {evidence.processed_at}")
                    print(f"    SHA256: {evidence.sha256_hash}")
            
            # Get storyboards
            storyboards = await self.db_service.get_storyboards_by_case(case_id)
            print(f"\nStoryboards: {len(storyboards)}")
            
            for storyboard in storyboards:
                print(f"  - {storyboard.title}")
                if verbose:
                    print(f"    Scenes: {len(storyboard.scenes)}")
                    print(f"    Status: {storyboard.status}")
            
            # Get render jobs
            render_jobs = await self.db_service.get_render_jobs_by_case(case_id)
            print(f"\nRender Jobs: {len(render_jobs)}")
            
            for job in render_jobs:
                print(f"  - Job {job.id}")
                print(f"    Status: {job.status}")
                print(f"    Profile: {job.profile}")
                if job.completed_at:
                    print(f"    Completed: {job.completed_at}")
            
            # Get audit trail
            audit_events = self.audit_logger.get_audit_trail(case_id=case_id)
            print(f"\nAudit Events: {len(audit_events)}")
            
            if verbose:
                for event in audit_events[-10:]:  # Show last 10 events
                    print(f"  - {event.timestamp}: {event.event_type.value}")
            
            # Check for issues
            issues = []
            
            # Check evidence processing
            unprocessed_evidence = [e for e in evidence_items if e.status != "processed"]
            if unprocessed_evidence:
                issues.append(f"Unprocessed evidence: {len(unprocessed_evidence)} items")
            
            # Check render jobs
            failed_renders = [j for j in render_jobs if j.status == "failed"]
            if failed_renders:
                issues.append(f"Failed render jobs: {len(failed_renders)}")
            
            # Check storyboard validation
            invalid_storyboards = [s for s in storyboards if s.status == "invalid"]
            if invalid_storyboards:
                issues.append(f"Invalid storyboards: {len(invalid_storyboards)}")
            
            if issues:
                print(f"\n=== Issues Found ===")
                for issue in issues:
                    print(f"  ⚠️  {issue}")
            else:
                print(f"\n✅ No issues found")
            
        except Exception as e:
            self.logger.error(f"Error debugging case: {e}")
    
    async def evidence_verify(self, evidence_id: str, check_integrity: bool = True):
        """Verify evidence integrity and processing status."""
        self.logger.info(f"Verifying evidence: {evidence_id}")
        
        try:
            evidence = await self.db_service.get_evidence(evidence_id)
            if not evidence:
                self.logger.error(f"Evidence {evidence_id} not found")
                return
            
            print(f"\n=== Evidence Verification ===")
            print(f"Evidence ID: {evidence.id}")
            print(f"Filename: {evidence.filename}")
            print(f"Type: {evidence.evidence_type}")
            print(f"Status: {evidence.status}")
            print(f"SHA256: {evidence.sha256_hash}")
            
            # Check file existence
            if await self.storage_service.exists(evidence.file_path):
                print(f"✅ File exists in storage")
                
                if check_integrity:
                    # Verify file integrity
                    try:
                        file_data = await self.storage_service.read(evidence.file_path)
                        actual_hash = hashlib.sha256(file_data).hexdigest()
                        
                        if actual_hash == evidence.sha256_hash:
                            print(f"✅ File integrity verified")
                        else:
                            print(f"❌ File integrity check failed")
                            print(f"   Expected: {evidence.sha256_hash}")
                            print(f"   Actual:   {actual_hash}")
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                else:
                    print(f"ℹ️  Integrity check skipped")
            else:
                print(f"❌ File not found in storage")
            
            # Check processing status
            if evidence.status == "processed":
                print(f"✅ Evidence has been processed")
                if evidence.ocr_text:
                    print(f"   OCR Text Length: {len(evidence.ocr_text)}")
                if evidence.transcript:
                    print(f"   Transcript Length: {len(evidence.transcript)}")
                if evidence.confidence_score:
                    print(f"   Confidence Score: {evidence.confidence_score}")
            else:
                print(f"⚠️  Evidence not yet processed (Status: {evidence.status})")
            
            # Check chain of custody
            if evidence.chain_of_custody:
                print(f"\n=== Chain of Custody ===")
                for i, entry in enumerate(evidence.chain_of_custody):
                    print(f"  {i+1}. {entry['timestamp']}: {entry['action']} by {entry['custodian']}")
            else:
                print(f"⚠️  No chain of custody information")
            
        except Exception as e:
            self.logger.error(f"Error verifying evidence: {e}")
    
    async def render_troubleshoot(self, render_id: str):
        """Troubleshoot render job issues."""
        self.logger.info(f"Troubleshooting render job: {render_id}")
        
        try:
            render_job = await self.db_service.get_render_job(render_id)
            if not render_job:
                self.logger.error(f"Render job {render_id} not found")
                return
            
            print(f"\n=== Render Job Troubleshooting ===")
            print(f"Render ID: {render_job.id}")
            print(f"Status: {render_job.status}")
            print(f"Profile: {render_job.profile}")
            print(f"Created: {render_job.created_at}")
            
            if render_job.started_at:
                print(f"Started: {render_job.started_at}")
            if render_job.completed_at:
                print(f"Completed: {render_job.completed_at}")
                duration = render_job.completed_at - render_job.started_at
                print(f"Duration: {duration}")
            
            # Check dependencies
            print(f"\n=== Dependencies ===")
            
            # Check case
            case = await self.db_service.get_case(render_job.case_id)
            if case:
                print(f"✅ Case exists: {case.title}")
            else:
                print(f"❌ Case not found: {render_job.case_id}")
            
            # Check storyboard
            if render_job.storyboard_id:
                storyboard = await self.db_service.get_storyboard(render_job.storyboard_id)
                if storyboard:
                    print(f"✅ Storyboard exists: {storyboard.title}")
                    print(f"   Scenes: {len(storyboard.scenes)}")
                else:
                    print(f"❌ Storyboard not found: {render_job.storyboard_id}")
            
            # Check timeline
            if render_job.timeline_id:
                timeline = await self.db_service.get_timeline(render_job.timeline_id)
                if timeline:
                    print(f"✅ Timeline exists: {timeline.id}")
                    print(f"   Duration: {timeline.total_duration_seconds}s")
                else:
                    print(f"❌ Timeline not found: {render_job.timeline_id}")
            
            # Check output file
            if render_job.output_path:
                if await self.storage_service.exists(render_job.output_path):
                    print(f"✅ Output file exists: {render_job.output_path}")
                    file_size = await self.storage_service.get_file_size(render_job.output_path)
                    print(f"   Size: {file_size} bytes")
                else:
                    print(f"❌ Output file not found: {render_job.output_path}")
            
            # Check for errors
            if render_job.status == "failed":
                print(f"\n=== Error Analysis ===")
                if render_job.error_message:
                    print(f"Error Message: {render_job.error_message}")
                
                # Get recent logs (this would be implemented with actual log retrieval)
                print(f"Check render orchestrator logs for detailed error information")
            
            # Performance analysis
            if render_job.started_at and render_job.completed_at:
                duration = render_job.completed_at - render_job.started_at
                print(f"\n=== Performance Analysis ===")
                print(f"Total Duration: {duration}")
                
                # Compare with expected duration
                if timeline:
                    expected_duration = timeline.total_duration_seconds
                    efficiency = (expected_duration / duration.total_seconds()) * 100
                    print(f"Expected Duration: {expected_duration}s")
                    print(f"Render Efficiency: {efficiency:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error troubleshooting render job: {e}")
    
    async def system_health_check(self):
        """Perform comprehensive system health check."""
        self.logger.info("Performing system health check")
        
        print(f"\n=== Legal-Sim System Health Check ===")
        print(f"Timestamp: {datetime.utcnow()}")
        
        health_status = {
            "database": False,
            "storage": False,
            "services": [],
            "issues": []
        }
        
        # Check database connectivity
        try:
            await self.db_service.health_check()
            print(f"✅ Database: Connected")
            health_status["database"] = True
        except Exception as e:
            print(f"❌ Database: Connection failed - {e}")
            health_status["issues"].append(f"Database connection failed: {e}")
        
        # Check storage connectivity
        try:
            # Try to list files in storage
            await self.storage_service.list_files("", limit=1)
            print(f"✅ Storage: Connected")
            health_status["storage"] = True
        except Exception as e:
            print(f"❌ Storage: Connection failed - {e}")
            health_status["issues"].append(f"Storage connection failed: {e}")
        
        # Check case statistics
        try:
            total_cases = await self.db_service.count_cases()
            active_cases = await self.db_service.count_cases(status="active")
            print(f"📊 Cases: {total_cases} total, {active_cases} active")
        except Exception as e:
            print(f"❌ Cases: Error retrieving statistics - {e}")
            health_status["issues"].append(f"Case statistics error: {e}")
        
        # Check evidence statistics
        try:
            total_evidence = await self.db_service.count_evidence()
            processed_evidence = await self.db_service.count_evidence(status="processed")
            print(f"📊 Evidence: {total_evidence} total, {processed_evidence} processed")
        except Exception as e:
            print(f"❌ Evidence: Error retrieving statistics - {e}")
            health_status["issues"].append(f"Evidence statistics error: {e}")
        
        # Check render queue
        try:
            pending_renders = await self.db_service.count_render_jobs(status="pending")
            running_renders = await self.db_service.count_render_jobs(status="running")
            print(f"📊 Render Queue: {pending_renders} pending, {running_renders} running")
        except Exception as e:
            print(f"❌ Render Queue: Error retrieving statistics - {e}")
            health_status["issues"].append(f"Render queue statistics error: {e}")
        
        # Check for stuck jobs
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            stuck_renders = await self.db_service.get_stuck_render_jobs(cutoff_time)
            if stuck_renders:
                print(f"⚠️  Stuck Render Jobs: {len(stuck_renders)}")
                for job in stuck_renders[:5]:  # Show first 5
                    print(f"   - {job.id} (started: {job.started_at})")
            else:
                print(f"✅ No stuck render jobs")
        except Exception as e:
            print(f"❌ Stuck Jobs Check: Error - {e}")
            health_status["issues"].append(f"Stuck jobs check error: {e}")
        
        # Summary
        print(f"\n=== Health Check Summary ===")
        if health_status["issues"]:
            print(f"❌ Issues Found: {len(health_status['issues'])}")
            for issue in health_status["issues"]:
                print(f"   - {issue}")
        else:
            print(f"✅ All systems healthy")
        
        return health_status
    
    async def backup_verify(self, backup_path: str):
        """Verify backup integrity and completeness."""
        self.logger.info(f"Verifying backup: {backup_path}")
        
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            self.logger.error(f"Backup directory not found: {backup_path}")
            return
        
        print(f"\n=== Backup Verification ===")
        print(f"Backup Path: {backup_path}")
        print(f"Backup Date: {datetime.fromtimestamp(backup_dir.stat().st_mtime)}")
        
        verification_results = {
            "files_found": 0,
            "files_verified": 0,
            "files_failed": 0,
            "database_backup": False,
            "storage_backup": False,
            "issues": []
        }
        
        # Check for database backup
        db_backup_files = list(backup_dir.glob("database_*.sql"))
        if db_backup_files:
            print(f"✅ Database backup found: {len(db_backup_files)} files")
            verification_results["database_backup"] = True
            verification_results["files_found"] += len(db_backup_files)
        else:
            print(f"❌ No database backup found")
            verification_results["issues"].append("No database backup found")
        
        # Check for storage backup
        storage_backup_dir = backup_dir / "storage"
        if storage_backup_dir.exists():
            storage_files = list(storage_backup_dir.rglob("*"))
            storage_files = [f for f in storage_files if f.is_file()]
            print(f"✅ Storage backup found: {len(storage_files)} files")
            verification_results["storage_backup"] = True
            verification_results["files_found"] += len(storage_files)
        else:
            print(f"❌ No storage backup found")
            verification_results["issues"].append("No storage backup found")
        
        # Check for configuration backup
        config_backup_files = list(backup_dir.glob("config_*.json"))
        if config_backup_files:
            print(f"✅ Configuration backup found: {len(config_backup_files)} files")
            verification_results["files_found"] += len(config_backup_files)
        else:
            print(f"⚠️  No configuration backup found")
        
        # Verify file integrity (sample check)
        if verification_results["files_found"] > 0:
            print(f"\n=== File Integrity Check ===")
            sample_files = []
            
            # Add some sample files for integrity check
            if db_backup_files:
                sample_files.extend(db_backup_files[:2])  # Check first 2 DB files
            if storage_backup_dir.exists():
                sample_files.extend(list(storage_backup_dir.rglob("*"))[:5])  # Check first 5 storage files
            
            for file_path in sample_files:
                if file_path.is_file():
                    try:
                        # Check if file is readable and has content
                        file_size = file_path.stat().st_size
                        if file_size > 0:
                            print(f"✅ {file_path.name}: {file_size} bytes")
                            verification_results["files_verified"] += 1
                        else:
                            print(f"❌ {file_path.name}: Empty file")
                            verification_results["files_failed"] += 1
                            verification_results["issues"].append(f"Empty file: {file_path.name}")
                    except Exception as e:
                        print(f"❌ {file_path.name}: Error - {e}")
                        verification_results["files_failed"] += 1
                        verification_results["issues"].append(f"File error {file_path.name}: {e}")
        
        # Summary
        print(f"\n=== Backup Verification Summary ===")
        print(f"Total Files: {verification_results['files_found']}")
        print(f"Verified: {verification_results['files_verified']}")
        print(f"Failed: {verification_results['files_failed']}")
        print(f"Database Backup: {'✅' if verification_results['database_backup'] else '❌'}")
        print(f"Storage Backup: {'✅' if verification_results['storage_backup'] else '❌'}")
        
        if verification_results["issues"]:
            print(f"\nIssues Found:")
            for issue in verification_results["issues"]:
                print(f"  - {issue}")
        
        return verification_results


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Legal-Sim CLI Administration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Case debug command
    case_parser = subparsers.add_parser("case-debug", help="Debug a specific case")
    case_parser.add_argument("case_id", help="Case ID to debug")
    case_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Evidence verify command
    evidence_parser = subparsers.add_parser("evidence-verify", help="Verify evidence integrity")
    evidence_parser.add_argument("evidence_id", help="Evidence ID to verify")
    evidence_parser.add_argument("--skip-integrity", action="store_true", help="Skip integrity check")
    
    # Render troubleshoot command
    render_parser = subparsers.add_parser("render-troubleshoot", help="Troubleshoot render job")
    render_parser.add_argument("render_id", help="Render job ID to troubleshoot")
    
    # System health check command
    health_parser = subparsers.add_parser("health-check", help="Perform system health check")
    
    # Backup verify command
    backup_parser = subparsers.add_parser("backup-verify", help="Verify backup integrity")
    backup_parser.add_argument("backup_path", help="Path to backup directory")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = LegalSimCLI()
    await cli.initialize_services()
    
    # Execute command
    try:
        if args.command == "case-debug":
            await cli.case_debug(args.case_id, args.verbose)
        elif args.command == "evidence-verify":
            await cli.evidence_verify(args.evidence_id, not args.skip_integrity)
        elif args.command == "render-troubleshoot":
            await cli.render_troubleshoot(args.render_id)
        elif args.command == "health-check":
            await cli.system_health_check()
        elif args.command == "backup-verify":
            await cli.backup_verify(args.backup_path)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        cli.logger.error(f"Command failed: {e}")
        sys.exit(1)
    finally:
        if cli.db_service:
            await cli.db_service.close()


if __name__ == "__main__":
    asyncio.run(main())
