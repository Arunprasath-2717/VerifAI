from typing import Dict, Any, List, Optional
from app.db.database import get_db_connection

class BenchmarkService:

    @classmethod
    def list_benchmarks(cls) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 
                benchmark_id,
                COUNT(DISTINCT model_id) as model_count,
                COUNT(id) as total_items,
                MIN(sampling_basis) as primary_sampling_basis,
                MIN(created_at) as created_at
            FROM benchmark_results
            GROUP BY benchmark_id
            ORDER BY created_at DESC"""
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "benchmark_id": r["benchmark_id"],
                "model_count": r["model_count"],
                "total_items": r["total_items"],
                "sampling_basis": r["primary_sampling_basis"],
                "created_at": r["created_at"]
            })
        return result

    @classmethod
    def get_benchmark_detail(cls, benchmark_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 
                benchmark_id,
                COUNT(DISTINCT model_id) as model_count,
                COUNT(id) as total_items,
                MIN(sampling_basis) as sampling_basis,
                MIN(created_at) as created_at
            FROM benchmark_results
            WHERE benchmark_id = ?
            GROUP BY benchmark_id""",
            (benchmark_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "benchmark_id": row["benchmark_id"],
            "model_count": row["model_count"],
            "total_items": row["total_items"],
            "sampling_basis": row["sampling_basis"],
            "created_at": row["created_at"]
        }

    @classmethod
    def get_benchmark_metrics(cls, benchmark_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM benchmark_results WHERE benchmark_id = ?", (benchmark_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        total_items = len(rows)
        sampling_basis = rows[0]["sampling_basis"]

        # Aggregate Claim-level & System-level metrics
        precisions = [r["precision"] for r in rows if r["precision"] is not None]
        recalls = [r["recall"] for r in rows if r["recall"] is not None]
        f1s = [r["f1"] for r in rows if r["f1"] is not None]
        accuracies = [r["accuracy"] for r in rows if r["accuracy"] is not None]
        eces = [r["ece"] for r in rows if r["ece"] is not None]
        latencies = [r["latency_ms"] for r in rows if r["latency_ms"] is not None]
        llm_calls = [r["llm_calls"] for r in rows if r["llm_calls"] is not None]
        search_calls = [r["search_calls"] for r in rows if r["search_calls"] is not None]
        tokens = [r["token_usage"] for r in rows if r["token_usage"] is not None]

        # Calculate False Positive Rate (FPR) and False Negative Rate (FNR)
        fp_count = 0
        fn_count = 0
        neg_count = 0
        pos_count = 0
        halluc_count = 0

        for r in rows:
            gt = r["ground_truth"]
            pred = r["predicted_verdict"]
            if gt == "CONTRADICTED":
                neg_count += 1
                if pred == "SUPPORTED":
                    fp_count += 1
                halluc_count += 1 if pred == "CONTRADICTED" or pred == "INCONCLUSIVE" else 0
            elif gt == "SUPPORTED":
                pos_count += 1
                if pred == "CONTRADICTED":
                    fn_count += 1

        fpr = round(fp_count / neg_count, 4) if neg_count > 0 else 0.0
        fnr = round(fn_count / pos_count, 4) if pos_count > 0 else 0.0
        hallucination_rate = round(fp_count / total_items, 4) if total_items > 0 else 0.0
        verification_accuracy = round(sum(accuracies) / len(accuracies), 4) if accuracies else 0.0

        failed_count = sum(1 for r in rows if r["status"] == "FAILED")
        failure_rate = round(failed_count / total_items, 4) if total_items > 0 else 0.0

        return {
            "benchmark_id": benchmark_id,
            "sampling_basis": sampling_basis,
            "total_items": total_items,
            "claim_level": {
                "precision": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
                "recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
                "f1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
                "accuracy": verification_accuracy
            },
            "system_level": {
                "hallucination_rate": hallucination_rate,
                "verification_accuracy": verification_accuracy,
                "false_positive_rate": fpr,
                "false_negative_rate": fnr
            },
            "calibration": {
                "ece": round(sum(eces) / len(eces), 4) if eces else 0.0
            },
            "operational": {
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                "avg_llm_calls": round(sum(llm_calls) / len(llm_calls), 2) if llm_calls else 0,
                "avg_search_calls": round(sum(search_calls) / len(search_calls), 2) if search_calls else 0,
                "total_token_usage": sum(tokens),
                "failure_rate": failure_rate
            }
        }

    @classmethod
    def get_benchmark_models(cls, benchmark_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                model_id,
                sampling_basis,
                COUNT(id) as item_count,
                AVG(precision) as avg_precision,
                AVG(recall) as avg_recall,
                AVG(f1) as avg_f1,
                AVG(accuracy) as avg_accuracy,
                AVG(ece) as avg_ece,
                AVG(latency_ms) as avg_latency_ms,
                SUM(token_usage) as total_tokens,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failures
            FROM benchmark_results
            WHERE benchmark_id = ?
            GROUP BY model_id, sampling_basis
        """
        cursor.execute(query, (benchmark_id,))
        rows = cursor.fetchall()
        conn.close()

        models_list = []
        for r in rows:
            tot = r["item_count"]
            fails = r["failures"] or 0
            models_list.append({
                "model_id": r["model_id"],
                "sampling_basis": r["sampling_basis"],
                "item_count": tot,
                "precision": round(r["avg_precision"], 4) if r["avg_precision"] is not None else 0.0,
                "recall": round(r["avg_recall"], 4) if r["avg_recall"] is not None else 0.0,
                "f1": round(r["avg_f1"], 4) if r["avg_f1"] is not None else 0.0,
                "accuracy": round(r["avg_accuracy"], 4) if r["avg_accuracy"] is not None else 0.0,
                "ece": round(r["avg_ece"], 4) if r["avg_ece"] is not None else 0.0,
                "latency_ms": round(r["avg_latency_ms"], 2) if r["avg_latency_ms"] is not None else 0,
                "token_usage": r["total_tokens"] or 0,
                "failure_rate": round(fails / tot, 4) if tot > 0 else 0.0
            })

        return models_list

    @classmethod
    def get_benchmark_claims(cls, benchmark_id: str, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        if model_id:
            cursor.execute(
                "SELECT * FROM benchmark_results WHERE benchmark_id = ? AND model_id = ? ORDER BY id ASC",
                (benchmark_id, model_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM benchmark_results WHERE benchmark_id = ? ORDER BY id ASC",
                (benchmark_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        claims = []
        for r in rows:
            is_correct = (r["ground_truth"] == r["predicted_verdict"])
            claims.append({
                "claim_id": r["id"],
                "item_id": r["item_id"],
                "claim_text": r["claim_text"],
                "model_id": r["model_id"],
                "sampling_basis": r["sampling_basis"],
                "ground_truth": r["ground_truth"],
                "predicted_verdict": r["predicted_verdict"],
                "precision": round(r["precision"], 4) if r["precision"] is not None else None,
                "recall": round(r["recall"], 4) if r["recall"] is not None else None,
                "f1": round(r["f1"], 4) if r["f1"] is not None else None,
                "accuracy": round(r["accuracy"], 4) if r["accuracy"] is not None else None,
                "ece": round(r["ece"], 4) if r["ece"] is not None else None,
                "is_correct": is_correct,
                "status": r["status"]
            })

        return claims

    @classmethod
    def compare_benchmarks(cls, benchmark_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        if benchmark_ids:
            placeholders = ",".join(["?"] * len(benchmark_ids))
            cursor.execute(f"SELECT DISTINCT benchmark_id FROM benchmark_results WHERE benchmark_id IN ({placeholders})", benchmark_ids)
        else:
            cursor.execute("SELECT DISTINCT benchmark_id FROM benchmark_results")

        bm_ids = [r[0] for r in cursor.fetchall()]
        conn.close()

        comparisons = []
        for b_id in bm_ids:
            m = cls.get_benchmark_metrics(b_id)
            if m:
                comparisons.append(m)

        return comparisons
