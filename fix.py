import dataclasses
from typing import Dict
from dataclasses import dataclass

@dataclass
class MosslandIdeaScorecard:
    idea_title: str
    core_analysis: str
    opportunity_risk: str
    auto_scores: Dict[str, float]
    debate_topic: str
    debate_session: str
    decision: str

    def _derive_average(self) -> float:
        values = list(self.auto_scores.values())
        return sum(values) / len(values) if values else 0.0

    def evaluate_status(self) -> str:
        total = self.auto_scores.get('Total_Score', 0.0)
        current = self.decision

        if current == 'PENDING' and total >= 8.0:
            return 'APPROVED'
        if current == 'PENDING' and total < 6.0:
            return 'FOR_REVIEW'
        return current

    def generate_output(self) -> str:
        avg = self._derive_average()
        final = self.evaluate_status()
        
        lines = [
            "=== MOSSLAND IDEA ANALYSIS ===",
            f"Idea: {self.idea_title}",
            f"Debate: {self.debate_session}",
            f"Topic: {self.debate_topic}",
            "---",
            "Scores:"
        ]
        
        for key, val in self.auto_scores.items():
            lines.append(f"  {key}: {val}")
        
        lines.extend([
            "---",
            f"Derived Avg: {avg:.1f}",
            f"Final Status: {final}",
            "============================="
        ])
        
        return "\n".join(lines)

def main():
    score_data = {
        'Total_Score': 8.0,
        'Feasibility': 8.0,
        'Relevance': 9.0,
        'Novelty': 7.0,
        'Impact': 8.0
    }

    idea = MosslandIdeaScorecard(
        idea_title="zk-SNARK Proof-Carrying Event Access Passes for Mossland Community Drops and Private Campaign Reward",
        core_analysis="Ethereum privacy narrative shifting from speculative to product requirement. Controlled access proves eligibility without identity leakage.",
        opportunity_risk="Privacy infrastructure solves expensive coordination. Targets community rewards, whitelists, and event gating.",
        auto_scores=score_data,
        debate_topic="[CRYPTO] Ethereum Hegotá Upgrade Drives Increased Interest in Native Privacy Solutions within Web3 Ecosystems",
        debate_session="4cf2e171",
        decision="PENDING"
    )

    print(idea.generate_output())

if __name__ == '__main__':
    main()