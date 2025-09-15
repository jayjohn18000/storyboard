"""Abstract policy interface for validation and compliance."""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PolicyType(Enum):
    """Types of policies."""
    ADMISSIBILITY = "admissibility"
    COVERAGE = "coverage"
    DETERMINISM = "determinism"
    SIGNOFF = "signoff"


class PolicyMode(Enum):
    """Policy execution modes."""
    SANDBOX = "sandbox"
    DEMONSTRATIVE = "demonstrative"


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    allowed: bool
    reason: str
    violations: List[str]
    recommendations: List[str]
    policy_version: str
    evaluated_at: str


@dataclass
class PolicyConfig:
    """Configuration for policy evaluation."""
    mode: PolicyMode = PolicyMode.DEMONSTRATIVE
    jurisdiction: str = "us-federal"
    strict_mode: bool = True
    include_recommendations: bool = True


class PolicyService(Protocol):
    """Protocol for policy service implementations."""
    
    async def evaluate_admissibility(
        self, 
        evidence_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate evidence admissibility."""
        ...
    
    async def evaluate_coverage(
        self, 
        storyboard_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate storyboard coverage."""
        ...
    
    async def evaluate_determinism(
        self, 
        render_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate render determinism."""
        ...
    
    async def get_policy_version(self, policy_type: PolicyType) -> str:
        """Get current policy version."""
        ...


class PolicyInterface(ABC):
    """Abstract base class for policy implementations."""
    
    @abstractmethod
    async def evaluate_admissibility(
        self, 
        evidence_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate evidence admissibility."""
        pass
    
    @abstractmethod
    async def evaluate_coverage(
        self, 
        storyboard_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate storyboard coverage."""
        pass
    
    @abstractmethod
    async def evaluate_determinism(
        self, 
        render_data: Dict[str, Any], 
        config: PolicyConfig
    ) -> PolicyResult:
        """Evaluate render determinism."""
        pass
    
    @abstractmethod
    async def get_policy_version(self, policy_type: PolicyType) -> str:
        """Get current policy version."""
        pass


class PolicyError(Exception):
    """Base exception for policy operations."""
    pass


class PolicyNotFoundError(PolicyError):
    """Raised when policy is not found."""
    pass


class PolicyEvaluationError(PolicyError):
    """Raised when policy evaluation fails."""
    pass


class JurisdictionNotSupportedError(PolicyError):
    """Raised when jurisdiction is not supported."""
    pass


@dataclass
class PolicyViolation:
    """Represents a policy violation with remediation suggestions."""
    rule_id: str
    severity: str  # "error", "warning", "info"
    message: str
    remediation_suggestion: str
    evidence_id: Optional[str] = None
    case_id: Optional[str] = None
    timestamp: Optional[str] = None
