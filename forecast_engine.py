"""
KazKaz AI - Gelecek Tahmin Motoru (Prophet)
=============================================
Özellikler:
  - Gelecek 3/6/12 ay gelir tahmini
  - Trend + seasonality ayrıştırma
  - Confidence interval (güven aralığı)
  - Anomali tespiti
  - Tahmin özet raporu

Kurulum: pip install prophet
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings("ignore")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


# ─────────────────────────────────────────────
# TAHMİN MOTORU
# ─────────────────────────────────────────────

class ForecastEngine:
    """
    Prophet tabanlı gelir tahmin motoru.

    Kullanım:
        fc = ForecastEngine(df)
        sonuc = fc.forecast(ay=3)
    """

    def __init__(self, df: pd.DataFrame):
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet kurulu değil: pip install prophet")

        self.df = df
        self._model: Optional[Prophet] = None
        self._forecast_df: Optional[pd.DataFrame] = None
        self._trained = False

    # ─────────────────────────────────────────
    # MODEL EĞİTİMİ
    # ─────────────────────────────────────────

    def _prepare_data(self) -> pd.DataFrame:
        """Prophet formatına çevir: ds (tarih), y (değer)."""
        monthly = (
            self.df.groupby("YilAy")["Gelir"]
            .sum()
            .reset_index()
        )
        # YilAy → datetime
        monthly["ds"] = pd.to_datetime(monthly["YilAy"], format="%Y-%m")
        monthly["y"]  = monthly["Gelir"].astype(float)
        return monthly[["ds", "y"]].sort_values("ds").reset_index(drop=True)

    def train(
        self,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = False,
        daily_seasonality:  bool = False,
        changepoint_prior_scale: float = 0.05,
    ) -> "ForecastEngine":
        """Modeli eğit."""
        data = self._prepare_data()

        if len(data) < 3:
            raise ValueError("Tahmin için en az 3 aylık veri gereklidir.")

        self._model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale,
            interval_width=0.90,  # %90 güven aralığı
        )
        self._model.fit(data)
        self._trained = True
        self._train_data = data
        return self

    # ─────────────────────────────────────────
    # TAHMİN
    # ─────────────────────────────────────────

    def forecast(self, ay: int = 3) -> Dict[str, Any]:
        """
        Gelecek `ay` adet aylık tahmin üretir.
        Returns: tahmin sonuçları + özet istatistikler
        """
        if not self._trained:
            self.train()

        future = self._model.make_future_dataframe(periods=ay, freq="MS")
        forecast = self._model.predict(future)
        self._forecast_df = forecast

        # Geçmiş vs tahmin ayrımı
        train_len     = len(self._train_data)
        gecmis        = forecast.iloc[:train_len]
        tahmin_donemi = forecast.iloc[train_len:]

        # Tahmin özeti
        tahmin_rows = []
        for _, row in tahmin_donemi.iterrows():
            tahmin_rows.append({
                "Dönem":        row["ds"].strftime("%Y-%m"),
                "Tahmin":       max(0, round(row["yhat"], 0)),
                "Alt Sınır":    max(0, round(row["yhat_lower"], 0)),
                "Üst Sınır":    max(0, round(row["yhat_upper"], 0)),
            })
        tahmin_df = pd.DataFrame(tahmin_rows)

        # Trend yönü
        trend_yonu = self._trend_direction(tahmin_donemi)

        # Büyüme beklentisi
        son_gercek   = float(self._train_data["y"].iloc[-1])
        ilk_tahmin   = float(tahmin_donemi["yhat"].iloc[0]) if not tahmin_donemi.empty else son_gercek
        son_tahmin   = float(tahmin_donemi["yhat"].iloc[-1]) if not tahmin_donemi.empty else son_gercek
        buyume_oran  = ((son_tahmin - son_gercek) / son_gercek * 100) if son_gercek > 0 else 0

        return {
            "tahmin_tablosu":   tahmin_df,
            "tam_forecast":     forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend"]],
            "gecmis_fit":       gecmis[["ds", "yhat"]],
            "trend_yonu":       trend_yonu,
            "toplam_tahmin":    float(tahmin_df["Tahmin"].sum()),
            "ortalama_tahmin":  float(tahmin_df["Tahmin"].mean()),
            "buyume_beklentisi": round(buyume_oran, 2),
            "ay_sayisi":        ay,
        }

    # ─────────────────────────────────────────
    # TREND ANALİZİ
    # ─────────────────────────────────────────

    def trend_components(self) -> Optional[pd.DataFrame]:
        """Trend ve mevsimsellik bileşenlerini döndürür."""
        if self._forecast_df is None:
            return None
        cols = ["ds", "trend"]
        if "yearly" in self._forecast_df.columns:
            cols.append("yearly")
        return self._forecast_df[cols]

    def _trend_direction(self, tahmin_df: pd.DataFrame) -> str:
        if tahmin_df.empty or len(tahmin_df) < 2:
            return "Belirsiz"
        ilk = tahmin_df["yhat"].iloc[0]
        son  = tahmin_df["yhat"].iloc[-1]
        if ilk == 0:
            return "Belirsiz"
        degisim = (son - ilk) / abs(ilk) * 100
        if degisim > 5:
            return "Yükseliş 📈"
        elif degisim < -5:
            return "Düşüş 📉"
        return "Stabil ➡️"

    # ─────────────────────────────────────────
    # ANOMALİ TESPİTİ
    # ─────────────────────────────────────────

    def detect_anomalies(self) -> pd.DataFrame:
        """
        Gerçek değerlerin güven aralığı dışına çıktığı noktaları tespit eder.
        """
        if self._forecast_df is None or not self._trained:
            self.train()
            future = self._model.make_future_dataframe(periods=0, freq="MS")
            self._forecast_df = self._model.predict(future)

        merged = self._train_data.merge(
            self._forecast_df[["ds", "yhat_lower", "yhat_upper"]],
            on="ds", how="left"
        )
        merged["anomali"] = (
            (merged["y"] < merged["yhat_lower"]) |
            (merged["y"] > merged["yhat_upper"])
        )
        return merged[merged["anomali"] == True][["ds", "y", "yhat_lower", "yhat_upper"]]

    # ─────────────────────────────────────────
    # ÖZET RAPOR
    # ─────────────────────────────────────────

    def summary_report(self, ay: int = 3) -> Dict[str, Any]:
        """Tahmin + anomali + trend içeren tam özet."""
        fc = self.forecast(ay)
        anomaliler = self.detect_anomalies()

        return {
            **fc,
            "anomali_sayisi": len(anomaliler),
            "anomaliler":     anomaliler,
            "trend_bileseni": self.trend_components(),
        }
