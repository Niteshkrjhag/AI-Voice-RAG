"""
q2_knowledge_base/seed.py — Generates realistic health insurance seed data

Simulates scraped content for the knowledge base assessment.
Includes:
  - Product marketing content
  - Policy/qualification rules
  - Duplicate material (to test dedup)
  - Inconsistent terminology (to test normalization)
  - PII (to test redaction)
  - Boilerplate (to test cleaning)
"""

import json
from pathlib import Path

from shared.config import config
from shared.logger import get_logger

log = get_logger("q2.seed")

# Raw mock documents containing the required anomalies
SEED_DOCUMENTS = [
    {
        "url": "https://health-shield.inc/products/premium-care",
        "title": "Premium Care Health Insurance | Health Shield",
        "markdown": """
        # Premium Care Health Insurance
        
        Copyright 2026 Health Shield Inc. All rights reserved.
        Home | About | Contact | Privacy Policy
        
        Our Premium Care plan offers comprehensive coverage for your entire family.
        The SA (Sum Assured) ranges from ₹10 Lakhs to ₹1 Crore.
        
        ## Key Benefits
        - **No Claim Bonus (NCB):** Get 50% extra coverage for every claim-free year, up to 100%.
        - **PED Coverage:** All pre-existing diseases are covered after a 2-year waiting period.
        - **Day Care:** Covers 500+ day care procedures.
        
        ## Qualification Rules
        - Entry age: 18 to 65 years.
        - Dependent children: 91 days to 25 years.
        - Mandatory medical checkup for applicants over 55 years.
        
        Contact John Doe at john.doe@healthshield.com or call +91-9876543210 for sales.
        """,
        "success": True,
    },
    {
        "url": "https://health-shield.inc/support/faq",
        "title": "Frequently Asked Questions",
        "markdown": """
        # Support and FAQs
        
        Privacy Policy | Terms of Service
        
        ### What is the waiting period for PED?
        For our standard policies, the waiting period for a pre-existing disease (PED) is 3 years. For the Premium Care plan, it is reduced to 2 years.
        
        ### Do I have to pay a co-pay?
        There is no co-pay if you receive treatment within our network hospitals. However, a 10% co-payment applies if you choose an out-of-network facility or if you are above 60 years of age at the time of policy purchase.
        
        ### How do I file a claim?
        Contact our TPA desk at the hospital for cashless claims. Ensure you carry your health card and a valid Govt ID (e.g., Aadhaar 1234 5678 9012 - FOR DEMO ONLY).
        """,
        "success": True,
    },
    {
        "url": "https://health-shield.inc/blog/understanding-ncb",
        "title": "Understanding Your No Claim Bonus",
        "markdown": """
        # Understanding Your No Claim Bonus
        
        Subscribe to our Newsletter | Follow us on Twitter
        
        A No Claim Bonus (NCB) is a reward given to policyholders for not making any claims during the policy year. 
        It effectively increases your health ins coverage without increasing your premium. 
        For instance, in our Premium Care plan, your SI (Sum Insured) goes up by 50% for every claim-free year!
        
        Share on Facebook | Tweet this
        """,
        "success": True,
    },
    {
        # Near-duplicate of the first document to test deduplication
        "url": "https://health-shield.inc/campaigns/premium-care-promo",
        "title": "Premium Care Promo 2026",
        "markdown": """
        # Premium Care Health Insurance (Promo)
        
        Our Premium Care plan offers comprehensive coverage for your family.
        The SA ranges from ₹10 Lakhs to ₹1 Crore.
        
        ## Key Benefits
        - **NCB:** Get 50% extra coverage for every claim-free year, up to 100%.
        - **PED Coverage:** Pre-existing diseases are covered after a 2-year waiting period.
        - **Day Care:** Covers 500+ day care procedures.
        
        ## Qualification Rules
        - Entry age: 18 to 65 years.
        - Dependent children: 91 days to 25 years.
        - Mandatory medical checkup for applicants over 55 years.
        
        Call our sales agent Ravi at +91 9988776655.
        """,
        "success": True,
    }
]


def generate_seed_data():
    """Write seed documents to the raw data directory."""
    raw_dir = config.DATA_RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    for doc in SEED_DOCUMENTS:
        safe_name = doc["url"].replace("https://", "").replace("http://", "")
        safe_name = safe_name.replace("/", "_").replace(".", "_")[:100]
        filepath = raw_dir / f"{safe_name}.json"
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        saved_count += 1
            
    log.info("seed_data_generated", count=saved_count, directory=str(raw_dir))


if __name__ == "__main__":
    generate_seed_data()
    print(f"Generated {len(SEED_DOCUMENTS)} seed documents in {config.DATA_RAW_DIR}")
