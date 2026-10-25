"""Phase 1 Runner: Temporal + Gemma 4 SRE Remediation Pipeline.

Executes Phase 1:
- Initializes target service
- Runs baseline test verification
- Runs Gemma 4 Security Reasoning & Grounding
- Transitions Temporal State Machine to PAUSED (Awaiting Review)
- Hands off artifacts to Kepler SRE AI IDE
"""
import os
import sys
import subprocess
from engine.temporal_workflow import DependencyRemediationWorkflow


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 70)
    print("[*] STARTING PHASE 1: TEMPORAL ORCHESTRATION + GEMMA 4 REASONING")
    print("=" * 70)

    # 1. Start Temporal Workflow
    workflow = DependencyRemediationWorkflow(root_dir)
    handoff = workflow.start_phase_1()

    # 2. Display Next Steps for Kepler
    print("\n" + "#" * 70)
    print("[+] PHASE 1 COMPLETE -> HANDING OFF TO KEPLER AI IDE")
    print("#" * 70)
    print("\nTemporal has safely paused in state: [PAUSED: AWAITING REVIEW]")
    print("Artifacts ready for Kepler:")
    print("  - Upgraded Manifest : upgraded_requirements.txt")
    print("  - Security Advisory  : gemma_advisory.json")
    print("  - Kepler Handoff     : .kepler/kepler_handoff.json")
    print("  - Prompt Guide       : .kepler/kepler_prompt.md")
    print("\n>>> YOU ARE NOW READY FOR KEPLER! Let me know when you open your Kepler app.")
    print("=" * 70)


if __name__ == "__main__":
    main()
