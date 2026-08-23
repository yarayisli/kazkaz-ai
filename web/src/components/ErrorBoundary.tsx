import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface State { hasError: boolean; }

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State { return { hasError: true }; }

  componentDidCatch(error: Error) {
    console.error('KazKaz arayüz hatası:', error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <main className="grid min-h-screen place-items-center bg-[#050816] p-6 text-white">
        <section className="w-full max-w-lg rounded-3xl border border-red-400/20 bg-white/[0.06] p-8 text-center shadow-2xl">
          <AlertTriangle className="mx-auto h-10 w-10 text-red-300" />
          <h1 className="mt-4 text-xl font-black">Bu ekran yüklenirken beklenmeyen bir sorun oluştu</h1>
          <p className="mt-3 text-sm leading-6 text-slate-300">Verileriniz silinmedi. Sayfayı yenileyin; sorun sürerse geri bildirimde bulunduğunuz ekranı belirtin.</p>
          <button type="button" onClick={() => window.location.reload()} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-slate-950"><RefreshCw className="h-4 w-4" /> Güvenli biçimde yeniden yükle</button>
        </section>
      </main>
    );
  }
}
