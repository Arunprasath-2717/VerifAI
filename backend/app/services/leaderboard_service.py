from typing import Dict, Any, List, Optional
from app.db.database import get_db_connection

AVAILABLE_LEADERBOARD_METRICS = [
    {"id": "verification_accuracy", "label": "Verification Accuracy", "description": "Ratio of supported claims out of total evaluable claims."},
    {"id": "trust_score", "label": "Trust Score", "description": "Aggregated core trust score calculated by verification system."},
    {"id": "hallucination_rate", "label": "Hallucination Rate", "description": "Proportion of claims identified as contradicted hallucinations."},
    {"id": "consistency", "label": "Consistency Signal", "description": "Average consistency signal quality score."},
    {"id": "support_rate", "label": "Support Rate", "description": "Proportion of claims with supported verdict."},
    {"id": "contradiction_rate", "label": "Contradiction Rate", "description": "Proportion of claims with contradicted verdict."},
    {"id": "inconclusive_rate", "label": "Inconclusive Rate", "description": "Proportion of claims with inconclusive verdict."},
    {"id": "average_confidence", "label": "Average Confidence", "description": "Mean confidence score across verified claims."},
    {"id": "evidence_supported_rate", "label": "Evidence-Supported Rate", "description": "Proportion of claims backed by strong evidence."}
]

class LeaderboardService:

    @classmethod
    def get_leaderboard(cls, sort_by: str = "verification_accuracy", order: str = "desc") -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query verifications + claims + consistency for each model
        query = """
            SELECT 
                v.model_id,
                COUNT(DISTINCT v.id) as verification_count,
                AVG(v.trust_score) as trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported_claims,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted_claims,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive_claims,
                AVG(c.confidence) as average_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            GROUP BY v.model_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        leaderboard = []
        for r in rows:
            model_id = r["model_id"]
            tot_claims = r["total_claims"] or 0
            sup = r["supported_claims"] or 0
            con = r["contradicted_claims"] or 0
            inc = r["inconclusive_claims"] or 0

            # Consistency signal
            cursor.execute(
                """SELECT AVG(cr.quality_score) FROM consistency_results cr 
                   JOIN verifications v ON cr.verification_id = v.id 
                   WHERE v.model_id = ?""",
                (model_id,)
            )
            cr_row = cursor.fetchone()
            consistency = round(cr_row[0], 4) if cr_row and cr_row[0] is not None else 0.0

            # Evidence supported rate
            cursor.execute(
                """SELECT COUNT(e.id), SUM(CASE WHEN e.status = 'SUPPORT' THEN 1 ELSE 0 END) 
                   FROM evidence e 
                   JOIN claims c ON e.claim_id = c.id 
                   JOIN verifications v ON c.verification_id = v.id 
                   WHERE v.model_id = ?""",
                (model_id,)
            )
            ev_row = cursor.fetchone()
            tot_ev = ev_row[0] or 0
            sup_ev = ev_row[1] or 0
            evidence_supported_rate = round(sup_ev / tot_ev, 4) if tot_ev > 0 else 0.0

            acc = round(sup / tot_claims, 4) if tot_claims > 0 else 0.0
            halluc = round(con / tot_claims, 4) if tot_claims > 0 else 0.0

            leaderboard.append({
                "model_id": model_id,
                "verification_count": r["verification_count"],
                "verification_accuracy": acc,
                "trust_score": round(r["trust_score"], 4) if r["trust_score"] is not None else 0.0,
                "hallucination_rate": halluc,
                "consistency": consistency,
                "support_rate": acc,
                "contradiction_rate": halluc,
                "inconclusive_rate": round(inc / tot_claims, 4) if tot_claims > 0 else 0.0,
                "average_confidence": round(r["average_confidence"], 4) if r["average_confidence"] is not None else None,
                "evidence_supported_rate": evidence_supported_rate
            })

        conn.close()

        reverse = (order.lower() == "desc")
        # Reverse sort order if sorting by hallucination_rate or contradiction_rate (lower is better)
        if sort_by in ["hallucination_rate", "contradiction_rate", "inconclusive_rate"]:
            reverse = not reverse

        leaderboard.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)

        # Assign ranks
        for rank, item in enumerate(leaderboard, start=1):
            item["rank"] = rank

        return leaderboard

    @classmethod
    def get_model_detail(cls, model_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check model exists
        cursor.execute("SELECT DISTINCT model_id FROM verifications WHERE model_id = ?", (model_id,))
        if not cursor.fetchone():
            conn.close()
            return None

        # Fetch model verifications stats
        cursor.execute(
            """SELECT 
                COUNT(DISTINCT v.id) as verification_count,
                AVG(v.trust_score) as trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported_claims,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted_claims,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive_claims,
                AVG(c.confidence) as avg_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            WHERE v.model_id = ?""",
            (model_id,)
        )
        r = cursor.fetchone()

        tot_claims = r["total_claims"] or 0
        sup = r["supported_claims"] or 0
        con = r["contradicted_claims"] or 0
        inc = r["inconclusive_claims"] or 0

        # Consistency
        cursor.execute(
            """SELECT AVG(cr.quality_score) FROM consistency_results cr 
               JOIN verifications v ON cr.verification_id = v.id 
               WHERE v.model_id = ?""",
            (model_id,)
        )
        cr_row = cursor.fetchone()
        consistency = round(cr_row[0], 4) if cr_row and cr_row[0] is not None else 0.0

        # Evidence support
        cursor.execute(
            """SELECT COUNT(e.id), SUM(CASE WHEN e.status = 'SUPPORT' THEN 1 ELSE 0 END) 
               FROM evidence e 
               JOIN claims c ON e.claim_id = c.id 
               JOIN verifications v ON c.verification_id = v.id 
               WHERE v.model_id = ?""",
            (model_id,)
        )
        ev_row = cursor.fetchone()
        tot_ev = ev_row[0] or 0
        sup_ev = ev_row[1] or 0
        evidence_supported_rate = round(sup_ev / tot_ev, 4) if tot_ev > 0 else 0.0

        # Historical trend for this model
        cursor.execute(
            """SELECT 
                DATE(v.created_at) as trend_date,
                AVG(v.trust_score) as avg_trust,
                COUNT(c.id) as claims_cnt,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as con_cnt
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            WHERE v.model_id = ?
            GROUP BY DATE(v.created_at)
            ORDER BY trend_date ASC""",
            (model_id,)
        )
        trend_rows = cursor.fetchall()
        trends = []
        for tr in trend_rows:
            tc = tr["claims_cnt"] or 0
            cc = tr["con_cnt"] or 0
            trends.append({
                "date": tr["trend_date"],
                "trust_score": round(tr["avg_trust"], 4) if tr["avg_trust"] is not None else 0.0,
                "hallucination_rate": round(cc / tc, 4) if tc > 0 else 0.0
            })

        conn.close()

        return {
            "model_id": model_id,
            "verification_count": r["verification_count"],
            "trust_score": round(r["trust_score"], 4) if r["trust_score"] is not None else 0.0,
            "accuracy": round(sup / tot_claims, 4) if tot_claims > 0 else 0.0,
            "hallucination_rate": round(con / tot_claims, 4) if tot_claims > 0 else 0.0,
            "consistency": consistency,
            "confidence": round(r["avg_confidence"], 4) if r["avg_confidence"] is not None else None,
            "evidence_support": evidence_supported_rate,
            "contradiction_rate": round(con / tot_claims, 4) if tot_claims > 0 else 0.0,
            "inconclusive_rate": round(inc / tot_claims, 4) if tot_claims > 0 else 0.0,
            "total_claims": tot_claims,
            "historical_performance": trends
        }

    @classmethod
    def compare_models(cls, model_ids: List[str]) -> Dict[str, Any]:
        if not model_ids:
            return {"models": [], "comparison_matrix": {}}

        comparison = []
        for mid in model_ids:
            detail = cls.get_model_detail(mid.strip())
            if detail:
                comparison.append(detail)

        metrics = ["trust_score", "accuracy", "hallucination_rate", "consistency", "confidence", "evidence_support", "contradiction_rate", "inconclusive_rate"]
        matrix = {m: {item["model_id"]: item.get(m) for item in comparison} for m in metrics}

        return {
            "models": comparison,
            "comparison_matrix": matrix
        }
