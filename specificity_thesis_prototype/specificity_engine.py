"""
Specificity Thesis Prototype Implementation
Version 0.1 - Working Draft

This module implements the core metrics and governance mechanisms
described in the Specificity Thesis for history-bearing intelligent systems.

Key Components:
- Specificity measurement (GSR/NGR)
- Structural Debt Potential (SDP) calculation
- Governance triggers (HOLD/RETRACT)
- Modularity detection
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class GovernanceState(Enum):
    """System governance states based on SDP thresholds."""
    OPERATIONAL = "operational"
    CAUTION = "caution"
    HOLD = "hold"
    RETRACT = "retract"
    COLLAPSE = "collapse"


@dataclass
class SpecificityDimensions:
    """
    Target-relevant dimensions that must be preserved for high specificity.
    
    These dimensions define what information must be retained to avoid
    accumulating Structural Debt Potential.
    """
    provenance_chain: List[str] = field(default_factory=list)
    contradiction_history: List[Dict[str, Any]] = field(default_factory=list)
    developmental_path: List[Dict[str, Any]] = field(default_factory=list)
    energetic_cost: float = 0.0
    alternative_paths_not_taken: List[Dict[str, Any]] = field(default_factory=list)
    timing_metadata: Dict[str, Any] = field(default_factory=dict)
    non_geometric_residue: float = 0.0
    
    def to_vector(self) -> np.ndarray:
        """Convert dimensions to a numerical vector for comparison."""
        # Simplified vectorization - in practice, this would be more sophisticated
        vector = [
            len(self.provenance_chain),
            len(self.contradiction_history),
            len(self.developmental_path),
            self.energetic_cost,
            len(self.alternative_paths_not_taken),
            self.non_geometric_residue
        ]
        return np.array(vector)


@dataclass
class Representation:
    """
    A representation or memory within the system.
    
    Contains both the geometric/compressed form and the full developmental record
    for GSR/NGR calculation.
    """
    id: str
    geometric_form: Any  # The compressed/geometric representation
    full_record: SpecificityDimensions  # The complete developmental history
    target_dimensions: List[str]  # Which dimensions are relevant for this target
    created_at: int = 0
    last_accessed: int = 0
    
    def get_target_vector(self) -> np.ndarray:
        """Extract only the target-relevant dimensions from full record."""
        full_vector = self.full_record.to_vector()
        # In practice, this would select specific indices based on target_dimensions
        return full_vector[:len(self.target_dimensions)]


@dataclass
class SDPComponents:
    """Components of Structural Debt Potential."""
    discrepancy_deferred_debt: float = 0.0  # D_d functional
    scar_load: float = 0.0  # Cognitive morphology metric
    coercivity: float = 0.0
    remanence: float = 0.0
    branching_burden: float = 0.0
    hold_fog: float = 0.0
    sera_waste_channel: float = 0.0
    ngr_applied: float = 0.0  # Non-Geometric Residue from Ageometrics
    
    def total(self) -> float:
        """Calculate total SDP from components."""
        return (
            self.discrepancy_deferred_debt * 1.0 +
            self.scar_load * 0.8 +
            self.coercivity * 0.6 +
            self.remanence * 0.5 +
            self.branching_burden * 0.7 +
            self.hold_fog * 0.4 +
            self.sera_waste_channel * 0.9 +
            self.ngr_applied * 1.2  # NGR has higher weight per thesis
        )


class SpecificityThesisEngine:
    """
    Core engine for measuring specificity and managing structural debt.
    
    Implements the measurement, governance, and emergence corollaries
    from the Specificity Thesis.
    """
    
    def __init__(self, resolution_capacity: float = 1.0):
        """
        Initialize the engine.
        
        Args:
            resolution_capacity: System's capacity to resolve structural debt
                                (Integrity Gauge baseline)
        """
        self.resolution_capacity = resolution_capacity
        self.representations: Dict[str, Representation] = {}
        self.sdp_history: List[float] = []
        self.governance_state = GovernanceState.OPERATIONAL
        
    def register_representation(self, rep: Representation) -> None:
        """Register a new representation in the system."""
        self.representations[rep.id] = rep
        
    def calculate_gsr(self, representation: Representation) -> float:
        """
        Calculate Geometric Sufficiency Ratio (GSR).
        
        GSR quantifies the fraction of recoverable target-relevant value
        retained by the geometric representation versus the fuller record.
        
        Returns:
            GSR value between 0.0 (complete loss) and 1.0 (perfect retention)
        """
        # Simplified implementation - in practice, this would use sophisticated
        # comparison algorithms between geometric_form and full_record
        
        full_vector = representation.get_target_vector()
        
        # Simulate geometric form extraction (lossy compression)
        # In real implementation, this would extract from representation.geometric_form
        if len(full_vector) == 0:
            return 1.0
            
        # Add some noise to simulate lossiness
        noise_factor = np.random.uniform(0.05, 0.3)
        geometric_vector = full_vector * (1.0 - noise_factor)
        
        # Calculate similarity (simplified cosine similarity)
        norm_full = np.linalg.norm(full_vector)
        norm_geo = np.linalg.norm(geometric_vector)
        
        if norm_full == 0 or norm_geo == 0:
            return 1.0 if norm_full == norm_geo else 0.0
            
        similarity = np.dot(full_vector, geometric_vector) / (norm_full * norm_geo)
        
        return max(0.0, min(1.0, similarity))
    
    def calculate_ngr(self, representation: Representation) -> float:
        """
        Calculate Non-Geometric Residue (NGR).
        
        NGR = 1 - GSR, representing the measurable residue that must be
        explicitly carried or debt will accumulate.
        """
        gsr = self.calculate_gsr(representation)
        return 1.0 - gsr
    
    def calculate_sdp(self, representation: Representation) -> SDPComponents:
        """
        Calculate Structural Debt Potential components for a representation.
        
        This assembles SDP from discrepancy debt, cognitive morphology metrics,
        SERA waste channels, and Ageometrics NGR.
        """
        ngr = self.calculate_ngr(representation)
        
        # Calculate components based on representation characteristics
        dims = representation.full_record
        
        # Discrepancy/Deferred Debt (D_d) - based on contradiction history
        discrepancy_debt = len(dims.contradiction_history) * 0.15
        
        # Scar load - from contradiction scars
        scar_load = len(dims.contradiction_history) * 0.1
        
        # Coercivity - resistance to change based on entrenched paths
        coercivity = len(dims.developmental_path) * 0.05
        
        # Remanence - lingering effects of past states
        remanence = dims.energetic_cost * 0.02
        
        # Branching burden - complexity from alternatives not taken
        branching_burden = len(dims.alternative_paths_not_taken) * 0.08
        
        # HOLD fog - uncertainty from unresolved states
        hold_fog = 0.1 if len(dims.contradiction_history) > 0 else 0.0
        
        # SERA waste channel forecasting
        sera_waste = ngr * 0.3  # Waste proportional to NGR
        
        return SDPComponents(
            discrepancy_deferred_debt=discrepancy_debt,
            scar_load=scar_load,
            coercivity=coercivity,
            remanence=remanence,
            branching_burden=branching_burden,
            hold_fog=hold_fog,
            sera_waste_channel=sera_waste,
            ngr_applied=ngr
        )
    
    def update_governance_state(self) -> GovernanceState:
        """
        Update system governance state based on current SDP vs resolution capacity.
        
        Implements Corollary 2: When projected SDP rises faster than resolution
        capacity (Integrity Gauge drop), system defaults to HOLD or RETRACT.
        """
        if not self.representations:
            self.governance_state = GovernanceState.OPERATIONAL
            return self.governance_state
            
        # Calculate average SDP across all representations
        total_sdp = sum(
            self.calculate_sdp(rep).total() 
            for rep in self.representations.values()
        )
        avg_sdp = total_sdp / len(self.representations)
        
        self.sdp_history.append(avg_sdp)
        
        # Determine state based on SDP relative to resolution capacity
        sdp_ratio = avg_sdp / self.resolution_capacity
        
        if sdp_ratio < 0.3:
            self.governance_state = GovernanceState.OPERATIONAL
        elif sdp_ratio < 0.6:
            self.governance_state = GovernanceState.CAUTION
        elif sdp_ratio < 0.85:
            self.governance_state = GovernanceState.HOLD
        elif sdp_ratio < 1.2:
            self.governance_state = GovernanceState.RETRACT
        else:
            self.governance_state = GovernanceState.COLLAPSE
            
        return self.governance_state
    
    def detect_modularity(self, representations: List[Representation]) -> Dict[str, List[str]]:
        """
        Detect emergent modularity in representations.
        
        Implements Corollary 3: Modularity emerges spontaneously under
        specificity preservation pressure.
        
        Returns:
            Dictionary mapping module names to lists of representation IDs
        """
        if len(representations) < 2:
            return {"default": [r.id for r in representations]}
            
        # Simple clustering based on target dimensions
        modules: Dict[str, List[str]] = {}
        
        for rep in representations:
            # Create module key from target dimensions
            module_key = "_".join(sorted(rep.target_dimensions))
            
            if module_key not in modules:
                modules[module_key] = []
            modules[module_key].append(rep.id)
            
        return modules
    
    def process_interference_test(
        self, 
        domain_a_reps: List[Representation],
        domain_b_reps: List[Representation]
    ) -> Dict[str, float]:
        """
        Test for processing and learning interference between domains.
        
        Implements the Interference Argument from Section 3.
        
        Returns:
            Dictionary with interference metrics
        """
        # Calculate within-domain overlap
        def calc_overlap(reps: List[Representation]) -> float:
            if len(reps) < 2:
                return 0.0
            vectors = [r.get_target_vector() for r in reps]
            overlaps = []
            for i in range(len(vectors)):
                for j in range(i+1, len(vectors)):
                    sim = np.corrcoef(vectors[i], vectors[j])[0, 1]
                    if not np.isnan(sim):
                        overlaps.append(abs(sim))
            return np.mean(overlaps) if overlaps else 0.0
            
        within_a = calc_overlap(domain_a_reps)
        within_b = calc_overlap(domain_b_reps)
        
        # Calculate cross-domain overlap
        cross_overlaps = []
        for rep_a in domain_a_reps:
            for rep_b in domain_b_reps:
                vec_a = rep_a.get_target_vector()
                vec_b = rep_b.get_target_vector()
                if len(vec_a) == len(vec_b):
                    sim = np.corrcoef(vec_a, vec_b)[0, 1]
                    if not np.isnan(sim):
                        cross_overlaps.append(abs(sim))
                        
        cross_domain = np.mean(cross_overlaps) if cross_overlaps else 0.0
        
        return {
            "within_domain_a_overlap": within_a,
            "within_domain_b_overlap": within_b,
            "cross_domain_overlap": cross_domain,
            "modularity_ratio": (within_a + within_b) / (2 * cross_domain) if cross_domain > 0 else float('inf')
        }


def demo_specificity_thesis():
    """Demonstrate the Specificity Thesis prototype."""
    print("=" * 70)
    print("SPECIFICITY THESIS PROTOTYPE DEMONSTRATION")
    print("=" * 70)
    
    # Initialize engine
    engine = SpecificityThesisEngine(resolution_capacity=1.0)
    
    # Create sample representations with varying specificity
    reps = []
    
    # High-specificity representation
    high_spec = Representation(
        id="high_spec_001",
        geometric_form={"compressed": True},
        full_record=SpecificityDimensions(
            provenance_chain=["source_a", "transform_1", "transform_2"],
            contradiction_history=[],
            developmental_path=[{"step": 1}, {"step": 2}, {"step": 3}],
            energetic_cost=0.5,
            alternative_paths_not_taken=[{"path": "alt_1"}],
            non_geometric_residue=0.1
        ),
        target_dimensions=["provenance", "development", "energy"],
        created_at=0
    )
    
    # Low-specificity representation
    low_spec = Representation(
        id="low_spec_001",
        geometric_form={"compressed": True},
        full_record=SpecificityDimensions(
            provenance_chain=["unknown"],
            contradiction_history=[{"contradiction": "unresolved_1"}, {"contradiction": "unresolved_2"}],
            developmental_path=[],
            energetic_cost=2.0,
            alternative_paths_not_taken=[],
            non_geometric_residue=0.7
        ),
        target_dimensions=["provenance", "development", "energy"],
        created_at=0
    )
    
    # Register representations
    engine.register_representation(high_spec)
    engine.register_representation(low_spec)
    reps.extend([high_spec, low_spec])
    
    # Calculate metrics
    print("\n1. GEOMETRIC SUFFICIENCY RATIO (GSR) & NON-GEOMETRIC RESIDUE (NGR)")
    print("-" * 70)
    for rep in reps:
        gsr = engine.calculate_gsr(rep)
        ngr = engine.calculate_ngr(rep)
        print(f"{rep.id}:")
        print(f"  GSR: {gsr:.3f} (target-relevant value retained)")
        print(f"  NGR: {ngr:.3f} (residue that must be carried)")
        
    print("\n2. STRUCTURAL DEBT POTENTIAL (SDP) ANALYSIS")
    print("-" * 70)
    for rep in reps:
        sdp = engine.calculate_sdp(rep)
        total_sdp = sdp.total()
        print(f"{rep.id}:")
        print(f"  Discrepancy Debt: {sdp.discrepancy_deferred_debt:.3f}")
        print(f"  Scar Load: {sdp.scar_load:.3f}")
        print(f"  NGR Applied: {sdp.ngr_applied:.3f}")
        print(f"  TOTAL SDP: {total_sdp:.3f}")
        
    print("\n3. GOVERNANCE STATE ASSESSMENT")
    print("-" * 70)
    state = engine.update_governance_state()
    print(f"Current Governance State: {state.value}")
    print(f"Resolution Capacity: {engine.resolution_capacity}")
    if engine.sdp_history:
        print(f"Average SDP: {engine.sdp_history[-1]:.3f}")
        print(f"SDP/Capacity Ratio: {engine.sdp_history[-1]/engine.resolution_capacity:.3f}")
        
    print("\n4. MODULARITY DETECTION (Corollary 3)")
    print("-" * 70)
    
    # Create domain-specific representations
    language_reps = [
        Representation(
            id=f"lang_{i}",
            geometric_form={},
            full_record=SpecificityDimensions(energetic_cost=0.1*i),
            target_dimensions=["language", "syntax"],
            created_at=i
        )
        for i in range(3)
    ]
    
    reasoning_reps = [
        Representation(
            id=f"reason_{i}",
            geometric_form={},
            full_record=SpecificityDimensions(energetic_cost=0.2*i),
            target_dimensions=["formal_reasoning", "logic"],
            created_at=i
        )
        for i in range(3)
    ]
    
    modules = engine.detect_modularity(language_reps + reasoning_reps)
    print(f"Detected {len(modules)} modules:")
    for module_name, rep_ids in modules.items():
        print(f"  {module_name}: {rep_ids}")
        
    print("\n5. INTERFERENCE TEST (Section 3)")
    print("-" * 70)
    interference = engine.process_interference_test(language_reps, reasoning_reps)
    print(f"Within-domain overlap (language): {interference['within_domain_a_overlap']:.3f}")
    print(f"Within-domain overlap (reasoning): {interference['within_domain_b_overlap']:.3f}")
    print(f"Cross-domain overlap: {interference['cross_domain_overlap']:.3f}")
    print(f"Modularity ratio: {interference['modularity_ratio']:.3f}")
    print("(Ratio > 1 indicates emergent modularity)")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Insights:")
    print("- Low specificity → High NGR → High SDP accumulation")
    print("- Governance triggers HOLD/RETRACT when SDP exceeds capacity")
    print("- Modularity emerges naturally to reduce interference")
    print("- Specificity is earned through complete developmental cycles")


if __name__ == "__main__":
    demo_specificity_thesis()
