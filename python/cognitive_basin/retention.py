"""
Retention decisions for governed memory items.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .memory.contracts import MemoryRetentionDecision
from .privacy import RetentionClass

if TYPE_CHECKING:
    from .memory.contracts import MemoryItem


def decide_retention(item: "MemoryItem") -> MemoryRetentionDecision:
    if item.contradiction_status == "contradicted":
        return MemoryRetentionDecision(
            decision="demote",
            reason="Active contradiction blocks promotion",
            retention_class=RetentionClass.REVIEW_REQUIRED,
            visibility_scope=item.visibility_scope,
            timestamp=time.time(),
        )
    if item.failed_uses and not item.successful_uses:
        return MemoryRetentionDecision(
            decision="demote",
            reason="Failed use without verified recovery",
            retention_class=RetentionClass.REVIEW_REQUIRED,
            visibility_scope=item.visibility_scope,
            timestamp=time.time(),
        )
    if (
        len(item.successful_uses) >= 2
        or (item.replay_references and item.evidence_status == "supported")
        or len(item.evidence_links) >= 2
    ):
        return MemoryRetentionDecision(
            decision="promote",
            reason="Verified usefulness, replay survival, or strong evidence supports retention",
            retention_class=RetentionClass.SHARED_WORKING
            if item.visibility_scope.name in {"SHARED_PROJECT", "EXPORTABLE_REDACTED", "AUDIT_RETAINED"}
            else RetentionClass.PRIVATE_WORKING,
            visibility_scope=item.visibility_scope,
            timestamp=time.time(),
        )
    return MemoryRetentionDecision(
        decision="retain",
        reason="Working memory retained pending stronger promotion or demotion evidence",
        retention_class=item.retention_class,
        visibility_scope=item.visibility_scope,
        timestamp=time.time(),
    )
