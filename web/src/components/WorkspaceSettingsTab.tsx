import React, { useEffect, useState } from 'react';
import { Building2, DatabaseBackup, FileDown, LockKeyhole, MailPlus, RefreshCw, Trash2, UploadCloud, UserMinus, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { SirketRolu, SirketUyeListesi, sirketUyesiCikar, sirketUyesiDavetEt, sirketUyesiRolGuncelle, sirketUyeleriniGetir } from '../lib/api';

interface WorkspaceSettingsTabProps {
  companyName: string;
  onNavigateDataEntry: () => void;
  onExportWorkspace: () => Promise<void> | void;
  onDeleteWorkspace: () => Promise<void> | void;
}

export const WorkspaceSettingsTab: React.FC<WorkspaceSettingsTabProps> = ({
  companyName,
  onNavigateDataEntry,
  onExportWorkspace,
  onDeleteWorkspace,
}) => {
  const { currentUser, userProfile, isGuest } = useAuth();
  const [activeAction, setActiveAction] = useState<'export' | 'delete' | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [members, setMembers] = useState<SirketUyeListesi | null>(null);
  const [memberLoading, setMemberLoading] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<Exclude<SirketRolu, 'admin'>>('viewer');
  const hasCompanyWorkspace = Boolean(currentUser && userProfile?.companyId && !isGuest);
  const canDelete = hasCompanyWorkspace && ['admin', 'cfo'].includes(userProfile?.role || '');
  const canManageMembers = hasCompanyWorkspace && userProfile?.role === 'admin';

  const loadMembers = async () => {
    if (!canManageMembers) return;
    setMemberLoading(true);
    try { setMembers(await sirketUyeleriniGetir()); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Kullanıcı listesi alınamadı.'); }
    finally { setMemberLoading(false); }
  };

  useEffect(() => { void loadMembers(); }, [canManageMembers]);

  const inviteMember = async (event: React.FormEvent) => {
    event.preventDefault();
    setMemberLoading(true); setMessage(null);
    try {
      const result = await sirketUyesiDavetEt(inviteEmail, inviteRole);
      setMessage(`${result.eposta} için ${result.rol} rolünde 7 günlük davet oluşturuldu.`);
      setInviteEmail('');
      await loadMembers();
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Davet oluşturulamadı.'); }
    finally { setMemberLoading(false); }
  };

  const changeRole = async (userId: string, role: SirketRolu) => {
    setMemberLoading(true); setMessage(null);
    try { await sirketUyesiRolGuncelle(userId, role); setMessage('Kullanıcı rolü güncellendi; kullanıcının oturum jetonunu yenilemesi gerekir.'); await loadMembers(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Rol güncellenemedi.'); }
    finally { setMemberLoading(false); }
  };

  const removeMember = async (userId: string, email: string | null) => {
    if (!window.confirm(`${email || 'Bu kullanıcı'} şirket çalışma alanından çıkarılsın mı?`)) return;
    setMemberLoading(true); setMessage(null);
    try { await sirketUyesiCikar(userId); setMessage('Kullanıcının şirket erişimi kaldırıldı.'); await loadMembers(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Kullanıcı çıkarılamadı.'); }
    finally { setMemberLoading(false); }
  };

  const exportData = async () => {
    setActiveAction('export');
    setMessage(null);
    try {
      await onExportWorkspace();
      setMessage('Şirket çalışma alanı JSON olarak dışa aktarıldı.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Veri dışa aktarılamadı.');
    } finally {
      setActiveAction(null);
    }
  };

  const deleteData = async () => {
    if (!window.confirm('Buluttaki aktif finans çalışma alanı kalıcı olarak silinsin mi? Bu işlem geri alınamaz.')) return;
    setActiveAction('delete');
    setMessage(null);
    try {
      await onDeleteWorkspace();
      setMessage('Buluttaki çalışma alanı silindi.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Çalışma alanı silinemedi.');
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="panel-card p-5 sm:p-6">
        <p className="panel-kicker">Yönetim</p>
        <h1 className="mt-2 text-xl font-extrabold text-[#0a1628]">Şirket ve çalışma alanı ayarları</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Şirket kimliği, kullanıcı rolü, veri sahipliği ve güvenlik işlemleri finansal veri girişinden ayrı yönetilir.</p>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="panel-card p-5">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-violet-50 text-violet-700"><Building2 className="h-5 w-5" /></span>
            <div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Aktif şirket</p><h2 className="text-base font-extrabold text-slate-900">{userProfile?.companyName || companyName}</h2></div>
          </div>
          <div className="mt-5 grid gap-3 text-xs sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-slate-400">Kullanıcı</p><p className="mt-1 truncate font-bold text-slate-800">{userProfile?.email || 'Misafir oturumu'}</p></div>
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-slate-400">Rol</p><p className="mt-1 font-bold capitalize text-slate-800">{userProfile?.role || 'misafir'}</p></div>
          </div>
          <button type="button" onClick={onNavigateDataEntry} className="panel-secondary-button mt-5"><UploadCloud className="h-4 w-4" /> Finansal veri girişine git</button>
        </section>

        <section className="panel-card p-5">
          <div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100 text-slate-700"><Users className="h-5 w-5" /></span><div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Erişim</p><h2 className="text-base font-extrabold text-slate-900">Rol tabanlı yetkilendirme</h2></div></div>
          <p className="mt-4 text-xs leading-5 text-slate-600">Admin kullanıcı ve rolleri yönetir. CFO veri yaşam döngüsünü yönetebilir. Analist veri hazırlayabilir; izleyici finansal sonuçları salt okunur inceler.</p>
          <div className="mt-4 flex items-start gap-2 rounded-xl bg-emerald-50 p-3 text-[11px] leading-5 text-emerald-800"><LockKeyhole className="mt-0.5 h-4 w-4 shrink-0" /> Şirket üyeliği ve rol değişiklikleri yalnız doğrulanmış backend üzerinden uygulanır; istemci kendi rolünü değiştiremez.</div>
        </section>
      </div>

      <section className="panel-card p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><Users className="mt-0.5 h-5 w-5 text-violet-700" /><div><h2 className="text-base font-extrabold text-slate-900">Kullanıcı ve rol yönetimi</h2><p className="mt-1 text-xs leading-5 text-slate-600">Davet edilen kişi aynı doğrulanmış e-posta ile giriş yapıp şirket kurulum ekranından daveti kabul eder.</p></div></div>{canManageMembers && <button type="button" onClick={() => void loadMembers()} disabled={memberLoading} aria-label="Kullanıcı listesini yenile" className="panel-secondary-button self-start disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${memberLoading ? 'animate-spin' : ''}`} /> Yenile</button>}</div>
        {!canManageMembers ? <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">Kullanıcı daveti ve rol değişikliği yalnız şirket Admin rolüne açıktır.</p> : <>
          <form onSubmit={(event) => void inviteMember(event)} className="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-[1fr_160px_auto]">
            <label className="text-xs font-bold text-slate-700">Davet e-postası<input type="email" required value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="kullanici@sirket.com" className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" /></label>
            <label className="text-xs font-bold text-slate-700">Başlangıç rolü<select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as Exclude<SirketRolu, 'admin'>)} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="viewer">İzleyici</option><option value="analyst">Analist</option><option value="cfo">CFO</option></select></label>
            <button type="submit" disabled={memberLoading || !inviteEmail.trim()} className="panel-primary-button self-end disabled:opacity-50"><MailPlus className="h-4 w-4" /> Davet oluştur</button>
          </form>
          <div className="mt-5 space-y-2">
            {members?.uyeler.map((member) => <article key={member.kullanici_id} className="flex flex-col gap-3 rounded-xl border border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><p className="truncate text-sm font-bold text-slate-900">{member.eposta || member.kullanici_id}</p><p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-400">Aktif üye</p></div><div className="flex items-center gap-2"><select aria-label={`${member.eposta || 'Kullanıcı'} rolü`} value={member.rol} disabled={member.kullanici_id === currentUser?.uid || memberLoading} onChange={(event) => void changeRole(member.kullanici_id, event.target.value as SirketRolu)} className="min-h-9 rounded-lg border border-slate-300 bg-white px-2 text-xs font-bold"><option value="admin">Admin</option><option value="cfo">CFO</option><option value="analyst">Analist</option><option value="viewer">İzleyici</option></select><button type="button" aria-label={`${member.eposta || 'Kullanıcı'} üyeliğini kaldır`} disabled={member.kullanici_id === currentUser?.uid || memberLoading} onClick={() => void removeMember(member.kullanici_id, member.eposta)} className="grid h-9 w-9 place-items-center rounded-lg border border-red-200 text-red-700 hover:bg-red-50 disabled:opacity-30"><UserMinus className="h-4 w-4" /></button></div></article>)}
            {!memberLoading && members && !members.uyeler.length && <p className="rounded-xl border border-dashed border-slate-300 p-4 text-center text-xs text-slate-500">Aktif kullanıcı bulunamadı.</p>}
          </div>
          {members?.davetler.length ? <div className="mt-5"><p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-slate-400">Bekleyen davetler</p><div className="mt-2 grid gap-2 sm:grid-cols-2">{members.davetler.map((invite) => <div key={invite.davet_id} className="rounded-xl border border-sky-100 bg-sky-50 p-3"><p className="truncate text-xs font-bold text-sky-950">{invite.eposta}</p><p className="mt-1 text-[10px] text-sky-700">{invite.rol} · 7 gün içinde kabul</p></div>)}</div></div> : null}
        </>}
      </section>

      <section className="panel-card p-5 sm:p-6">
        <div className="flex items-start gap-3"><DatabaseBackup className="mt-0.5 h-5 w-5 text-violet-700" /><div><h2 className="text-base font-extrabold text-slate-900">Veri sahipliği ve yaşam döngüsü</h2><p className="mt-1 text-xs leading-5 text-slate-600">Şirket verinizi dışa aktarabilir veya yetkiniz varsa buluttaki aktif çalışma alanını silebilirsiniz.</p></div></div>
        {!hasCompanyWorkspace && <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">Bu işlemler için doğrulanmış kullanıcı ve kalıcı şirket çalışma alanı gerekir.</p>}
        {message && <p role="status" className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">{message}</p>}
        <div className="mt-5 flex flex-wrap gap-3">
          <button type="button" disabled={!hasCompanyWorkspace || activeAction !== null} onClick={() => void exportData()} className="panel-secondary-button disabled:cursor-not-allowed disabled:opacity-50"><FileDown className="h-4 w-4" /> {activeAction === 'export' ? 'Hazırlanıyor…' : 'Verilerimi dışa aktar'}</button>
          <button type="button" disabled={!canDelete || activeAction !== null} onClick={() => void deleteData()} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-red-200 bg-white px-4 text-xs font-extrabold text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"><Trash2 className="h-4 w-4" /> {activeAction === 'delete' ? 'Siliniyor…' : 'Bulut verisini sil'}</button>
        </div>
        <p className="mt-4 text-[10px] leading-4 text-slate-500">Silme yalnızca Admin ve CFO rollerine açıktır. Yedeklerdeki veriler tanımlanmış saklama ve imha politikasına göre ayrıca temizlenmelidir.</p>
      </section>
    </div>
  );
};
