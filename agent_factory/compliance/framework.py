"""
Compliance framework for Agent Factory Platform.

Supports SOC 2, GDPR, and other compliance requirements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ComplianceStandard(str, Enum):
    """Compliance standards."""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"


@dataclass
class ComplianceControl:
    """Compliance control."""
    id: str
    name: str
    description: str
    standard: ComplianceStandard
    category: str
    requirements: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    last_assessed: datetime | None = None
    notes: str = ""


@dataclass
class ComplianceAssessment:
    """Compliance assessment."""
    id: str
    standard: ComplianceStandard
    assessed_at: datetime
    assessed_by: str
    controls: list[ComplianceControl]
    overall_status: ComplianceStatus
    notes: str = ""


class ComplianceFramework:
    """
    Manages compliance framework.
    
    Example:
        >>> framework = ComplianceFramework()
        >>> control = framework.create_control(
        ...     name="Access Control",
        ...     standard=ComplianceStandard.SOC2,
        ...     category="Security"
        ... )
        >>> assessment = framework.assess_compliance(ComplianceStandard.SOC2)
    """
    
    def __init__(self):
        """Initialize compliance framework."""
        self.controls: dict[str, ComplianceControl] = {}
        self.assessments: list[ComplianceAssessment] = []
        self._initialize_default_controls()
    
    def _initialize_default_controls(self) -> None:
        """Initialize default compliance controls."""
        # SOC 2 controls
        soc2_controls = [
            {
                "id": "soc2-cc1",
                "name": "Control Environment",
                "description": "The entity demonstrates a commitment to integrity and ethical values.",
                "standard": ComplianceStandard.SOC2,
                "category": "Control Environment",
            },
            {
                "id": "soc2-cc2",
                "name": "Communication and Information",
                "description": "The entity obtains or generates and uses relevant information.",
                "standard": ComplianceStandard.SOC2,
                "category": "Communication",
            },
            {
                "id": "soc2-cc3",
                "name": "Risk Assessment",
                "description": "The entity identifies risks to achievement of objectives.",
                "standard": ComplianceStandard.SOC2,
                "category": "Risk Management",
            },
            {
                "id": "soc2-cc4",
                "name": "Monitoring Activities",
                "description": "The entity selects and develops control activities.",
                "standard": ComplianceStandard.SOC2,
                "category": "Monitoring",
            },
            {
                "id": "soc2-cc5",
                "name": "Control Activities",
                "description": "The entity deploys control activities through policies and procedures.",
                "standard": ComplianceStandard.SOC2,
                "category": "Control Activities",
            },
        ]
        
        # GDPR controls
        gdpr_controls = [
            {
                "id": "gdpr-1",
                "name": "Data Minimization",
                "description": "Personal data shall be adequate, relevant, and limited.",
                "standard": ComplianceStandard.GDPR,
                "category": "Data Protection",
            },
            {
                "id": "gdpr-2",
                "name": "Right to Erasure",
                "description": "Data subjects have the right to erasure of personal data.",
                "standard": ComplianceStandard.GDPR,
                "category": "Data Subject Rights",
            },
            {
                "id": "gdpr-3",
                "name": "Data Portability",
                "description": "Data subjects have the right to data portability.",
                "standard": ComplianceStandard.GDPR,
                "category": "Data Subject Rights",
            },
            {
                "id": "gdpr-4",
                "name": "Privacy by Design",
                "description": "Data protection by design and by default.",
                "standard": ComplianceStandard.GDPR,
                "category": "Privacy",
            },
        ]
        
        for control_data in soc2_controls + gdpr_controls:
            control = ComplianceControl(**control_data)  # type: ignore[arg-type]
            self.controls[control.id] = control
    
    def create_control(
        self,
        name: str,
        description: str,
        standard: ComplianceStandard,
        category: str,
        requirements: list[str] | None = None,
    ) -> ComplianceControl:
        """
        Create a compliance control.
        
        Args:
            name: Control name
            description: Control description
            standard: Compliance standard
            category: Control category
            requirements: List of requirements
            
        Returns:
            Created control
        """
        import uuid
        control_id = str(uuid.uuid4())
        
        control = ComplianceControl(
            id=control_id,
            name=name,
            description=description,
            standard=standard,
            category=category,
            requirements=requirements or [],
        )
        
        self.controls[control_id] = control
        return control
    
    def assess_control(
        self,
        control_id: str,
        status: ComplianceStatus,
        evidence: list[str] | None = None,
        notes: str = "",
    ) -> None:
        """
        Assess a compliance control.
        
        Args:
            control_id: Control ID
            status: Compliance status
            evidence: List of evidence
            notes: Assessment notes
        """
        control = self.controls.get(control_id)
        if not control:
            raise ValueError(f"Control not found: {control_id}")
        
        control.status = status
        control.last_assessed = datetime.utcnow()
        control.evidence = evidence or []
        control.notes = notes
    
    def assess_compliance(
        self,
        standard: ComplianceStandard,
        assessed_by: str,
        notes: str = "",
    ) -> ComplianceAssessment:
        """
        Assess compliance for a standard.
        
        Args:
            standard: Compliance standard
            assessed_by: Assessor identifier
            notes: Assessment notes
            
        Returns:
            Compliance assessment
        """
        import uuid
        assessment_id = str(uuid.uuid4())
        
        # Get controls for standard
        standard_controls = [
            c for c in self.controls.values()
            if c.standard == standard
        ]
        
        # Determine overall status
        compliant_count = sum(
            1 for c in standard_controls
            if c.status == ComplianceStatus.COMPLIANT
        )
        total_count = len(standard_controls)
        
        if compliant_count == total_count:
            overall_status = ComplianceStatus.COMPLIANT
        elif compliant_count == 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        else:
            overall_status = ComplianceStatus.PARTIAL
        
        assessment = ComplianceAssessment(
            id=assessment_id,
            standard=standard,
            assessed_at=datetime.utcnow(),
            assessed_by=assessed_by,
            controls=standard_controls,
            overall_status=overall_status,
            notes=notes,
        )
        
        self.assessments.append(assessment)
        return assessment
    
    def get_compliance_status(self, standard: ComplianceStandard) -> dict[str, Any]:
        """
        Get compliance status for a standard.
        
        Args:
            standard: Compliance standard
            
        Returns:
            Status dictionary
        """
        controls = [
            c for c in self.controls.values()
            if c.standard == standard
        ]
        
        status_counts = {
            ComplianceStatus.COMPLIANT: 0,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.PARTIAL: 0,
            ComplianceStatus.NOT_ASSESSED: 0,
        }
        
        for control in controls:
            status_counts[control.status] += 1
        
        total = len(controls)
        compliance_percent = (
            (status_counts[ComplianceStatus.COMPLIANT] / total * 100)
            if total > 0
            else 0.0
        )
        
        # Get latest assessment
        latest_assessment = None
        for assessment in reversed(self.assessments):
            if assessment.standard == standard:
                latest_assessment = assessment
                break
        
        return {
            "standard": standard.value,
            "total_controls": total,
            "compliant": status_counts[ComplianceStatus.COMPLIANT],
            "non_compliant": status_counts[ComplianceStatus.NON_COMPLIANT],
            "partial": status_counts[ComplianceStatus.PARTIAL],
            "not_assessed": status_counts[ComplianceStatus.NOT_ASSESSED],
            "compliance_percent": compliance_percent,
            "latest_assessment": {
                "assessed_at": latest_assessment.assessed_at.isoformat() if latest_assessment else None,
                "assessed_by": latest_assessment.assessed_by if latest_assessment else None,
                "overall_status": latest_assessment.overall_status.value if latest_assessment else None,
            } if latest_assessment else None,
        }
    
    def list_controls(
        self,
        standard: ComplianceStandard | None = None,
        category: str | None = None,
    ) -> list[ComplianceControl]:
        """
        List compliance controls.
        
        Args:
            standard: Filter by standard
            category: Filter by category
            
        Returns:
            List of controls
        """
        controls = list(self.controls.values())
        
        if standard:
            controls = [c for c in controls if c.standard == standard]
        
        if category:
            controls = [c for c in controls if c.category == category]
        
        return controls


# Global instance
_compliance_framework: ComplianceFramework | None = None


def get_compliance_framework() -> ComplianceFramework:
    """Get global compliance framework instance."""
    global _compliance_framework
    if _compliance_framework is None:
        _compliance_framework = ComplianceFramework()
    return _compliance_framework
