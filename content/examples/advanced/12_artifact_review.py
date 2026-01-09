"""Example: Artifact review and approval workflow.

This example demonstrates:
1. Creating review requests for artifacts
2. Risk assessment
3. Approval/rejection workflow
4. Review statistics
"""

import asyncio

from paracle_review import ReviewConfig, ReviewManager, ReviewPolicy


async def main():
    """Run artifact review example."""
    print("=== Artifact Review Workflow Example ===\n")

    # Create review manager with policy
    config = ReviewConfig(
        policy=ReviewPolicy(
            enabled=True,
            trigger_mode="high_risk_only",
            high_risk_patterns=["*.env", "*.key", "/etc/*", "rm -rf"],
            auto_approve_low_risk=True,
            min_approvals=2,  # Require 2 approvals
        )
    )
    manager = ReviewManager(config)

    # 1. Create low-risk review (auto-approved)
    print("1. Creating low-risk artifact review...")
    review1_id = await manager.create_review(
        artifact_id="file-001",
        artifact_type="file_change",
        sandbox_id="sandbox-123",
        artifact_content={
            "path": "/workspace/data.txt",
            "operation": "write",
            "content": "some data",
        },
    )
    review1 = await manager.get_review(review1_id)
    print(f"   Review ID: {review1_id}")
    print(f"   Risk Level: {review1.risk_level}")
    print(f"   Status: {review1.status.value}")
    if review1.status.value == "approved":
        print("   ✓ Auto-approved (low risk)")

    # 2. Create high-risk review (requires approval)
    print("\n2. Creating high-risk artifact review...")
    review2_id = await manager.create_review(
        artifact_id="file-002",
        artifact_type="file_change",
        sandbox_id="sandbox-123",
        artifact_content={
            "path": "/etc/hosts",
            "operation": "write",
            "content": "127.0.0.1 malicious.com",
        },
    )
    review2 = await manager.get_review(review2_id)
    print(f"   Review ID: {review2_id}")
    print(f"   Risk Level: {review2.risk_level}")
    print(f"   Status: {review2.status.value}")
    print(f"   Required approvals: {review2.required_approvals}")

    # 3. First approval
    print("\n3. First reviewer approving...")
    await manager.approve(
        review2_id,
        reviewer="alice@example.com",
        comment="Verified change is needed for testing",
    )
    review2 = await manager.get_review(review2_id)
    print(f"   Approvals: {review2.approval_count()}/{review2.required_approvals}")
    print(f"   Status: {review2.status.value}")

    # 4. Second approval
    print("\n4. Second reviewer approving...")
    await manager.approve(review2_id, reviewer="bob@example.com", comment="Looks good")
    review2 = await manager.get_review(review2_id)
    print(f"   Approvals: {review2.approval_count()}/{review2.required_approvals}")
    print(f"   Status: {review2.status.value}")
    print("   ✓ Fully approved!")

    # 5. Create review to reject
    print("\n5. Creating review for rejection...")
    review3_id = await manager.create_review(
        artifact_id="file-003",
        artifact_type="command_execution",
        sandbox_id="sandbox-123",
        artifact_content={
            "command": "rm -rf /data",
            "operation": "execute",
        },
    )
    review3 = await manager.get_review(review3_id)
    print(f"   Review ID: {review3_id}")
    print(f"   Risk Level: {review3.risk_level}")

    # 6. Reject review
    print("\n6. Reviewer rejecting...")
    await manager.reject(
        review3_id,
        reviewer="charlie@example.com",
        comment="Too dangerous - deletes all data",
    )
    review3 = await manager.get_review(review3_id)
    print(f"   Status: {review3.status.value}")
    print("   ✗ Rejected!")

    # 7. List all reviews
    print("\n7. All reviews:")
    all_reviews = manager.list_reviews()
    for review in all_reviews:
        print(
            f"   - {review.review_id}: {review.artifact_type} "
            f"({review.risk_level} risk) → {review.status.value}"
        )

    # 8. List pending reviews
    print("\n8. Pending reviews:")
    pending = manager.get_pending_count()
    print(f"   Count: {pending}")

    # 9. Statistics
    print("\n9. Review statistics:")
    all_reviews = manager.list_reviews()
    print(f"   Total: {len(all_reviews)}")
    print(f"   Approved: {sum(1 for r in all_reviews if r.status.value == 'approved')}")
    print(f"   Rejected: {sum(1 for r in all_reviews if r.status.value == 'rejected')}")
    print(f"   Pending: {sum(1 for r in all_reviews if r.status.value == 'pending')}")

    # 10. Review decisions
    print("\n10. Review decision history:")
    review2 = await manager.get_review(review2_id)
    for i, decision in enumerate(review2.decisions, 1):
        print(f"   {i}. {decision.reviewer}: {decision.decision}")
        if decision.comment:
            print(f"      Comment: {decision.comment}")

    print("\n✓ Review workflow complete")


if __name__ == "__main__":
    asyncio.run(main())
