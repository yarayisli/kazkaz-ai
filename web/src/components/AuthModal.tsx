import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, LogIn, UserPlus, X, AlertCircle, Lock, MailCheck, KeyRound } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { loginWithGoogle, loginWithEmail, signUpWithEmail, resetPassword, enableGuestMode } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup' | 'reset'>('login');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const dialog = dialogRef.current;
    window.requestAnimationFrame(() => {
      dialog?.querySelector<HTMLElement>(mode === 'signup' ? '#auth-display-name' : '#auth-email')?.focus();
    });
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key !== 'Tab' || !dialog) return;
      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'));
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [isOpen, mode, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);

    try {
      if (mode === 'login') {
        await loginWithEmail(email, password);
      } else if (mode === 'signup') {
        await signUpWithEmail(email, password, displayName || 'Kullanıcı');
      } else {
        await resetPassword(email);
        setNotice('Bu e-postayla bir hesap varsa şifre yenileme bağlantısı gönderildi. Gelen kutusu ve spam klasörünü kontrol edin.');
        return;
      }
      onClose();
    } catch (err: any) {
      console.error('Auth error:', err);
      if (mode === 'reset' && err.code === 'auth/user-not-found') {
        setNotice('Bu e-postayla bir hesap varsa şifre yenileme bağlantısı gönderildi. Gelen kutusu ve spam klasörünü kontrol edin.');
      } else if (err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') {
        setError('E-posta adresi veya şifre hatalı. Şifrenizi unuttuysanız yenileme bağlantısını kullanın.');
      } else if (err.code === 'auth/email-already-in-use') {
        setError('Bu e-posta adresi zaten kayıtlı.');
      } else if (err.code === 'auth/weak-password') {
        setError('Şifre en az 6 karakter olmalıdır.');
      } else if (err.code === 'auth/invalid-email' || err.code === 'auth/missing-email') {
        setError('Geçerli bir e-posta adresi yazın.');
      } else if (err.code === 'auth/user-disabled') {
        setError('Bu hesap devre dışı bırakılmış. Destek ekibiyle iletişime geçin.');
      } else if (err.code === 'auth/operation-not-allowed') {
        setError('E-posta/şifre ile giriş Firebase panelinde henüz etkinleştirilmemiş.');
      } else if (err.code === 'auth/network-request-failed') {
        setError('Firebase sunucusuna ulaşılamadı. İnternet bağlantısını ve proje ayarlarını kontrol edin.');
      } else if (err.code === 'auth/too-many-requests') {
        setError('Çok fazla deneme yapıldı. Kısa süre bekleyip yeniden deneyin.');
      } else {
        setError('Kimlik doğrulama işlemi tamamlanamadı. Biraz sonra yeniden deneyin.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogle = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await loginWithGoogle();
      onClose();
    } catch (err: any) {
      if (err.code === 'auth/popup-blocked') {
        setError('Google giriş penceresi tarayıcı tarafından engellendi. Pop-up izni verip yeniden deneyin.');
      } else if (err.code === 'auth/unauthorized-domain') {
        setError('Bu alan adı Firebase Authorized domains listesinde değil.');
      } else if (err.code === 'auth/operation-not-allowed') {
        setError('Google sağlayıcısı Firebase Authentication panelinde etkin değil.');
      } else if (err.code === 'auth/popup-closed-by-user') {
        setError('Google giriş penceresi tamamlanmadan kapatıldı.');
      } else {
        setError('Google ile giriş yapılamadı. Firebase sağlayıcı ve alan adı ayarlarını kontrol edin.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleGuest = () => {
    enableGuestMode();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="auth-modal-title" className="auth-modal bg-white text-slate-900 rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-6 relative space-y-5 animate-in fade-in zoom-in-95 duration-200">

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Giriş penceresini kapat"
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center space-y-1 pt-2">
          <div className="w-12 h-12 bg-slate-900 text-white rounded-xl mx-auto flex items-center justify-center font-bold text-xl shadow-sm">
            {mode === 'reset' ? <KeyRound className="h-5 w-5" /> : 'K'}
          </div>
          <h2 id="auth-modal-title" className="text-xl font-extrabold text-slate-900 tracking-tight">
            {mode === 'reset' ? 'Şifrenizi yenileyin' : 'KazKaz AI’a giriş yapın'}
          </h2>
          <p className="text-sm text-slate-500">
            {mode === 'reset' ? 'Hesabınızın e-posta adresine güvenli bağlantı gönderelim' : 'Şirketinizin finans çalışma alanına güvenli erişim'}
          </p>
        </div>

        {/* Tab switcher */}
        {mode !== 'reset' && <div className="flex bg-slate-100 p-1 rounded-xl text-sm font-semibold">
          <button
            type="button"
            onClick={() => { setMode('login'); setError(null); setNotice(null); }}
            className={`flex-1 py-2 rounded-lg transition-all ${mode === 'login' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'}`}
          >
            Oturum Aç
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setError(null); setNotice(null); }}
            className={`flex-1 py-2 rounded-lg transition-all ${mode === 'signup' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'}`}
          >
            Yeni Hesap Oluştur
          </button>
        </div>}

        {/* Error Notification */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <div role="status" className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs leading-5 text-emerald-800 flex items-start gap-2">
            <MailCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>{notice}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === 'signup' && (
            <div>
              <label htmlFor="auth-display-name" className="block text-sm font-semibold text-slate-700 mb-1.5">Ad Soyad / Unvan</label>
              <input
                id="auth-display-name"
                type="text"
                autoComplete="name"
                required
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Ahmet Yılmaz"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-3 text-sm text-slate-950 caret-slate-950 placeholder:text-slate-400 focus:ring-2 focus:ring-orange-400 focus:bg-white outline-none"
              />
            </div>
          )}

          <div>
            <label htmlFor="auth-email" className="block text-sm font-semibold text-slate-700 mb-1.5">E-posta adresi</label>
            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="cfo@firma.com"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-3 text-sm text-slate-950 caret-slate-950 placeholder:text-slate-400 focus:ring-2 focus:ring-orange-400 focus:bg-white outline-none"
            />
          </div>

          {mode !== 'reset' && <div>
            <div className="mb-1.5 flex items-center justify-between gap-3">
              <label htmlFor="auth-password" className="block text-sm font-semibold text-slate-700">Şifre</label>
              {mode === 'login' && <button type="button" onClick={() => { setMode('reset'); setError(null); setNotice(null); }} className="text-xs font-bold text-violet-700 hover:text-violet-900 hover:underline">Şifremi unuttum</button>}
            </div>
            <input
              id="auth-password"
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-3 text-sm text-slate-950 caret-slate-950 placeholder:text-slate-400 focus:ring-2 focus:ring-orange-400 focus:bg-white outline-none"
            />
          </div>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#0F2252] hover:bg-[#1B3A6B] text-white font-semibold text-sm py-3 rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm disabled:opacity-50 mt-2"
          >
            {mode === 'login' ? <LogIn className="w-4 h-4" /> : mode === 'signup' ? <UserPlus className="w-4 h-4" /> : <MailCheck className="w-4 h-4" />}
            <span>{mode === 'login' ? 'Giriş Yap' : mode === 'signup' ? 'Hesabı Kaydet & Başla' : 'Şifre yenileme bağlantısı gönder'}</span>
          </button>
          {mode === 'reset' && <button type="button" onClick={() => { setMode('login'); setError(null); setNotice(null); }} className="flex w-full items-center justify-center gap-2 py-1 text-xs font-bold text-slate-600 hover:text-slate-900"><ArrowLeft className="h-3.5 w-3.5" /> Giriş ekranına dön</button>}
        </form>

        {mode !== 'reset' && <><div className="relative my-4 text-center">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200"></div></div>
          <span className="relative bg-white px-3 text-[10px] text-slate-400 font-semibold uppercase tracking-wider">veya</span>
        </div>

        {/* OAuth 2.0 & Google Sign In */}
        <div className="space-y-2">
          <button
            type="button"
            onClick={handleGoogle}
            disabled={submitting}
            className="w-full bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-sm py-3 rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs disabled:opacity-50"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
            </svg>
            <span>Google / OAuth 2.0 ile Giriş Yap</span>
          </button>

          <button
            type="button"
            onClick={handleGuest}
            className="w-full bg-slate-100 hover:bg-slate-200/80 text-slate-700 font-semibold text-sm py-3 rounded-xl transition-all cursor-pointer"
          >
            Misafir (Demo) Modunda Devam Et
          </button>
        </div></>}

        {/* Security Note */}
        <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-400 text-center flex items-center justify-center gap-1">
          <Lock className="w-3 h-3 text-slate-400" />
          <span>Rol tabanlı erişim ve oturum doğrulaması</span>
        </div>

      </div>
    </div>
  );
};
