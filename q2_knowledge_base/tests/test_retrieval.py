"""
q2_knowledge_base/tests/test_retrieval.py — Evaluates retrieval accuracy

Runs 5 specific queries against the knowledge base to test semantic search.
Assessments requirement:
- 5 queries (product, policy, qualification, FAQ, objection).
- Show user question, retrieved chunk, source reference, and verdict.
"""

import asyncio

from q2_knowledge_base.retriever import search_knowledge_base


QUERIES = [
    {
        "type": "Product",
        "question": "What is the maximum sum insured for the Premium Care plan?",
        "expected_topic": "Sum Assured up to ₹1 Crore",
    },
    {
        "type": "Policy/FAQ",
        "question": "Do I have to pay any co-pay if I go to an out-of-network hospital?",
        "expected_topic": "10% co-payment applies for out-of-network",
    },
    {
        "type": "Qualification",
        "question": "My father is 62 years old, can he buy this policy?",
        "expected_topic": "Entry age 18 to 65 years. Medical checkup required over 55.",
    },
    {
        "type": "Objection",
        "question": "But I heard pre-existing diseases take 4 years to cover!",
        "expected_topic": "PED waiting period is 2 years for Premium Care (3 years for standard).",
    },
    {
        "type": "FAQ/Rules",
        "question": "How does the No Claim Bonus work?",
        "expected_topic": "50% extra coverage for claim-free year, up to 100%.",
    },
]


async def run_evaluations():
    print("=" * 80)
    print("KNOWLEDGE BASE RETRIEVAL EVALUATION (5 QUERIES)")
    print("=" * 80)

    for q in QUERIES:
        print(f"\n[QUERY: {q['type']}]")
        print(f"Q: {q['question']}")
        
        # We limit to top 1 result for strict evaluation
        results = await search_knowledge_base(q["question"], limit=1)
        
        if not results:
            print("❌ RETRIEVED: None")
            print("VERDICT: Incorrect (No results)")
            continue
            
        best_hit = results[0]
        
        print(f"✅ RETRIEVED (Source: {best_hit.metadata.source_url})")
        print(f"--- Chunk Content ---")
        print(best_hit.content.strip())
        print(f"---------------------")
        print(f"Expected Topic: {q['expected_topic']}")
        print("Verdict: [PENDING MANUAL REVIEW - Correct / Partially Correct / Incorrect]")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_evaluations())
