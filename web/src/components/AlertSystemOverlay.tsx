import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  AlertTriangle,
  ShieldAlert,
  X,
  Bell,
  Volume2,
  VolumeX,
  ArrowRight,
  CheckCircle2,
  Flame,
  Activity,
  TrendingDown,
  PieChart,
  Settings,
  Bot,
  Zap,
  RotateCcw,
  Sliders,
  Sparkles,
  Info
} from 'lucide-react';
import { useAlerts } from '../context/AlertContext';
import { FinancialAlert } from '../types';

interface AlertSystemOverlayProps {
  onNavigateTab: (tabId: string) => void;
}

export const AlertSystemOverlay: React.FC<AlertSystemOverlayProps> = ({ onNavigateTab }) => {
  const showSimulationTools = import.meta.env.VITE_ENABLE_SIMULATION_TOOLS === 'true';
  const {
    alerts,
    toasts,
    unreadCount,
    activeModalAlert,
    setActiveModalAlert,
    markAsRead,
    markAllAsRead,
    clearAlert,
    dismissToast,
    triggerBudgetTestAlert,
    triggerCashflowTestAlert,
    runFullFinancialScan,
    thresholds,
    updateThresholds,
    isMuted,
    toggleSound,
  } = useAlerts();

  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'budget' | 'cashflow'>('all');

  // Filter alerts for drawer
  const filteredAlerts = alerts.filter(a => {
    if (activeFilter === 'budget') return a.type === 'budget_exceeded';
    if (activeFilter === 'cashflow') return a.type === 'cashflow_drop';
    return true;
  });

  const hasUnreadCritical = alerts.some(a => !a.read && a.severity === 'critical');

  return (
    <>
      {/* 1. PULSING SCREEN CORNER SIREN BEACON EFFECT (When critical unread alert exists) */}
      {hasUnreadCritical && (
        <div className="fixed top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none z-30 animate-pulse" />
      )}

      {/* 2. FLOATING TOAST NOTIFICATION STACK */}
      <div className="fixed left-3 right-3 top-20 z-50 flex flex-col gap-3 pointer-events-none sm:left-auto sm:right-6 sm:w-full sm:max-w-md">
        <AnimatePresence>
          {toasts.map((toast) => {
            const isCritical = toast.severity === 'critical';
            return (
              <motion.div
                key={toast.toastId}
                initial={{ opacity: 0, x: 80, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 100, scale: 0.8 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                className={`pointer-events-auto rounded-xs p-4 border shadow-2xl backdrop-blur-xl relative overflow-hidden ${
                  isCritical
                    ? 'bg-[#181010]/95 border-red-500/60 text-white ring-1 ring-red-500/30'
                    : 'bg-[#181610]/95 border-amber-500/60 text-white ring-1 ring-amber-500/30'
                }`}
              >
                {/* Laser scanline pulse line */}
                <div
                  className={`absolute top-0 left-0 right-0 h-1 ${
                    isCritical ? 'bg-gradient-to-r from-red-600 via-rose-400 to-red-600 animate-pulse' : 'bg-gradient-to-r from-amber-500 via-yellow-300 to-amber-500'
                  }`}
                />

                <div className="flex items-start justify-between gap-3 pt-1">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-xs shrink-0 mt-0.5 ${
                      isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                    }`}>
                      {isCritical ? <ShieldAlert className="w-5 h-5 animate-bounce" /> : <AlertTriangle className="w-5 h-5" />}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono font-extrabold uppercase px-1.5 py-0.2 rounded-xs ${
                          isCritical ? 'bg-red-500 text-white' : 'bg-amber-500 text-black font-bold'
                        }`}>
                          {isCritical ? 'KRİTİK UYARI' : 'BÜTÇE RİSKİ'}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">{toast.timestamp}</span>
                      </div>

                      <h4 className="text-xs font-display font-bold text-white leading-tight">
                        {toast.title}
                      </h4>

                      <p className="text-[11px] text-slate-300 leading-snug line-clamp-2">
                        {toast.message}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => dismissToast(toast.toastId)}
                    aria-label={`${toast.title} bildirimini kapat`}
                    className="text-slate-400 hover:text-white p-1 rounded-xs hover:bg-white/10 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Actions Bar */}
                <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-xs font-mono">
                  <span className="text-[10px] text-slate-400">
                    {toast.threshold || 'Sistem Uyarısı'}
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        dismissToast(toast.toastId);
                        setActiveModalAlert(toast);
                      }}
                      className="text-[11px] font-bold text-[#FF4D00] hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
                    >
                      <span>Teşhis Et</span>
                      <Zap className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => {
                        dismissToast(toast.toastId);
                        markAsRead(toast.id);
                        onNavigateTab(toast.actionTab);
                      }}
                      className="bg-white/10 hover:bg-white/20 text-white font-bold text-[10px] px-2.5 py-1 rounded-xs flex items-center gap-1 transition-colors cursor-pointer border border-white/15"
                    >
                      <span>{toast.actionLabel}</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* 3. HEADER BELL BADGE TRIGGER (Floating Action Bar or Drawer Trigger) */}
      <div className="fixed bottom-4 left-4 right-4 z-40 flex items-center justify-end gap-2 sm:bottom-6 sm:left-auto sm:right-6">
        {/* Sound Toggle Floating Button */}
        <button
          onClick={toggleSound}
          title={isMuted ? 'Sesli Uyarıları Aç' : 'Sesli Uyarıları Sessize Al'}
          aria-label={isMuted ? 'Sesli uyarıları aç' : 'Sesli uyarıları sessize al'}
          className={`shrink-0 rounded-xl border p-3 shadow-xl backdrop-blur-md transition-all cursor-pointer ${
            isMuted
              ? 'bg-[#18181b]/90 text-slate-500 border-white/10 hover:bg-white/10'
              : 'bg-[#FF4D00]/20 text-[#FF4D00] border-[#FF4D00]/40 hover:bg-[#FF4D00]/30'
          }`}
        >
          {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
        </button>

        {/* Notification Drawer Toggle Button */}
        <button
          onClick={() => setIsNotificationCenterOpen(!isNotificationCenterOpen)}
          aria-label={`Uyarı merkezini ${isNotificationCenterOpen ? 'kapat' : 'aç'}${unreadCount ? `, ${unreadCount} okunmamış uyarı` : ''}`}
          aria-expanded={isNotificationCenterOpen}
          className={`relative min-w-0 rounded-xl border px-3 py-3 shadow-2xl backdrop-blur-md font-mono font-bold text-xs flex items-center gap-2 transition-all cursor-pointer sm:px-4 ${
            unreadCount > 0
              ? 'bg-[#FF4D00] text-white border-[#FF4D00] hover:bg-[#e04400] ring-2 ring-[#FF4D00]/40'
              : 'bg-[#18181b]/90 text-slate-200 border-white/15 hover:bg-white/10'
          }`}
        >
          <Bell className={`w-4 h-4 ${unreadCount > 0 ? 'animate-bounce' : ''}`} />
          <span className="truncate">UYARI MERKEZİ</span>

          {unreadCount > 0 && (
            <span className="bg-white text-[#FF4D00] text-[10px] font-black px-1.5 py-0.2 rounded-xs font-mono ml-1">
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* 4. NOTIFICATION CENTER DRAWER / PANEL */}
      <AnimatePresence>
        {isNotificationCenterOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsNotificationCenterOpen(false)}
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            />

            <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className="w-screen max-w-md bg-[#111113] border-l border-white/15 shadow-2xl flex flex-col justify-between"
              >
                {/* Header */}
                <div className="p-5 border-b border-white/10 space-y-3 bg-[#18181b]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xs bg-[#FF4D00]/20 border border-[#FF4D00]/40 flex items-center justify-center text-[#FF4D00]">
                        <ShieldAlert className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="text-base font-display font-bold text-white tracking-tight">
                          Canlı Uyarı & Risk Yönetimi
                        </h3>
                        <p className="text-xs font-mono text-slate-400">
                          Bütçe ve Nakit Akışı İkaz Protokolü
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setIsSettingsOpen(true)}
                        title="Eşik Ayarları"
                        aria-label="Uyarı eşik ayarlarını aç"
                        className="p-2 text-slate-400 hover:text-white rounded-xs hover:bg-white/10 transition-colors"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setIsNotificationCenterOpen(false)}
                        aria-label="Uyarı merkezini kapat"
                        className="p-2 text-slate-400 hover:text-white rounded-xs hover:bg-white/10 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Quick Filter Tabs */}
                  <div className="flex items-center justify-between pt-1 font-mono text-xs">
                    <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xs border border-white/10">
                      <button
                        onClick={() => setActiveFilter('all')}
                        className={`px-2.5 py-1 rounded-xs transition-colors ${
                          activeFilter === 'all' ? 'bg-[#FF4D00] text-white font-bold' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Tümü ({alerts.length})
                      </button>
                      <button
                        onClick={() => setActiveFilter('budget')}
                        className={`px-2.5 py-1 rounded-xs transition-colors ${
                          activeFilter === 'budget' ? 'bg-[#FF4D00] text-white font-bold' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Bütçe
                      </button>
                      <button
                        onClick={() => setActiveFilter('cashflow')}
                        className={`px-2.5 py-1 rounded-xs transition-colors ${
                          activeFilter === 'cashflow' ? 'bg-[#FF4D00] text-white font-bold' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Nakit
                      </button>
                    </div>

                    {unreadCount > 0 && (
                      <button
                        onClick={markAllAsRead}
                        className="text-[11px] text-[#FF4D00] hover:underline cursor-pointer font-bold"
                      >
                        Tümünü Okundu İşaretle
                      </button>
                    )}
                  </div>
                </div>

                {/* Alert List Body */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar">
                  {/* Simulation Trigger Bar */}
                  {showSimulationTools && <div className="p-3 bg-white/[0.03] rounded-xs border border-white/10 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-300">
                      <span className="flex items-center gap-1 font-bold text-[#FF4D00]">
                        <Zap className="w-3.5 h-3.5" />
                        CANLI UYARI SİSTEMİ TEST PANELİ
                      </span>
                      <span className="text-[10px] text-slate-500">Özel Efekt Simülasyonu</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                      <button
                        onClick={() => triggerBudgetTestAlert('Pazarlama & Reklam', 185000)}
                        className="bg-red-950/60 hover:bg-red-900/80 text-red-200 border border-red-800/60 py-2 px-2.5 rounded-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-[11px]"
                      >
                        <Flame className="w-3.5 h-3.5 text-red-400 shrink-0" />
                        <span>Bütçe Aşımı Tetikle</span>
                      </button>

                      <button
                        onClick={() => triggerCashflowTestAlert(450000)}
                        className="bg-amber-950/60 hover:bg-amber-900/80 text-amber-200 border border-amber-800/60 py-2 px-2.5 rounded-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-[11px]"
                      >
                        <TrendingDown className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>Nakit Düşüşü Tetikle</span>
                      </button>
                    </div>

                    <button
                      onClick={runFullFinancialScan}
                      className="w-full bg-white/5 hover:bg-white/10 text-slate-200 border border-white/15 py-1.5 px-3 rounded-xs text-[11px] font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-[#FF4D00]" />
                      <span>Tüm Finansal Taramayı Yeniden Çalıştır</span>
                    </button>
                  </div>}

                  {filteredAlerts.length === 0 ? (
                    <div className="text-center py-12 space-y-2 text-slate-500 font-mono text-xs">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                      <p>Kayıtlı aktif uyarı bulunmuyor.</p>
                    </div>
                  ) : (
                    filteredAlerts.map((alert) => {
                      const isCritical = alert.severity === 'critical';
                      return (
                        <div
                          key={alert.id}
                          className={`p-3.5 rounded-xs border transition-all space-y-2 relative ${
                            !alert.read
                              ? isCritical
                                ? 'bg-red-950/30 border-red-500/50 text-white'
                                : 'bg-amber-950/30 border-amber-500/50 text-white'
                              : 'bg-white/[0.02] border-white/10 text-slate-300'
                          }`}
                        >
                          {!alert.read && (
                            <span className="absolute top-3 right-3 w-2 h-2 rounded-full bg-[#FF4D00] animate-ping" />
                          )}

                          <div className="flex items-start justify-between gap-2">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 font-mono text-[10px]">
                                <span className={`px-1.5 py-0.2 rounded-xs font-bold uppercase ${
                                  isCritical ? 'bg-red-500 text-white' : 'bg-amber-500 text-black'
                                }`}>
                                  {alert.type === 'budget_exceeded' ? 'BÜTÇE' : 'NAKİT'}
                                </span>
                                <span className="text-slate-400">{alert.timestamp}</span>
                              </div>

                              <h4 className="text-xs font-bold text-white leading-snug">
                                {alert.title}
                              </h4>
                            </div>
                          </div>

                          <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                            {alert.message}
                          </p>

                          <div className="pt-2 border-t border-white/10 flex items-center justify-between text-xs font-mono">
                            <button
                              onClick={() => {
                                markAsRead(alert.id);
                                setActiveModalAlert(alert);
                                setIsNotificationCenterOpen(false);
                              }}
                              className="text-[#FF4D00] hover:underline font-bold text-[11px] flex items-center gap-1 cursor-pointer"
                            >
                              <Zap className="w-3 h-3" />
                              <span>Teşhis Raporu</span>
                            </button>

                            <button
                              onClick={() => {
                                markAsRead(alert.id);
                                setIsNotificationCenterOpen(false);
                                onNavigateTab(alert.actionTab);
                              }}
                              className="bg-white/10 hover:bg-white/20 text-white px-2.5 py-1 rounded-xs text-[10px] font-bold flex items-center gap-1 cursor-pointer"
                            >
                              <span>{alert.actionLabel}</span>
                              <ArrowRight className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 bg-[#18181b] text-xs font-mono text-slate-400 flex items-center justify-between">
                  <span>Ses Efektleri: <strong>{isMuted ? 'Kapalı' : 'Açık'}</strong></span>
                  <button
                    onClick={toggleSound}
                    className="text-xs text-[#FF4D00] hover:underline font-bold cursor-pointer"
                  >
                    {isMuted ? 'Sesi Aç' : 'Sessize Al'}
                  </button>
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* 5. INTERACTIVE DIAGNOSTIC MODAL (Full diagnostic breakdown on critical alert) */}
      <AnimatePresence>
        {activeModalAlert && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="diagnostic-modal-title"
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="max-w-xl w-full bg-[#18181b] border border-[#FF4D00]/50 rounded-xs shadow-2xl overflow-hidden relative"
            >
              {/* Header with laser bar */}
              <div className="bg-gradient-to-r from-red-950 via-[#18181b] to-red-950 p-5 border-b border-white/10 relative">
                <div className="h-1 bg-gradient-to-r from-red-500 via-[#FF4D00] to-red-500 absolute top-0 left-0 right-0 animate-pulse" />

                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-red-500/20 text-red-400 border border-red-500/40 rounded-xs">
                      <ShieldAlert className="w-6 h-6 animate-bounce" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono font-bold text-red-400 uppercase tracking-widest block">
                        FİNANSAL TEŞHİS PROTOKOLÜ #402
                      </span>
                      <h3 id="diagnostic-modal-title" className="text-lg font-display font-bold text-white">
                        {activeModalAlert.title}
                      </h3>
                    </div>
                  </div>

                  <button
                    onClick={() => setActiveModalAlert(null)}
                    aria-label="Teşhis penceresini kapat"
                    className="p-1.5 text-slate-400 hover:text-white rounded-xs hover:bg-white/10 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-5">
                {/* Impact Stat */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/5 p-3 rounded-xs border border-white/10 font-mono">
                    <span className="text-[10px] text-slate-400 block">TESPİT EDİLEN ETKİ TUTARI</span>
                    <div className="text-xl font-bold text-red-400">
                      {activeModalAlert.amount ? `₺${Math.abs(activeModalAlert.amount).toLocaleString('tr-TR')}` : 'Belirtilmedi'}
                    </div>
                  </div>

                  <div className="bg-white/5 p-3 rounded-xs border border-white/10 font-mono">
                    <span className="text-[10px] text-slate-400 block">UYARI DÜZEYİ & EŞİK</span>
                    <div className="text-sm font-bold text-amber-400 mt-1">
                      {activeModalAlert.threshold || 'Kritik Sınır Aşıldı'}
                    </div>
                  </div>
                </div>

                {/* Diagnostic Description */}
                <div className="space-y-2">
                  <span className="text-xs font-mono text-slate-400 block">DETAYLI RİSK ANALİZİ & AÇIKLAMA</span>
                  <div className="p-4 bg-white/[0.02] border border-white/10 rounded-xs text-sm text-slate-200 leading-relaxed font-sans">
                    {activeModalAlert.message}
                  </div>
                </div>

                {/* AI CFO Recommendation */}
                <div className="p-4 bg-[#FF4D00]/10 border border-[#FF4D00]/30 rounded-xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#FF4D00]">
                    <Bot className="w-4 h-4" />
                    <span>AI CFO AKSİYON DEĞERLENDİRMESİ</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    Bu uyarının dayandığı metrikleri ve veri kapsamını inceleyin. AI CFO olası aksiyonları karşılaştırabilir; ödeme, borç ve yatırım kararları yetkili insan onayı olmadan uygulanmaz.
                  </p>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="p-5 border-t border-white/10 bg-[#111113] flex flex-col sm:flex-row items-center justify-between gap-3">
                <button
                  onClick={() => setActiveModalAlert(null)}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xs border border-white/15 text-slate-300 text-xs font-mono hover:bg-white/10 transition-colors cursor-pointer"
                >
                  Kapat
                </button>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <button
                    onClick={() => {
                      const tab = activeModalAlert.actionTab;
                      setActiveModalAlert(null);
                      onNavigateTab(tab);
                    }}
                    className="flex-1 sm:flex-initial bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold px-4 py-2.5 rounded-xs border border-white/15 transition-colors cursor-pointer"
                  >
                    {activeModalAlert.actionLabel}
                  </button>

                  <button
                    onClick={() => {
                      setActiveModalAlert(null);
                      onNavigateTab('cfo-agent');
                    }}
                    className="flex-1 sm:flex-initial bg-[#FF4D00] hover:bg-[#e04400] text-white text-xs font-bold px-4 py-2.5 rounded-xs transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-md"
                  >
                    <Bot className="w-4 h-4" />
                    <span>AI CFO ile Aksiyon Planı Al</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 6. THRESHOLD SETTINGS MODAL */}
      <AnimatePresence>
        {isSettingsOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="threshold-settings-title"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="max-w-md w-full bg-[#18181b] border border-white/15 rounded-xs p-6 space-y-5 shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <div className="flex items-center gap-2">
                  <Sliders className="w-5 h-5 text-[#FF4D00]" />
                  <h3 id="threshold-settings-title" className="text-base font-display font-bold text-white">Uyarı Eşik Ayarları</h3>
                </div>
                <button
                  onClick={() => setIsSettingsOpen(false)}
                  aria-label="Uyarı eşik ayarlarını kapat"
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 font-mono text-xs">
                <div>
                  <label className="text-slate-300 block mb-1">
                    Bütçe Aşım Toleransı (%)
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="1"
                      max="25"
                      value={thresholds.budgetOverrunPercent}
                      onChange={(e) => updateThresholds({ budgetOverrunPercent: Number(e.target.value) })}
                      className="flex-1 accent-[#FF4D00] cursor-pointer"
                    />
                    <span className="font-bold text-[#FF4D00] w-12 text-right">%{thresholds.budgetOverrunPercent}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">Harcama bütçeyi %{thresholds.budgetOverrunPercent} aştığında bildirim verilir.</span>
                </div>

                <div>
                  <label className="text-slate-300 block mb-1">
                    Kritik Nakit Düşüş Eşiği (₺)
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="50000"
                      max="500000"
                      step="25000"
                      value={thresholds.cashflowDropTRY}
                      onChange={(e) => updateThresholds({ cashflowDropTRY: Number(e.target.value) })}
                      className="flex-1 accent-[#FF4D00] cursor-pointer"
                    />
                    <span className="font-bold text-[#FF4D00] w-20 text-right">₺{(thresholds.cashflowDropTRY / 1000).toFixed(0)}K</span>
                  </div>
                  <span className="text-[10px] text-slate-500">Nakit akışı tek ayda ₺{thresholds.cashflowDropTRY.toLocaleString('tr-TR')} düştüğünde ikaz verilir.</span>
                </div>
              </div>

              <button
                onClick={() => setIsSettingsOpen(false)}
                className="w-full bg-[#FF4D00] hover:bg-[#e04400] text-white font-bold text-xs py-2.5 rounded-xs transition-colors"
              >
                Kaydet ve Kapat
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
