"""
Orchestrator Voice Module - Usage Examples

Demonstrates how to integrate voice announcements into task orchestration workflows.

Run this file to see all announcement types in action:
    python orchestrator_voice_example.py

For silent mode (no audio generation):
    VOICE_ENABLED=false python orchestrator_voice_example.py
"""

import os
from orchestrator_voice import (
    announce_agent_deployment,
    announce_tdd_phase,
    announce_test_results,
    announce_validation_summary,
    announce_completion
)


def example_basic_announcements():
    """Basic usage examples for all announcement types."""
    print("=" * 60)
    print("BASIC ANNOUNCEMENTS")
    print("=" * 60)

    # 1. Agent Deployment
    print("\n1. Agent Deployment Announcement:")
    path = announce_agent_deployment("feature-implementation", "1.2.3")
    print(f"   Generated: {path}")

    # 2. TDD Phase Announcements
    print("\n2. TDD Phase Announcements:")
    for phase in ["RED", "GREEN", "REFACTOR"]:
        path = announce_tdd_phase(phase, "2.1")
        print(f"   {phase}: {path}")

    # 3. Test Results
    print("\n3. Test Results Announcements:")
    path = announce_test_results(18, 0, "2.3")
    print(f"   All passing: {path}")
    path = announce_test_results(15, 3, "2.4")
    print(f"   Some failing: {path}")

    # 4. Validation Summary
    print("\n4. Validation Summary:")
    details = {
        "tests_passed": True,
        "implementation_complete": True,
        "documentation_updated": True
    }
    path = announce_validation_summary("complete", details)
    print(f"   Validation: {path}")

    # 5. Task Completion
    print("\n5. Task Completion:")
    deliverables = [
        "test_orchestrator_voice.py",
        "orchestrator_voice.py",
        "ORCHESTRATOR_VOICE_README.md"
    ]
    path = announce_completion("3.1", deliverables)
    print(f"   Completion: {path}")


def example_tdd_workflow():
    """Example of TDD workflow with voice announcements."""
    print("\n" + "=" * 60)
    print("TDD WORKFLOW SIMULATION")
    print("=" * 60)

    task_id = "4.2"

    # Deploy agent
    print("\n[Step 1] Deploying agent...")
    announce_agent_deployment("feature-implementation", task_id)

    # RED phase
    print("\n[Step 2] RED phase - Writing tests...")
    announce_tdd_phase("RED", task_id)
    announce_test_results(0, 5, task_id)  # Tests fail initially

    # GREEN phase
    print("\n[Step 3] GREEN phase - Implementing code...")
    announce_tdd_phase("GREEN", task_id)
    announce_test_results(5, 0, task_id)  # Tests now pass

    # REFACTOR phase
    print("\n[Step 4] REFACTOR phase - Optimizing...")
    announce_tdd_phase("REFACTOR", task_id)
    announce_test_results(5, 0, task_id)  # Tests still pass

    # Validation
    print("\n[Step 5] Validating deliverables...")
    validation_details = {
        "tests_passing": True,
        "code_quality": True,
        "documentation": True
    }
    announce_validation_summary("complete", validation_details)

    # Completion
    print("\n[Step 6] Task complete!")
    deliverables = ["module.py", "test_module.py", "README.md"]
    announce_completion(task_id, deliverables)


def example_multi_agent_coordination():
    """Example of coordinating multiple agents."""
    print("\n" + "=" * 60)
    print("MULTI-AGENT COORDINATION")
    print("=" * 60)

    agents = [
        ("research-agent", "5.1"),
        ("feature-implementation", "5.2"),
        ("testing-validation", "5.3"),
        ("documentation-generator", "5.4")
    ]

    print("\nDeploying agents in sequence:")
    for agent_name, task_id in agents:
        path = announce_agent_deployment(agent_name, task_id)
        print(f"  - {agent_name}: {path}")

    print("\nReporting results:")
    for agent_name, task_id in agents:
        path = announce_completion(task_id, [f"{agent_name}_output.json"])
        print(f"  - Task {task_id}: {path}")


def example_test_failure_recovery():
    """Example of handling test failures and recovery."""
    print("\n" + "=" * 60)
    print("TEST FAILURE RECOVERY")
    print("=" * 60)

    task_id = "6.1"

    # Initial test run with failures
    print("\n[Attempt 1] Initial test run:")
    announce_test_results(3, 7, task_id)

    # Fixing issues
    print("\n[Attempt 2] After bug fixes:")
    announce_test_results(8, 2, task_id)

    # Final success
    print("\n[Attempt 3] All issues resolved:")
    announce_test_results(10, 0, task_id)

    # Validation
    validation = {
        "tests_passing": True,
        "code_review": True,
        "performance": True
    }
    announce_validation_summary("complete", validation)


def example_conditional_announcements():
    """Example of conditional announcement logic."""
    print("\n" + "=" * 60)
    print("CONDITIONAL ANNOUNCEMENTS")
    print("=" * 60)

    task_id = "7.1"
    passed_tests = 15
    failed_tests = 3

    # Only announce if there are failures
    if failed_tests > 0:
        print(f"\nAnnouncing test failures:")
        path = announce_test_results(passed_tests, failed_tests, task_id)
        print(f"  Audio path: {path}")
    else:
        print("\nAll tests passing - silent success mode")

    # Only announce significant milestones
    total_tests = passed_tests + failed_tests
    if total_tests >= 10:
        print(f"\nMilestone: {total_tests} tests in suite")
        announce_validation_summary("milestone", {"test_count": total_tests})


def example_voice_disabled():
    """Example with voice disabled (testing mode)."""
    print("\n" + "=" * 60)
    print("VOICE DISABLED MODE (TESTING)")
    print("=" * 60)

    # Save current state
    original_value = os.environ.get("VOICE_ENABLED")

    # Temporarily disable voice
    os.environ["VOICE_ENABLED"] = "false"

    print("\nAll announcements should return None:")
    path1 = announce_agent_deployment("test-agent", "8.1")
    path2 = announce_tdd_phase("RED", "8.2")
    path3 = announce_test_results(5, 0, "8.3")

    print(f"  Agent deployment: {path1}")
    print(f"  TDD phase: {path2}")
    print(f"  Test results: {path3}")

    # Restore original value
    if original_value is not None:
        os.environ["VOICE_ENABLED"] = original_value
    else:
        del os.environ["VOICE_ENABLED"]


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ORCHESTRATOR VOICE MODULE - USAGE EXAMPLES")
    print("=" * 60)

    voice_status = os.environ.get("VOICE_ENABLED", "true")
    print(f"\nVoice Status: {voice_status}")
    print("(Set VOICE_ENABLED=false to disable audio generation)")

    # Run all examples
    example_basic_announcements()
    example_tdd_workflow()
    example_multi_agent_coordination()
    example_test_failure_recovery()
    example_conditional_announcements()
    example_voice_disabled()

    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
