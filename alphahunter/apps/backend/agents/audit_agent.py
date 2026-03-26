import time
from sqlalchemy.orm import Session
from models.db import ScanRun, ScanResult, Decision
from loguru import logger

class AuditAgent:
    def __init__(self, db: Session):
        self.db = db
        
    def log_scan_result(self, scan_run_id: int, result_data: dict, reasoning_text: str):
        """Persists the scan finding for transparency."""
        try:
            db_result = ScanResult(
                scan_run_id=scan_run_id,
                symbol=result_data["symbol"],
                price=result_data.get("price"),
                volume_today=result_data.get("volume_today"),
                
                breakout_triggered=result_data.get("breakout_triggered", False),
                volume_spike_triggered=result_data.get("volume_spike_triggered", False),
                bulk_deal_triggered=result_data.get("bulk_deal_triggered", False),
                
                breakout_details=result_data.get("breakout_details", {}),
                volume_spike_details=result_data.get("volume_spike_details", {}),
                bulk_deal_details=result_data.get("bulk_deal_details", {}),
                
                signal_count=result_data.get("signal_count", 0),
                composite_score=result_data.get("composite_score", 0),
                
                reasoning_text=reasoning_text,
                
                backtest_matches=result_data.get("backtest_matches", 0),
                backtest_success_rate=result_data.get("backtest_success_rate", 0),
                backtest_cases_json=result_data.get("cases", [])
            )
            self.db.add(db_result)
            self.db.commit()
            self.db.refresh(db_result)
            return db_result.id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Audit log failed for result {result_data.get('symbol')}: {e}")
            return None

    def log_decision(self, scan_result_id: int, symbol: str, decision_data: dict, full_snapshot: dict):
        """Creates the formal, auditable decision track record."""
        try:
            db_decision = Decision(
                scan_result_id=scan_result_id,
                symbol=symbol,
                action=decision_data["action"],
                confidence=decision_data["confidence"],
                entry_price=decision_data["entry_price"],
                target_price=decision_data["target_price"],
                stop_loss=decision_data["stop_loss"],
                rr_ratio=decision_data["rr_ratio"],
                score_signal=decision_data["score_signal"],
                score_backtest=decision_data["score_backtest"],
                score_composite=decision_data["score_composite"],
                snapshot_json=full_snapshot
            )
            self.db.add(db_decision)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Audit log failed for decision {symbol}: {e}")
