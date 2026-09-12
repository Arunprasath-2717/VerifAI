from datetime import datetime
from typing import Dict, Any, List, Optional
from app.db.database import get_db_connection

class AnalyticsService:

    @staticmethod
    def _build_filter_clause(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        model_id: Optional[str] = None,
        verdict: Optional[str] = None,
        domain: Optional[str] = None,
        v_prefix: str = "v",
        c_prefix: str = "c"
    ) -> tuple[str, List[Any]]:
        where_conditions = []
        params = []

        if date_from:
            where_conditions.append(f"{v_prefix}.created_at >= ?")
            params.append(date_from)
        if date_to:
            where_conditions.append(f"{v_prefix}.created_at <= ?")
            params.append(date_to)
        if model_id:
            where_conditions.append(f"{v_prefix}.model_id = ?")
            params.append(model_id)
        if domain:
            where_conditions.append(f"{v_prefix}.domain = ?")
            params.append(domain)
        if verdict:
            where_conditions.append(f"{c_prefix}.verdict = ?")
            params.append(verdict.upper())

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        return where_clause, params

    @classmethod
    def get_overview(
        cls,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        model_id: Optional[str] = None,
        verdict: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        # Overview verification count and overall trust score
        query = f"""
            SELECT 
                COUNT(DISTINCT v.id) as total_verifications,
                AVG(v.trust_score) as avg_trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported_claims,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted_claims,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive_claims,
                AVG(c.confidence) as avg_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
        """
        cursor.execute(query, params)
        row = cursor.fetchone()

        total_verifications = row["total_verifications"] or 0
        avg_trust_score = round(row["avg_trust_score"], 4) if row["avg_trust_score"] is not None else None
        total_claims = row["total_claims"] or 0
        supported = row["supported_claims"] or 0
        contradicted = row["contradicted_claims"] or 0
        inconclusive = row["inconclusive_claims"] or 0
        avg_confidence = round(row["avg_confidence"], 4) if row["avg_confidence"] is not None else None

        # Hallucination rate = Contradicted claims / Total evaluable claims (supported + contradicted + inconclusive)
        hallucination_rate = round(contradicted / total_claims, 4) if total_claims > 0 else 0.0

        # Signal Quality metric
        sig_query = f"""
            SELECT 
                COUNT(cr.id) as total_signals,
                SUM(CASE WHEN cr.signal_type IN ('entailment', 'contradiction') THEN 1 ELSE 0 END) as valid_signals,
                AVG(cr.quality_score) as avg_quality
            FROM consistency_results cr
            JOIN verifications v ON cr.verification_id = v.id
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
        """
        cursor.execute(sig_query, params)
        sig_row = cursor.fetchone()
        signal_quality = round(sig_row["avg_quality"], 4) if sig_row and sig_row["avg_quality"] is not None else 0.0

        # Evidence Quality metric
        ev_query = f"""
            SELECT 
                COUNT(e.id) as total_evidence,
                AVG(e.strength) as avg_strength,
                SUM(CASE WHEN e.status = 'SUPPORT' THEN 1 ELSE 0 END) as support_evidence,
                SUM(CASE WHEN e.status = 'CONTRADICT' THEN 1 ELSE 0 END) as contradict_evidence,
                SUM(CASE WHEN e.status = 'UNKNOWN' THEN 1 ELSE 0 END) as unknown_evidence
            FROM evidence e
            JOIN claims c ON e.claim_id = c.id
            JOIN verifications v ON c.verification_id = v.id
            {where_clause}
        """
        cursor.execute(ev_query, params)
        ev_row = cursor.fetchone()
        evidence_quality = round(ev_row["avg_strength"], 4) if ev_row and ev_row["avg_strength"] is not None else 0.0

        conn.close()

        return {
            "overall_trust_score": avg_trust_score,
            "total_verifications": total_verifications,
            "total_claims": total_claims,
            "supported_claims": supported,
            "contradicted_claims": contradicted,
            "inconclusive_claims": inconclusive,
            "hallucination_rate": hallucination_rate,
            "average_confidence": avg_confidence,
            "signal_quality": signal_quality,
            "evidence_quality": evidence_quality
        }

    @classmethod
    def get_trust_score(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                AVG(v.trust_score) as trust_score,
                MIN(v.trust_score) as min_score,
                MAX(v.trust_score) as max_score,
                COUNT(DISTINCT v.id) as sample_size
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
        """
        cursor.execute(query, params)
        row = cursor.fetchone()

        conn.close()

        score = round(row["trust_score"], 4) if row["trust_score"] is not None else None
        return {
            "trust_score": score,
            "min_trust_score": round(row["min_score"], 4) if row["min_score"] is not None else None,
            "max_trust_score": round(row["max_score"], 4) if row["max_score"] is not None else None,
            "sample_size": row["sample_size"] or 0,
            "source_of_truth": "core.verifications.trust_score",
            "has_signal": score is not None
        }

    @classmethod
    def get_verification_stats(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported_count,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted_count,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive_count
            FROM claims c
            JOIN verifications v ON c.verification_id = v.id
            {where_clause}
        """
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()

        total = row["total_claims"] or 0
        sup = row["supported_count"] or 0
        con = row["contradicted_count"] or 0
        inc = row["inconclusive_count"] or 0

        return {
            "total_claims": total,
            "supported": {
                "count": sup,
                "percentage": round(sup / total * 100, 2) if total > 0 else 0.0
            },
            "contradicted": {
                "count": con,
                "percentage": round(con / total * 100, 2) if total > 0 else 0.0
            },
            "inconclusive": {
                "count": inc,
                "percentage": round(inc / total * 100, 2) if total > 0 else 0.0
            }
        }

    @classmethod
    def get_hallucination_rate(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted_count,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported_count
            FROM claims c
            JOIN verifications v ON c.verification_id = v.id
            {where_clause}
        """
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()

        total = row["total_claims"] or 0
        contradicted = row["contradicted_count"] or 0

        hallucination_rate = round(contradicted / total, 4) if total > 0 else 0.0
        contradiction_rate = round(contradicted / total, 4) if total > 0 else 0.0

        return {
            "hallucination_rate": hallucination_rate,
            "contradiction_rate": contradiction_rate,
            "total_evaluated_claims": total,
            "contradicted_claims": contradicted,
            "definition": "Ratio of CONTRADICTED claims to total claims evaluated by verification pipeline."
        }

    @classmethod
    def get_confidence(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT c.confidence 
            FROM claims c
            JOIN verifications v ON c.verification_id = v.id
            {where_clause}
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        valid_confidences = [r["confidence"] for r in rows if r["confidence"] is not None]
        no_signal_count = len(rows) - len(valid_confidences)

        # Build histogram buckets: 0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
        buckets = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }

        for c in valid_confidences:
            if c < 0.2:
                buckets["0.0-0.2"] += 1
            elif c < 0.4:
                buckets["0.2-0.4"] += 1
            elif c < 0.6:
                buckets["0.4-0.6"] += 1
            elif c < 0.8:
                buckets["0.6-0.8"] += 1
            else:
                buckets["0.8-1.0"] += 1

        avg_conf = round(sum(valid_confidences) / len(valid_confidences), 4) if valid_confidences else None

        return {
            "average_confidence": avg_conf,
            "total_claims": len(rows),
            "valid_signal_count": len(valid_confidences),
            "no_verification_signal_count": no_signal_count,
            "distribution": [
                {"range": k, "count": v} for k, v in buckets.items()
            ],
            "note": "Claims with missing confidence are explicitly tracked as 'No verification signal' rather than zero."
        }

    @classmethod
    def get_signal_quality(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                cr.signal_type,
                COUNT(cr.id) as count,
                AVG(cr.quality_score) as avg_quality
            FROM consistency_results cr
            JOIN verifications v ON cr.verification_id = v.id
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
            GROUP BY cr.signal_type
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        signals = {
            "entailment": 0,
            "contradiction": 0,
            "absent": 0,
            "refused": 0,
            "failed_judgment": 0
        }
        quality_scores = []
        total_signals = 0

        for r in rows:
            st = r["signal_type"]
            cnt = r["count"]
            if st in signals:
                signals[st] = cnt
            total_signals += cnt
            if r["avg_quality"] is not None:
                quality_scores.append(r["avg_quality"])

        avg_sig_quality = round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0.0

        return {
            "average_signal_quality": avg_sig_quality,
            "total_signals": total_signals,
            "breakdown": signals,
            "note": "Preserves explicit distinction between absent, refused, and failed_judgment."
        }

    @classmethod
    def get_evidence_quality(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                e.status,
                COUNT(e.id) as count,
                AVG(e.strength) as avg_strength,
                SUM(CASE WHEN e.strength >= 0.8 THEN 1 ELSE 0 END) as strong_evidence_count
            FROM evidence e
            JOIN claims c ON e.claim_id = c.id
            JOIN verifications v ON c.verification_id = v.id
            {where_clause}
            GROUP BY e.status
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        distribution = {
            "SUPPORT": 0,
            "CONTRADICT": 0,
            "UNKNOWN": 0
        }
        total_ev = 0
        strong_ev = 0
        strengths = []

        for r in rows:
            st = r["status"]
            cnt = r["count"]
            if st in distribution:
                distribution[st] = cnt
            total_ev += cnt
            strong_ev += r["strong_evidence_count"] or 0
            if r["avg_strength"] is not None:
                strengths.append(r["avg_strength"])

        avg_strength = round(sum(strengths) / len(strengths), 4) if strengths else 0.0

        return {
            "average_strength": avg_strength,
            "total_evidence": total_ev,
            "strong_evidence_count": strong_ev,
            "distribution": distribution,
            "note": "UNKNOWN status is preserved independently without converting to SUPPORT or CONTRADICT."
        }

    @classmethod
    def get_trends(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        # Aggregate daily trends
        query = f"""
            SELECT 
                DATE(v.created_at) as trend_date,
                COUNT(DISTINCT v.id) as verifications_count,
                AVG(v.trust_score) as avg_trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive,
                AVG(c.confidence) as avg_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
            GROUP BY DATE(v.created_at)
            ORDER BY trend_date ASC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data_points = []
        for r in rows:
            t_claims = r["total_claims"] or 0
            cnt_contradicted = r["contradicted"] or 0
            data_points.append({
                "date": r["trend_date"],
                "verifications": r["verifications_count"],
                "trust_score": round(r["avg_trust_score"], 4) if r["avg_trust_score"] is not None else None,
                "supported": r["supported"] or 0,
                "contradicted": cnt_contradicted,
                "inconclusive": r["inconclusive"] or 0,
                "hallucination_rate": round(cnt_contradicted / t_claims, 4) if t_claims > 0 else 0.0,
                "confidence": round(r["avg_confidence"], 4) if r["avg_confidence"] is not None else None
            })

        return {
            "trends": data_points
        }

    @classmethod
    def get_domains(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                v.domain,
                COUNT(DISTINCT v.id) as verification_count,
                AVG(v.trust_score) as avg_trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive,
                AVG(c.confidence) as avg_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
            GROUP BY v.domain
            ORDER BY verification_count DESC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        domains_list = []
        for r in rows:
            t_claims = r["total_claims"] or 0
            cnt_con = r["contradicted"] or 0
            domains_list.append({
                "domain": r["domain"],
                "verification_count": r["verification_count"],
                "trust_score": round(r["avg_trust_score"], 4) if r["avg_trust_score"] is not None else None,
                "supported": r["supported"] or 0,
                "contradicted": cnt_con,
                "inconclusive": r["inconclusive"] or 0,
                "hallucination_rate": round(cnt_con / t_claims, 4) if t_claims > 0 else 0.0,
                "confidence": round(r["avg_confidence"], 4) if r["avg_confidence"] is not None else None
            })

        return {"domains": domains_list}

    @classmethod
    def get_models(cls, date_from: Optional[str] = None, date_to: Optional[str] = None, model_id: Optional[str] = None, verdict: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause, params = cls._build_filter_clause(date_from, date_to, model_id, verdict, domain)

        query = f"""
            SELECT 
                v.model_id,
                COUNT(DISTINCT v.id) as verification_count,
                AVG(v.trust_score) as avg_trust_score,
                COUNT(c.id) as total_claims,
                SUM(CASE WHEN c.verdict = 'SUPPORTED' THEN 1 ELSE 0 END) as supported,
                SUM(CASE WHEN c.verdict = 'CONTRADICTED' THEN 1 ELSE 0 END) as contradicted,
                SUM(CASE WHEN c.verdict = 'INCONCLUSIVE' THEN 1 ELSE 0 END) as inconclusive,
                AVG(c.confidence) as avg_confidence
            FROM verifications v
            LEFT JOIN claims c ON v.id = c.verification_id
            {where_clause}
            GROUP BY v.model_id
            ORDER BY verification_count DESC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        models_list = []
        for r in rows:
            t_claims = r["total_claims"] or 0
            sup = r["supported"] or 0
            con = r["contradicted"] or 0
            inc = r["inconclusive"] or 0
            models_list.append({
                "model_id": r["model_id"],
                "verification_count": r["verification_count"],
                "trust_score": round(r["avg_trust_score"], 4) if r["avg_trust_score"] is not None else None,
                "supported_rate": round(sup / t_claims, 4) if t_claims > 0 else 0.0,
                "contradiction_rate": round(con / t_claims, 4) if t_claims > 0 else 0.0,
                "inconclusive_rate": round(inc / t_claims, 4) if t_claims > 0 else 0.0,
                "hallucination_rate": round(con / t_claims, 4) if t_claims > 0 else 0.0,
                "average_confidence": round(r["avg_confidence"], 4) if r["avg_confidence"] is not None else None
            })

        return {"models": models_list}

    @classmethod
    def get_filters(cls) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT model_id FROM verifications ORDER BY model_id")
        models = [r[0] for r in cursor.fetchall() if r[0]]

        cursor.execute("SELECT DISTINCT domain FROM verifications ORDER BY domain")
        domains = [r[0] for r in cursor.fetchall() if r[0]]

        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM verifications")
        min_max = cursor.fetchone()
        conn.close()

        return {
            "models": models,
            "domains": domains,
            "verdicts": ["SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"],
            "date_range": {
                "min": min_max[0] if min_max else None,
                "max": min_max[1] if min_max else None
            }
        }
