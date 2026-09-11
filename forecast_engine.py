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
        "prophet":     "Prophet (tam model — mevsimsellik + istatistiksel güven aralığı)",
        "statsmodels": "Holt-Winters (orta model — trend + mevsimsellik; senaryo bandı)",
        "linear":      "Lineer Trend (basit projeksiyon; senaryo bandı)",
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
        """Aylık gelir serisini standart formata çevir + eksik ayları 0 ile doldur.

        Codex (#29): _prepare_data eksik ayları atlarsa forecast backend'leri
        ardışık ay üretir ama holdout gerçek ile positional zip yanlış aylara
        denk gelir. Reindex tam aylık grid → holdout eşleşmesi periyot bazlı.
        """
        monthly = (
            self.df.groupby("YilAy")["Gelir"]
            .sum()
            .reset_index()
        )
        if monthly.empty:
            return pd.DataFrame(columns=["ds", "y"])
        monthly["ds"] = pd.to_datetime(monthly["YilAy"], format="%Y-%m")
        monthly = monthly.sort_values("ds").reset_index(drop=True)
        # Tam aylık grid — eksik aylar 0 gelirle doldurulur (KOBİ verisinde
        # 0-satış ayı gerçek bilgi; tahmini bozan boşluk değil).
        tam_grid = pd.date_range(monthly["ds"].iloc[0], monthly["ds"].iloc[-1], freq="MS")
        monthly = monthly.set_index("ds").reindex(tam_grid).rename_axis("ds").reset_index()
        monthly["y"] = monthly["Gelir"].fillna(0.0).clip(lower=0).astype(float)
        return monthly[["ds", "y"]]

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
        # Codex (#29): validation aynı Prophet konfigüyle yeniden eğitmeli.
        self._train_args = {
            "yearly_seasonality": yearly_seasonality,
            "changepoint_prior_scale": changepoint_prior_scale,
        }

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
        """Son 6 aylık trendi baz alan basit lineer regresyon.

        Codex (#29): _forecast_linear polinomu ``len(train_data) + i`` global
        indekste değerlendiriyor. Tail-relative (0..5) koordinatlar bu
        değerlendirmeyi kırıyordu — 21 ay train + 3 ay holdout senaryosunda
        MAPE %0 yerine %20 çıkıyordu. Fit koordinatlarını global indekse
        (n-tail_len..n-1) hizala.
        """
        tail = data.tail(min(6, len(data)))
        n = len(data)
        x = np.arange(n - len(tail), n)  # global indeks — forecast ile aynı eksen
        y = tail["y"].values
        self._model = np.polyfit(x, y, deg=1)  # (slope, intercept)

    # ── Tahmin ────────────────────────────────────────────────────────────────

    def forecast(
        self,
        ay: int = 3,
        enflasyon_yillik: Optional[float] = None,
        dogrula: bool = False,
        dogrulama_ay: int = 3,
    ) -> Dict[str, Any]:
        """
        Tahmin döndürür.

        enflasyon_yillik: opsiyonel yıllık enflasyon oranı (ör. 0.35 = %35).
            Verilirse tahmin tablosuna reel (bugünkü satın alma gücüne göre
            deflate edilmiş) sütunlar eklenir. Nominal sütunlar korunur.
        dogrula: True ise son ``dogrulama_ay`` (varsayılan 3) ay holdout
            olarak ayrılıp motor bu periyoda göre yeniden eğitilir; tahminler
            gerçek ile karşılaştırılıp MAPE hesaplanır. Prophet için ekstra
            eğitim maliyeti olduğundan opt-in bırakıldı. Sonuç
            ``geriye_donuk_mape``, ``mape_holdout_ay`` ve ``guven_seviyesi``
            alanlarında raporlanır. Yetersiz veride sessizce atlanır ve
            ``guven_seviyesi="olcuulmedi"`` döner.
        """
        if not self._trained:
            self.train()

        if PROPHET_AVAILABLE:
            result = self._forecast_prophet(ay)
        elif STATSMODELS_AVAILABLE:
            result = self._forecast_statsmodels(ay)
        else:
            result = self._forecast_linear(ay)

        # Geriye dönük doğrulama (holdout WAPE + MAPE) — opt-in
        # Codex #30: doğrulama çalışmasa da WAPE alanları None ile
        # doldurulmalı; aksi halde caller KeyError alır.
        mape_bilgisi = self._geriye_donuk_mape(dogrulama_ay) if dogrula else None
        if mape_bilgisi is not None:
            result.update(mape_bilgisi)
        else:
            result.setdefault("geriye_donuk_mape", None)
            result.setdefault("geriye_donuk_wape", None)
            result.setdefault("dogrulama_metrigi", None)
            result.setdefault("mape_holdout_ay", dogrulama_ay if dogrula else 0)
            result.setdefault("eslesen_ay", 0)
            result.setdefault(
                "guven_seviyesi",
                "olculmedi" if not dogrula else "olculmedi_veri_yetersiz",
            )

        if enflasyon_yillik is not None and enflasyon_yillik > 0:
            result = self._apply_deflator(result, enflasyon_yillik)

        return result

    def _geriye_donuk_mape(self, holdout_ay: int) -> Optional[Dict[str, Any]]:
        """Walk-forward doğrulama: son N ay holdout, gerisi eğitim.

        Metrik: WAPE (Σ|forecast-actual| / Σ|actual|). Codex (#29): MAPE
        sıfır aktarımlı aylarda tanımsız; eskiden zero-satırları atlıyorduk
        ve tam holdout ay sayısı bildirilirken güven şişik çıkıyordu. WAPE
        sıfır aylara doğal olarak dayanıklı (payda toplamı sıfır değilse
        anlamlı). Ayrıca train() argümanları (yearly_seasonality,
        changepoint_prior_scale) validation'a aynen taşınır.

        Yeterli veri yoksa None döner (çağıran fallback değeri ayarlar).
        Aktif backend ile aynı yolu kullanır (Prophet/statsmodels/linear).
        """
        data = self._train_data
        if data is None or len(data) < holdout_ay + 6 or holdout_ay < 1:
            return None

        train_df = data.iloc[:-holdout_ay].reset_index(drop=True)
        holdout_df = data.iloc[-holdout_ay:].reset_index(drop=True)

        # Aynı backend'te taze motorla eğit + tahmin et
        gecici = ForecastEngine(self.df)
        gecici._train_data = train_df
        train_args = getattr(self, "_train_args", None) or {
            "yearly_seasonality": True,
            "changepoint_prior_scale": 0.05,
        }
        try:
            if PROPHET_AVAILABLE:
                gecici._train_prophet(
                    train_df,
                    yearly_seasonality=train_args["yearly_seasonality"],
                    changepoint_prior_scale=train_args["changepoint_prior_scale"],
                )
                tahmin = gecici._forecast_prophet(holdout_ay)
            elif STATSMODELS_AVAILABLE:
                gecici._train_statsmodels(train_df)
                tahmin = gecici._forecast_statsmodels(holdout_ay)
            else:
                gecici._train_linear(train_df)
                tahmin = gecici._forecast_linear(holdout_ay)
        except Exception:
            return None

        tahmin_df = tahmin["tahmin_tablosu"]
        # Periyot bazlı hizalama — positional zip yerine ay etiketiyle join.
        # (_prepare_data artık tam grid reindex yapıyor; boşluk 0 gelirdir.)
        tahmin_haritasi = {
            row["Dönem"]: float(row["Tahmin"])
            for _, row in tahmin_df.iterrows()
        }
        eslesen = []
        for _, gercek_satir in holdout_df.iterrows():
            donem = gercek_satir["ds"].strftime("%Y-%m")
            tahmin_v = tahmin_haritasi.get(donem)
            if tahmin_v is None:
                continue
            eslesen.append((tahmin_v, float(gercek_satir["y"])))

        # Yeterli örneklem: holdout aylarının en az yarısı eşleşmeli
        if len(eslesen) < max(1, holdout_ay // 2 + 1):
            return None

        toplam_gercek = sum(abs(g) for _, g in eslesen)
        toplam_hata = sum(abs(t - g) for t, g in eslesen)
        if toplam_gercek == 0:
            # Payda sıfır — WAPE tanımsız. Karar için sinyal yok.
            return None

        wape = round(toplam_hata / toplam_gercek * 100, 2)

        # Codex #30: geriye_donuk_mape gerçek MAPE olmalı, WAPE kopyası değil.
        # MAPE = mean(|f-g|/|g|); yalnızca tüm gerçekler > 0 iken tanımlı.
        # Sıfır ay varsa MAPE None döner; caller güveni WAPE üzerinden okur.
        if all(g > 0 for _, g in eslesen):
            mape = round(
                sum(abs(t - g) / g for t, g in eslesen) / len(eslesen) * 100, 2
            )
        else:
            mape = None

        if wape <= 10:
            guven = "yuksek"
        elif wape <= 25:
            guven = "orta"
        else:
            guven = "dusuk"
        return {
            "geriye_donuk_wape": wape,
            "geriye_donuk_mape": mape,  # None if any holdout actual is 0
            "mape_holdout_ay":   holdout_ay,
            "eslesen_ay":        len(eslesen),
            "dogrulama_metrigi": "WAPE",
            "guven_seviyesi":    guven,
        }

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

        # Prophet gerçek istatistiksel aralık üretir; statsmodels/linear'de
        # bant sabit yüzdedir (senaryo bandı), güven aralığı değildir.
        band_turu = "istatistiksel" if ACTIVE_BACKEND == "prophet" else "senaryo"

        return {
            "tahmin_tablosu":    tahmin_df,
            "band_turu":         band_turu,
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

    def summary_report(
        self,
        ay: int = 3,
        enflasyon_yillik: Optional[float] = None,
    ) -> Dict[str, Any]:
        fc = self.forecast(ay, enflasyon_yillik=enflasyon_yillik)
        anomaliler = self.detect_anomalies()
        return {
            **fc,
            "anomali_sayisi": len(anomaliler),
            "anomaliler":     anomaliler,
            "trend_bileseni": self.trend_components(),
        }
