"""
KazKaz AI - Gelecek Tahmin Motoru
====================================
Backend öncelik sırası:
  1. Prophet (cmdstanpy backend) — en güvenilir, mevsimsellik destekli
  2. statsmodels ExponentialSmoothing — Prophet kurulamadığında devreye girer
  3. Lineer trend — hiçbiri yoksa basit projeksiyon

Streamlit Cloud notu:
  - pystan KULLANILMIYOR (build timeout riski)
  - PROPHET_USE_CMDSTAN=1 env variable Streamlit Secrets'a eklenmelidir
  - Prophet yüklenemezse uygulama sessizce statsmodels'e geçer
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings("ignore")

# ─── Backend tespiti ───────────────────────────────────────────────────────────

PROPHET_AVAILABLE = False
STATSMODELS_AVAILABLE = False
ACTIVE_BACKEND = "linear"   # fallback

try:
    # cmdstanpy backend zorla — pystan'ı bypass eder
    os.environ.setdefault("PROPHET_USE_CMDSTAN", "1")
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    ACTIVE_BACKEND = "prophet"
except Exception:
    pass

if not PROPHET_AVAILABLE:
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        STATSMODELS_AVAILABLE = True
        ACTIVE_BACKEND = "statsmodels"
    except ImportError:
        pass


def get_backend_info() -> Dict[str, str]:
    """UI'da hangi backend'in aktif olduğunu göstermek için."""
    labels = {
        "prophet":     "Prophet (tam model — mevsimsellik + güven aralığı)",
        "statsmodels": "Holt-Winters (orta model — trend + mevsimsellik)",
        "linear":      "Lineer Trend (basit projeksiyon)",
    }
    return {
        "backend": ACTIVE_BACKEND,
        "label":   labels[ACTIVE_BACKEND],
        "tam_model": PROPHET_AVAILABLE,
    }


# ─── Ana Motor ────────────────────────────────────────────────────────────────

class ForecastEngine:
    """
    Çok katmanlı gelir tahmin motoru.
    Prophet → Holt-Winters → Lineer sırasıyla dener.

    Kullanım:
        fc = ForecastEngine(df)
        sonuc = fc.forecast(ay=6)
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._trained = False
        self._model = None
        self._train_data: Optional[pd.DataFrame] = None
        self._forecast_df: Optional[pd.DataFrame] = None
        self.backend = ACTIVE_BACKEND

    # ── Veri Hazırlama ────────────────────────────────────────────────────────

    def _prepare_data(self) -> pd.DataFrame:
        """Aylık gelir serisini standart formata çevir."""
        monthly = (
            self.df.groupby("YilAy")["Gelir"]
            .sum()
            .reset_index()
        )
        monthly["ds"] = pd.to_datetime(monthly["YilAy"], format="%Y-%m")
        monthly["y"]  = monthly["Gelir"].clip(lower=0).astype(float)
        return monthly[["ds", "y"]].sort_values("ds").reset_index(drop=True)

    # ── Eğitim ────────────────────────────────────────────────────────────────

    def train(
        self,
        yearly_seasonality: bool = True,
        changepoint_prior_scale: float = 0.05,
    ) -> "ForecastEngine":
        data = self._prepare_data()

        # Minimum veri şartı — güvenilir tahmin için
        n_ay = len(data)
        if n_ay < 3:
            raise ValueError(
                "Tahmin için en az 3 aylık veri gereklidir. "
                f"Şu an {n_ay} ay veri var."
            )

        # Uyarılar için sakla (tahmin çıktısında gösterilir)
        self._veri_uyarilari = []
        if n_ay < 6:
            self._veri_uyarilari.append(
                f"⚠️ Sadece {n_ay} ay veri var. Tahmin güvenilirliği düşüktür. "
                "En az 6 ay, ideal olarak 12+ ay veri önerilir."
            )
        elif n_ay < 12:
            self._veri_uyarilari.append(
                f"⚠️ {n_ay} ay veri ile mevsimsel örüntü tam yakalanamaz. "
                "Yıllık mevsimsellik için 12+ ay veri önerilir."
            )
        elif n_ay < 24 and PROPHET_AVAILABLE:
            self._veri_uyarilari.append(
                f"ℹ️ {n_ay} ay veri ile Prophet mevsimsellik tespit edebilir "
                "ancak 24+ ay veri sonuçları daha da iyileştirir."
            )

        self._train_data = data

        if PROPHET_AVAILABLE:
            self._train_prophet(data, yearly_seasonality, changepoint_prior_scale)
        elif STATSMODELS_AVAILABLE:
            self._train_statsmodels(data)
            self._veri_uyarilari.append(
                "ℹ️ Prophet yüklü değil, Holt-Winters kullanılıyor. "
                "Güven aralığı istatistiksel değil, ±%15 sabit tahminidir."
            )
        else:
            self._train_linear(data)
            self._veri_uyarilari.append(
                "⚠️ Prophet ve statsmodels yüklü değil, sadece lineer trend kullanılıyor. "
                "Mevsimsellik ve döngüsellik tespit edilmez. Güven aralığı geniş (±%20)."
            )

        self._trained = True
        return self

    def _train_prophet(self, data, yearly_seasonality, changepoint_prior_scale):
        self._model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=changepoint_prior_scale,
            interval_width=0.90,
        )
        # TR resmi tatil regressörü: dini bayramlar (Ramazan, Kurban) her yıl
        # ~11 gün kayar; ulusal tatiller sabit. Prophet'a bunları öğreterek
        # aylık gelirdeki bayram öncesi/sonrası sıçramaları yakalarız.
        # En az 12 ay veri şart — kısa serilerde regressör aşırı-öğrenme yapar.
        self._tr_holidays_active = False
        if len(data) >= 12:
            try:
                self._model.add_country_holidays(country_name="TR")
                self._tr_holidays_active = True
            except Exception:
                pass
        self._model.fit(data)

    def _train_statsmodels(self, data):
        n = len(data)
        # Yıllık mevsimsellik için en az 2 yıl gerekir
        use_seasonal = n >= 24
        self._model = ExponentialSmoothing(
            data["y"].values,
            trend="add",
            seasonal="add" if use_seasonal else None,
            seasonal_periods=12 if use_seasonal else None,
            initialization_method="estimated",
        ).fit(optimized=True)

    def _train_linear(self, data):
        """Son 6 aylık trendi baz alan basit lineer regresyon."""
        tail = data.tail(min(6, len(data)))
        x = np.arange(len(tail))
        y = tail["y"].values
        self._model = np.polyfit(x, y, deg=1)  # (slope, intercept)

    # ── Tahmin ────────────────────────────────────────────────────────────────

    def forecast(
        self,
        ay: int = 3,
        enflasyon_yillik: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Tahmin döndürür.

        enflasyon_yillik: opsiyonel yıllık enflasyon oranı (ör. 0.35 = %35).
            Verilirse tahmin tablosuna reel (bugünkü satın alma gücüne göre
            deflate edilmiş) sütunlar eklenir. Nominal sütunlar korunur.
        """
        if not self._trained:
            self.train()

        if PROPHET_AVAILABLE:
            result = self._forecast_prophet(ay)
        elif STATSMODELS_AVAILABLE:
            result = self._forecast_statsmodels(ay)
        else:
            result = self._forecast_linear(ay)

        if enflasyon_yillik is not None and enflasyon_yillik > 0:
            result = self._apply_deflator(result, enflasyon_yillik)

        return result

    @staticmethod
    def _apply_deflator(result: Dict[str, Any], enflasyon_yillik: float) -> Dict[str, Any]:
        """
        Nominal tahmini reel değere çevir (bugünkü satın alma gücü).
        Aylık deflatör: (1 + yıllık)^(1/12) - 1
        t. ay için: reel_t = nominal_t / (1 + aylık_infl)^t
        """
        tahmin_df = result["tahmin_tablosu"].copy()
        aylik_infl = (1 + enflasyon_yillik) ** (1 / 12) - 1

        deflators = [1 / (1 + aylik_infl) ** (t + 1) for t in range(len(tahmin_df))]
        tahmin_df["Tahmin (Reel ₺)"] = [
            round(v * d, 0) for v, d in zip(tahmin_df["Tahmin"], deflators)
        ]
        tahmin_df["Alt Sınır (Reel ₺)"] = [
            round(v * d, 0) for v, d in zip(tahmin_df["Alt Sınır"], deflators)
        ]
        tahmin_df["Üst Sınır (Reel ₺)"] = [
            round(v * d, 0) for v, d in zip(tahmin_df["Üst Sınır"], deflators)
        ]

        result["tahmin_tablosu"] = tahmin_df
        result["enflasyon_uygulandi"] = enflasyon_yillik
        result["toplam_tahmin_reel"] = float(tahmin_df["Tahmin (Reel ₺)"].sum())
        result["metodoloji_notu"] = (
            f"Tahmin nominal ₺'dir. Reel sütunlar yıllık %{enflasyon_yillik*100:.1f} "
            "enflasyon deflatörü ile bugünkü satın alma gücüne çevrilmiştir. "
            "Reel büyüme = nominal büyüme − enflasyon."
        )
        return result

    def _forecast_prophet(self, ay: int) -> Dict[str, Any]:
        future = self._model.make_future_dataframe(periods=ay, freq="MS")
        forecast = self._model.predict(future)
        self._forecast_df = forecast

        train_len     = len(self._train_data)
        tahmin_donemi = forecast.iloc[train_len:]

        rows = []
        for _, row in tahmin_donemi.iterrows():
            rows.append({
                "Dönem":     row["ds"].strftime("%Y-%m"),
                "Tahmin":    max(0, round(row["yhat"], 0)),
                "Alt Sınır": max(0, round(row["yhat_lower"], 0)),
                "Üst Sınır": max(0, round(row["yhat_upper"], 0)),
            })
        tahmin_df = pd.DataFrame(rows)

        return self._build_result(tahmin_df, tahmin_donemi["yhat"].values)

    def _forecast_statsmodels(self, ay: int) -> Dict[str, Any]:
        forecast_vals = self._model.forecast(ay)
        forecast_vals = np.clip(forecast_vals, 0, None)

        # Holt-Winters güven aralığı: ±%15 yorum aralığı
        rows = []
        last_ds = self._train_data["ds"].iloc[-1]
        for i, val in enumerate(forecast_vals):
            period = last_ds + pd.DateOffset(months=i + 1)
            margin = val * 0.15
            rows.append({
                "Dönem":     period.strftime("%Y-%m"),
                "Tahmin":    round(val, 0),
                "Alt Sınır": round(max(0, val - margin), 0),
                "Üst Sınır": round(val + margin, 0),
            })
        tahmin_df = pd.DataFrame(rows)

        return self._build_result(tahmin_df, forecast_vals)

    def _forecast_linear(self, ay: int) -> Dict[str, Any]:
        slope, intercept = self._model
        n = len(self._train_data)

        rows = []
        vals = []
        last_ds = self._train_data["ds"].iloc[-1]
        for i in range(ay):
            val = max(0, slope * (n + i) + intercept)
            vals.append(val)
            period = last_ds + pd.DateOffset(months=i + 1)
            margin = abs(val) * 0.20  # lineer'de belirsizlik daha yüksek
            rows.append({
                "Dönem":     period.strftime("%Y-%m"),
                "Tahmin":    round(val, 0),
                "Alt Sınır": round(max(0, val - margin), 0),
                "Üst Sınır": round(val + margin, 0),
            })
        tahmin_df = pd.DataFrame(rows)

        return self._build_result(tahmin_df, np.array(vals))

    def _build_result(self, tahmin_df: pd.DataFrame, yhat_vals: np.ndarray) -> Dict[str, Any]:
        son_gercek  = float(self._train_data["y"].iloc[-1])
        son_tahmin  = float(yhat_vals[-1]) if len(yhat_vals) > 0 else son_gercek
        buyume_oran = ((son_tahmin - son_gercek) / son_gercek * 100) if son_gercek > 0 else 0

        uyarilar = list(getattr(self, "_veri_uyarilari", []))
        # Backend'e özgü güven notu
        if ACTIVE_BACKEND == "linear":
            guven_notu = "Tahmin sadece son 6 ayın doğrusal trendine dayanır."
        elif ACTIVE_BACKEND == "statsmodels":
            guven_notu = "Güven aralığı istatistiksel değil, ±%15 sabit tahminidir."
        else:
            tr_ek = " TR resmi tatil regressörü aktif." if getattr(self, "_tr_holidays_active", False) else ""
            guven_notu = f"Güven aralığı %90 (Prophet default).{tr_ek}"

        return {
            "tahmin_tablosu":    tahmin_df,
            "trend_yonu":        self._trend_direction(yhat_vals),
            "toplam_tahmin":     float(tahmin_df["Tahmin"].sum()),
            "ortalama_tahmin":   float(tahmin_df["Tahmin"].mean()),
            "buyume_beklentisi": round(buyume_oran, 2),
            "ay_sayisi":         len(tahmin_df),
            "backend":           ACTIVE_BACKEND,
            "backend_label":     get_backend_info()["label"],
            "guven_notu":        guven_notu,
            "veri_uyarilari":    uyarilar,
            "metodoloji_notu":   (
                "Tahmin nominal değerlere dayanır — enflasyon düzeltmesi uygulanmamıştır. "
                "Tahmin edilen büyüme reel değil, nominal büyümedir."
            ),
            # Prophet'ta dolu gelir, diğerlerinde None
            "tam_forecast":      self._forecast_df[["ds","yhat","yhat_lower","yhat_upper","trend"]]
                                 if self._forecast_df is not None else None,
        }

    # ── Trend ─────────────────────────────────────────────────────────────────

    def _trend_direction(self, yhat_vals: np.ndarray) -> str:
        if len(yhat_vals) < 2:
            return "Belirsiz"
        ilk, son = float(yhat_vals[0]), float(yhat_vals[-1])
        if ilk == 0:
            return "Belirsiz"
        degisim = (son - ilk) / abs(ilk) * 100
        if degisim > 5:
            return "Yükseliş 📈"
        elif degisim < -5:
            return "Düşüş 📉"
        return "Stabil ➡️"

    def trend_components(self) -> Optional[pd.DataFrame]:
        """Sadece Prophet backend'inde dolu döner."""
        if self._forecast_df is None:
            return None
        cols = ["ds", "trend"]
        if "yearly" in self._forecast_df.columns:
            cols.append("yearly")
        return self._forecast_df[cols]

    # ── Anomali ───────────────────────────────────────────────────────────────

    def detect_anomalies(self) -> pd.DataFrame:
        """
        Prophet: güven aralığı dışına çıkan noktalar.
        Diğerleri: ±2 standart sapma kuralı.
        """
        if not self._trained:
            self.train()

        data = self._train_data.copy()

        if PROPHET_AVAILABLE and self._forecast_df is not None:
            merged = data.merge(
                self._forecast_df[["ds", "yhat_lower", "yhat_upper"]],
                on="ds", how="left"
            )
            merged["anomali"] = (
                (merged["y"] < merged["yhat_lower"]) |
                (merged["y"] > merged["yhat_upper"])
            )
        else:
            mu  = data["y"].mean()
            std = data["y"].std()
            merged = data.copy()
            merged["yhat_lower"] = mu - 2 * std
            merged["yhat_upper"] = mu + 2 * std
            merged["anomali"] = (
                (merged["y"] < merged["yhat_lower"]) |
                (merged["y"] > merged["yhat_upper"])
            )

        return merged[merged["anomali"]][["ds", "y", "yhat_lower", "yhat_upper"]].reset_index(drop=True)

    # ── Tam Özet ──────────────────────────────────────────────────────────────

    def summary_report(self, ay: int = 3) -> Dict[str, Any]:
        fc = self.forecast(ay)
        anomaliler = self.detect_anomalies()
        return {
            **fc,
            "anomali_sayisi": len(anomaliler),
            "anomaliler":     anomaliler,
            "trend_bileseni": self.trend_components(),
        }
