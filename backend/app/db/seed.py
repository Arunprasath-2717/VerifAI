import random
from datetime import datetime, timedelta
from app.db.database import get_db_connection

MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
    {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic"},
    {"id": "llama-3.1-70b", "name": "Llama 3.1 70B", "provider": "Meta"},
    {"id": "qwen-2.5-72b", "name": "Qwen 2.5 72B", "provider": "Alibaba"},
    {"id": "mistral-large", "name": "Mistral Large", "provider": "Mistral AI"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "Google"}
]

DOMAINS = ["Healthcare", "Finance", "Legal", "Technology", "Science", "General Knowledge"]
VERDICTS = ["SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"]
EVIDENCE_STATUSES = ["SUPPORT", "CONTRADICT", "UNKNOWN"]
SIGNALS = ["entailment", "contradiction", "absent", "refused", "failed_judgment"]
SAMPLING_BASES = ["prompt_generation", "response_rewrite"]

def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM verifications")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("Seeding database with realistic verification & benchmark data...")

    # Seed Sources
    sources = [
        ("src-1", "https://pubmed.ncbi.nlm.nih.gov/articles", "Healthcare", 0.95),
        ("src-2", "https://finance.yahoo.com/news", "Finance", 0.88),
        ("src-3", "https://law.cornell.edu/statutes", "Legal", 0.92),
        ("src-4", "https://arxiv.org/abs/computer-science", "Technology", 0.90),
        ("src-5", "https://nature.com/articles", "Science", 0.96),
        ("src-6", "https://wikipedia.org/wiki", "General Knowledge", 0.75),
    ]
    for s in sources:
        cursor.execute(
            "INSERT INTO sources (id, url, domain, quality_score) VALUES (?, ?, ?, ?)",
            s
        )

    # Seed Verifications, Claims, Evidence, Consistency Results
    base_time = datetime.now() - timedelta(days=30)
    
    verification_count = 0
    for i in range(120):
        v_id = f"v-{i+1:04d}"
        model = random.choice(MODELS)
        domain = random.choice(DOMAINS)
        created_at = base_time + timedelta(hours=i*6, minutes=random.randint(0, 59))
        
        # Model run entry
        cursor.execute(
            "INSERT INTO model_runs (id, model_id, model_name, provider, token_count, latency_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"mr-{i+1:04d}", model["id"], model["name"], model["provider"], random.randint(150, 2400), random.randint(200, 1800), created_at.isoformat())
        )

        # Trust score varies slightly by model quality
        model_bias = {
            "gpt-4o": 0.88,
            "claude-3-5-sonnet": 0.90,
            "llama-3.1-70b": 0.82,
            "qwen-2.5-72b": 0.84,
            "mistral-large": 0.80,
            "gemini-1.5-pro": 0.86
        }.get(model["id"], 0.80)

        trust_score = round(min(1.0, max(0.2, random.normalvariate(model_bias, 0.1))), 3)

        cursor.execute(
            "INSERT INTO verifications (id, query, trust_score, status, domain, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (v_id, f"Verification query regarding {domain.lower()} research claim #{i+1}", trust_score, "COMPLETED", domain, model["id"], created_at.isoformat())
        )

        # Generate 1 to 4 claims per verification
        num_claims = random.randint(1, 4)
        for c_idx in range(num_claims):
            c_id = f"c-{i+1:04d}-{c_idx+1}"
            
            # Determine verdict based on trust_score
            verdict_rand = random.random()
            if verdict_rand < trust_score * 0.75:
                verdict = "SUPPORTED"
            elif verdict_rand < trust_score * 0.75 + (1 - trust_score) * 0.6:
                verdict = "CONTRADICTED"
            else:
                verdict = "INCONCLUSIVE"

            # 10% chance confidence is NULL (representing "No verification signal")
            if random.random() < 0.10:
                confidence = None
            else:
                confidence = round(min(0.99, max(0.35, random.normalvariate(0.82 if verdict == "SUPPORTED" else 0.65, 0.12))), 3)

            cursor.execute(
                "INSERT INTO claims (id, verification_id, claim_text, verdict, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (c_id, v_id, f"Claim statement #{c_idx+1} for {domain} query {i+1}", verdict, confidence, created_at.isoformat())
            )

            # Evidence
            num_evidence = random.randint(1, 3)
            for e_idx in range(num_evidence):
                e_id = f"e-{c_id}-{e_idx+1}"
                src = random.choice(sources)
                if verdict == "SUPPORTED":
                    e_status = random.choice(["SUPPORT", "SUPPORT", "UNKNOWN"])
                elif verdict == "CONTRADICTED":
                    e_status = random.choice(["CONTRADICT", "CONTRADICT", "UNKNOWN"])
                else:
                    e_status = "UNKNOWN"

                strength = round(random.uniform(0.4, 0.98), 3)
                cursor.execute(
                    "INSERT INTO evidence (id, claim_id, source_id, status, strength, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (e_id, c_id, src[0], e_status, strength, created_at.isoformat())
                )

        # Consistency Results
        signal = random.choices(
            SIGNALS,
            weights=[0.65, 0.18, 0.08, 0.05, 0.04],
            k=1
        )[0]
        cursor.execute(
            "INSERT INTO consistency_results (id, verification_id, signal_type, quality_score, created_at) VALUES (?, ?, ?, ?, ?)",
            (f"cr-{v_id}", v_id, signal, round(random.uniform(0.5, 0.99), 3), created_at.isoformat())
        )

    # Seed Benchmark Results
    benchmarks = ["bm-factuality-v1", "bm-hallucination-v2", "bm-reasoning-v1"]
    for bm_id in benchmarks:
        for model in MODELS:
            sampling_basis = random.choice(SAMPLING_BASES)
            base_acc = {
                "gpt-4o": 0.92,
                "claude-3-5-sonnet": 0.94,
                "llama-3.1-70b": 0.85,
                "qwen-2.5-72b": 0.87,
                "mistral-large": 0.83,
                "gemini-1.5-pro": 0.89
            }.get(model["id"], 0.85)

            # Create 20 benchmark items per model & benchmark
            for item in range(20):
                item_id = f"{bm_id}-{model['id']}-{item+1:02d}"
                gt = random.choice(["SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"])
                
                # Model prediction
                if random.random() < base_acc:
                    pred = gt
                else:
                    pred = random.choice([v for v in VERDICTS if v != gt])

                prec = round(random.uniform(0.75, 0.98), 3)
                rec = round(random.uniform(0.70, 0.96), 3)
                f1_val = round(2 * (prec * rec) / (prec + rec), 3)
                acc_val = round(base_acc + random.uniform(-0.05, 0.05), 3)
                ece_val = round(random.uniform(0.02, 0.12), 4)

                cursor.execute(
                    """INSERT INTO benchmark_results (
                        id, benchmark_id, model_id, sampling_basis, item_id, claim_text,
                        ground_truth, predicted_verdict, precision, recall, f1, accuracy, ece,
                        latency_ms, llm_calls, search_calls, token_usage, status, resample_count,
                        successful_resamples, failed_resamples, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"br-{item_id}", bm_id, model["id"], sampling_basis, item_id,
                        f"Benchmark evaluated claim #{item+1} for model {model['name']}",
                        gt, pred, prec, rec, f1_val, acc_val, ece_val,
                        random.randint(350, 1900), random.randint(1, 4), random.randint(0, 3), random.randint(300, 3500),
                        "SUCCESS" if random.random() > 0.03 else "FAILED",
                        5, random.randint(4, 5), random.randint(0, 1),
                        (datetime.now() - timedelta(days=random.randint(1, 15))).isoformat()
                    )
                )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
