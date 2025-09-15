#!/usr/bin/env python3
"""Legal-Sim Preflight Check Script.

Verifies all services are healthy, checks database migrations are current,
validates all configurations, tests external service connections,
verifies backup systems, checks monitoring is active, and validates security settings.
"""

import os
import sys
import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.shared.services.database_service import DatabaseService
from services.shared.implementations.storage.local_storage import LocalStorage
from services.shared.security.audit import AuditLogger
from services.shared.utils.monitoring import MetricsCollector


class PreflightCheck:
    """Comprehensive preflight check for Legal-Sim deployment."""
    
    def __init__(self):
        self.setup_logging()
        self.checks = []
        self.failures = []
        self.warnings = []
        
    def setup_logging(self):
        """Setup logging for preflight checks."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all preflight checks."""
        
        self.logger.info("Starting Legal-Sim Preflight Checks")
        
        start_time = time.time()
        
        # Service Health Checks
        await self.check_service_health()
        
        # Database Checks
        await self.check_database_migrations()
        await self.check_database_connectivity()
        await self.check_database_performance()
        
        # Configuration Validation
        await self.check_environment_variables()
        await self.check_configuration_files()
        
        # External Service Connections
        await self.check_external_services()
        
        # Backup Systems
        await self.check_backup_systems()
        
        # Monitoring
        await self.check_monitoring_systems()
        
        # Security
        await self.check_security_settings()
        
        # Performance
        await self.check_system_performance()
        
        end_time = time.time()
        
        # Generate report
        report = self.generate_report(start_time, end_time)
        
        self.logger.info(f"Preflight checks completed in {end_time - start_time:.2f} seconds")
        
        return report
    
    async def check_service_health(self):
        """Check if all services are healthy."""
        
        self.logger.info("Checking service health...")
        
        services = [
            {"name": "API Gateway", "port": 8000},
            {"name": "Evidence Processor", "port": 8001},
            {"name": "Storyboard Service", "port": 8002},
            {"name": "Timeline Compiler", "port": 8003},
            {"name": "Render Orchestrator", "port": 8004}
        ]
        
        for service in services:
            try:
                # Check if service is responding
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{service['port']}/health", timeout=5) as response:
                        if response.status == 200:
                            self.add_check(f"Service Health - {service['name']}", "PASS", "Service is healthy")
                        else:
                            self.add_check(f"Service Health - {service['name']}", "FAIL", f"Service returned status {response.status}")
            except Exception as e:
                self.add_check(f"Service Health - {service['name']}", "FAIL", f"Service not responding: {e}")
    
    async def check_database_migrations(self):
        """Check if database migrations are current."""
        
        self.logger.info("Checking database migrations...")
        
        try:
            db_service = DatabaseService()
            await db_service.connect()
            
            # Check migration status
            pending_migrations = await db_service.get_pending_migrations()
            
            if pending_migrations:
                self.add_check("Database Migrations", "FAIL", f"{len(pending_migrations)} pending migrations")
            else:
                self.add_check("Database Migrations", "PASS", "All migrations are current")
            
            await db_service.close()
            
        except Exception as e:
            self.add_check("Database Migrations", "FAIL", f"Failed to check migrations: {e}")
    
    async def check_database_connectivity(self):
        """Check database connectivity and basic operations."""
        
        self.logger.info("Checking database connectivity...")
        
        try:
            db_service = DatabaseService()
            await db_service.connect()
            
            # Test basic query
            result = await db_service.execute_query("SELECT 1")
            
            if result:
                self.add_check("Database Connectivity", "PASS", "Database connection successful")
            else:
                self.add_check("Database Connectivity", "FAIL", "Database query failed")
            
            await db_service.close()
            
        except Exception as e:
            self.add_check("Database Connectivity", "FAIL", f"Database connection failed: {e}")
    
    async def check_database_performance(self):
        """Check database performance."""
        
        self.logger.info("Checking database performance...")
        
        try:
            db_service = DatabaseService()
            await db_service.connect()
            
            # Test query performance
            start_time = time.time()
            await db_service.execute_query("SELECT COUNT(*) FROM cases")
            query_time = time.time() - start_time
            
            if query_time < 1.0:
                self.add_check("Database Performance", "PASS", f"Query time: {query_time:.3f}s")
            elif query_time < 5.0:
                self.add_check("Database Performance", "WARN", f"Slow query time: {query_time:.3f}s")
            else:
                self.add_check("Database Performance", "FAIL", f"Very slow query time: {query_time:.3f}s")
            
            await db_service.close()
            
        except Exception as e:
            self.add_check("Database Performance", "FAIL", f"Database performance check failed: {e}")
    
    async def check_environment_variables(self):
        """Check required environment variables."""
        
        self.logger.info("Checking environment variables...")
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "STORAGE_URL",
            "JWT_SECRET",
            "ENCRYPTION_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.add_check("Environment Variables", "FAIL", f"Missing variables: {', '.join(missing_vars)}")
        else:
            self.add_check("Environment Variables", "PASS", "All required variables present")
    
    async def check_configuration_files(self):
        """Check configuration files."""
        
        self.logger.info("Checking configuration files...")
        
        config_files = [
            "config/policy-packs/opa-policies.rego",
            "config/rbac-policies/case.yaml",
            "config/rbac-policies/evidence.yaml",
            "config/rbac-policies/storyboard.yaml",
            "config/rbac-policies/render.yaml",
            "config/rbac-policies/export.yaml"
        ]
        
        missing_files = []
        for file_path in config_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.add_check("Configuration Files", "FAIL", f"Missing files: {', '.join(missing_files)}")
        else:
            self.add_check("Configuration Files", "PASS", "All configuration files present")
    
    async def check_external_services(self):
        """Check external service connections."""
        
        self.logger.info("Checking external services...")
        
        external_services = [
            {"name": "Redis", "url": os.getenv("REDIS_URL", "redis://localhost:6379")},
            {"name": "MinIO/S3", "url": os.getenv("STORAGE_URL", "http://localhost:9000")},
            {"name": "OPA", "url": os.getenv("OPA_URL", "http://localhost:8181")}
        ]
        
        for service in external_services:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{service['url']}/health", timeout=5) as response:
                        if response.status == 200:
                            self.add_check(f"External Service - {service['name']}", "PASS", "Service is healthy")
                        else:
                            self.add_check(f"External Service - {service['name']}", "FAIL", f"Service returned status {response.status}")
            except Exception as e:
                self.add_check(f"External Service - {service['name']}", "FAIL", f"Service not responding: {e}")
    
    async def check_backup_systems(self):
        """Check backup systems."""
        
        self.logger.info("Checking backup systems...")
        
        try:
            # Check if backup directory exists and is writable
            backup_dir = Path("/backups")
            if backup_dir.exists() and backup_dir.is_dir():
                # Test write access
                test_file = backup_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                self.add_check("Backup Systems", "PASS", "Backup directory is accessible")
            else:
                self.add_check("Backup Systems", "FAIL", "Backup directory not accessible")
                
        except Exception as e:
            self.add_check("Backup Systems", "FAIL", f"Backup system check failed: {e}")
    
    async def check_monitoring_systems(self):
        """Check monitoring systems."""
        
        self.logger.info("Checking monitoring systems...")
        
        try:
            # Check if metrics collector is working
            metrics = MetricsCollector("preflight-check")
            metrics.increment_counter("preflight_check_test")
            
            self.add_check("Monitoring Systems", "PASS", "Metrics collection is working")
            
        except Exception as e:
            self.add_check("Monitoring Systems", "FAIL", f"Monitoring check failed: {e}")
    
    async def check_security_settings(self):
        """Check security settings."""
        
        self.logger.info("Checking security settings...")
        
        security_checks = []
        
        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET")
        if jwt_secret and len(jwt_secret) >= 32:
            security_checks.append(("JWT Secret", "PASS", "JWT secret is properly configured"))
        else:
            security_checks.append(("JWT Secret", "FAIL", "JWT secret is not properly configured"))
        
        # Check encryption key
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if encryption_key and len(encryption_key) >= 32:
            security_checks.append(("Encryption Key", "PASS", "Encryption key is properly configured"))
        else:
            security_checks.append(("Encryption Key", "FAIL", "Encryption key is not properly configured"))
        
        # Check SSL/TLS settings
        ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
        if ssl_enabled:
            security_checks.append(("SSL/TLS", "PASS", "SSL/TLS is enabled"))
        else:
            security_checks.append(("SSL/TLS", "WARN", "SSL/TLS is not enabled"))
        
        for check_name, status, message in security_checks:
            self.add_check(f"Security - {check_name}", status, message)
    
    async def check_system_performance(self):
        """Check system performance."""
        
        self.logger.info("Checking system performance...")
        
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent < 80:
                self.add_check("System Performance - CPU", "PASS", f"CPU usage: {cpu_percent:.1f}%")
            else:
                self.add_check("System Performance - CPU", "WARN", f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent < 80:
                self.add_check("System Performance - Memory", "PASS", f"Memory usage: {memory.percent:.1f}%")
            else:
                self.add_check("System Performance - Memory", "WARN", f"High memory usage: {memory.percent:.1f}%")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent < 80:
                self.add_check("System Performance - Disk", "PASS", f"Disk usage: {disk.percent:.1f}%")
            else:
                self.add_check("System Performance - Disk", "WARN", f"High disk usage: {disk.percent:.1f}%")
                
        except Exception as e:
            self.add_check("System Performance", "FAIL", f"Performance check failed: {e}")
    
    def add_check(self, check_name: str, status: str, message: str):
        """Add a check result."""
        
        check_result = {
            "name": check_name,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.checks.append(check_result)
        
        if status == "FAIL":
            self.failures.append(check_result)
        elif status == "WARN":
            self.warnings.append(check_result)
    
    def generate_report(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate preflight check report."""
        
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c["status"] == "PASS"])
        warning_checks = len(self.warnings)
        failed_checks = len(self.failures)
        
        overall_status = "PASS"
        if failed_checks > 0:
            overall_status = "FAIL"
        elif warning_checks > 0:
            overall_status = "WARN"
        
        report = {
            "overall_status": overall_status,
            "check_summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "warnings": warning_checks,
                "failed": failed_checks,
                "duration_seconds": end_time - start_time
            },
            "checks": self.checks,
            "failures": self.failures,
            "warnings": self.warnings,
            "recommendations": self.generate_recommendations(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on check results."""
        
        recommendations = []
        
        if self.failures:
            recommendations.append("Fix all failed checks before proceeding with deployment")
        
        if self.warnings:
            recommendations.append("Review and address warning conditions")
        
        # Specific recommendations based on failures
        for failure in self.failures:
            if "Service Health" in failure["name"]:
                recommendations.append("Ensure all services are running and healthy")
            elif "Database" in failure["name"]:
                recommendations.append("Check database connectivity and configuration")
            elif "Security" in failure["name"]:
                recommendations.append("Review and fix security configuration")
            elif "Backup" in failure["name"]:
                recommendations.append("Configure and test backup systems")
        
        if not self.failures and not self.warnings:
            recommendations.append("All checks passed - system is ready for deployment")
        
        return recommendations


async def main():
    """Main entry point for preflight checks."""
    
    check = PreflightCheck()
    
    try:
        report = await check.run_all_checks()
        
        # Print summary
        print(f"\n=== Legal-Sim Preflight Check Report ===")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Checks: {report['check_summary']['total_checks']}")
        print(f"Passed: {report['check_summary']['passed']}")
        print(f"Warnings: {report['check_summary']['warnings']}")
        print(f"Failed: {report['check_summary']['failed']}")
        print(f"Duration: {report['check_summary']['duration_seconds']:.2f} seconds")
        
        # Print failures
        if report['failures']:
            print(f"\n=== FAILURES ===")
            for failure in report['failures']:
                print(f"❌ {failure['name']}: {failure['message']}")
        
        # Print warnings
        if report['warnings']:
            print(f"\n=== WARNINGS ===")
            for warning in report['warnings']:
                print(f"⚠️  {warning['name']}: {warning['message']}")
        
        # Print recommendations
        if report['recommendations']:
            print(f"\n=== RECOMMENDATIONS ===")
            for recommendation in report['recommendations']:
                print(f"💡 {recommendation}")
        
        # Save report
        report_file = Path("preflight_report.json")
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\nDetailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['overall_status'] == "FAIL":
            sys.exit(1)
        elif report['overall_status'] == "WARN":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Preflight check failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
