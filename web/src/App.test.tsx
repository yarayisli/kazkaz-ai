import React from 'react';
import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
const m=vi.hoisted(()=>({auth:{currentUser:{uid:'ua'},userProfile:{companyId:'a',role:'admin',onboardingProfile:{}},isGuest:false},load:vi.fn(),save:vi.fn(),remove:vi.fn()}));
vi.mock('./context/AuthContext',()=>({useAuth:()=>m.auth,AuthProvider:({children}:any)=>children}));
vi.mock('./context/AlertContext',()=>({AlertProvider:({children}:any)=>children}));
vi.mock('./lib/workspacePersistence',()=>({loadWorkspace:m.load,saveWorkspace:m.save,deleteWorkspace:m.remove,exportWorkspace:vi.fn()}));
vi.mock('./lib/api',()=>({zamanSerisiAnalizi:vi.fn(),CalismaAlaniCakismaHatasi:class extends Error {constructor(public mevcutRevizyon:number,message:string){super(message);}}}));
vi.mock('./components/Navigation',()=>({Navigation:({setActiveTab}:any)=><nav>{[['Veri','data-entry'],['Özet','overview'],['Ayarlar','settings']].map(([label,id])=><button key={id} onClick={()=>setActiveTab(id)}>{label}</button>)}</nav>}));
vi.mock('./components/LandingPage',()=>({LandingPage:()=>null}));
vi.mock('./components/ScreenTabs',()=>({ScreenTabs:()=>null}));
vi.mock('./components/CompanySetup',()=>({CompanySetup:()=>null}));
vi.mock('./components/FeedbackWidget',()=>({FeedbackWidget:()=>null}));
vi.mock('./components/AlertSystemOverlay',()=>({AlertSystemOverlay:()=>null}));
vi.mock('./components/OverviewTab',()=>({OverviewTab:({data}:any)=><div>{data.companyName}</div>}));
vi.mock('./components/DataEntryTab',()=>({DataEntryTab:({onSave}:any)=><button onClick={()=>void onSave({companyName:'Taslak'},null)}>Kaydet</button>}));
vi.mock('./components/WorkspaceSettingsTab',()=>({WorkspaceSettingsTab:({onDeleteWorkspace}:any)=><button onClick={()=>void onDeleteWorkspace().catch(()=>undefined)}>Sil</button>}));
import {WorkspaceOturumu} from './App';
import {CalismaAlaniCakismaHatasi} from './lib/api';
const snapshot=(name:string)=>({financialData:{companyName:name},cashFlow:[],debts:[],customers:[],budget:[],financialAudit:null,isSampleData:false});
const deferred=()=>{let resolve!:(v:any)=>void;const promise=new Promise<any>(r=>{resolve=r;});return {promise,resolve};};
afterEach(cleanup);
beforeEach(()=>{vi.clearAllMocks();m.auth={currentUser:{uid:'ua'},userProfile:{companyId:'a',role:'admin',onboardingProfile:{}},isGuest:false};m.load.mockResolvedValue({snapshot:snapshot('A gizli'),revizyon:1});m.save.mockResolvedValue({revizyon:2});});
async function openData(){fireEvent.click(screen.getByText('Veri'));await screen.findByText('Kaydet');await screen.findByText('Şirket çalışma alanı güvenli kayıttan yüklendi.');}
it('409 sonrası tekrar kayıt yapmaz; içerik yenilendikten sonra yeni revizyonu kullanır',async()=>{
 render(<WorkspaceOturumu/>);await openData();m.save.mockRejectedValueOnce(new CalismaAlaniCakismaHatasi(2,'çakışma'));
 fireEvent.click(screen.getByText('Kaydet'));await screen.findByText('En son sürümü yükle');
 fireEvent.click(screen.getByText('Veri'));fireEvent.click(await screen.findByText('Kaydet'));expect(m.save).toHaveBeenCalledTimes(1);
 m.load.mockResolvedValueOnce({snapshot:snapshot('Yeni kayıt'),revizyon:2});fireEvent.click(screen.getByText('En son sürümü yükle'));
 await screen.findByText('En son sürüm yüklendi. Değişikliklerinizi kontrol edip yeniden kaydedebilirsiniz.');
 fireEvent.click(screen.getByText('Veri'));fireEvent.click(await screen.findByText('Kaydet'));await waitFor(()=>expect(m.save).toHaveBeenCalledTimes(2));expect(m.save.mock.calls[1][3]).toBe(2);
});
it('A manuel yenilemesinin geç yanıtı B şirketine uygulanmaz',async()=>{
 const view=render(<WorkspaceOturumu/>);await openData();m.save.mockRejectedValueOnce(new CalismaAlaniCakismaHatasi(2,'çakışma'));
 fireEvent.click(screen.getByText('Kaydet'));await screen.findByText('En son sürümü yükle');const late=deferred();m.load.mockReturnValueOnce(late.promise);fireEvent.click(screen.getByText('En son sürümü yükle'));
 m.auth={...m.auth,currentUser:{uid:'ub'},userProfile:{...m.auth.userProfile,companyId:'b'}};m.load.mockResolvedValueOnce({snapshot:snapshot('B kaydı'),revizyon:7});view.rerender(<WorkspaceOturumu/>);
 fireEvent.click(screen.getByText('Özet'));await screen.findByText('B kaydı');await act(async()=>late.resolve({snapshot:snapshot('A geç gizli'),revizyon:2}));expect(screen.queryByText('A geç gizli')).toBeNull();expect(screen.getByText('B kaydı')).toBeTruthy();
});
it('yükleme bitmeden kayıt göndermez',async()=>{
 const late=deferred();m.load.mockReturnValueOnce(late.promise);render(<WorkspaceOturumu/>);fireEvent.click(screen.getByText('Veri'));fireEvent.click(await screen.findByText('Kaydet'));expect(m.save).not.toHaveBeenCalled();await act(async()=>late.resolve({snapshot:null,revizyon:0}));
});
it('iki eşzamanlı kayıt göndermez',async()=>{
 render(<WorkspaceOturumu/>);await openData();const late=deferred();m.save.mockReturnValueOnce(late.promise);fireEvent.click(screen.getByText('Kaydet'));fireEvent.click(screen.getByText('Kaydet'));expect(m.save).toHaveBeenCalledTimes(1);await act(async()=>late.resolve({revizyon:2}));
});
it('silme sonrası yeni kayıtta silmenin revizyonunu kullanır',async()=>{
 render(<WorkspaceOturumu/>);await openData();m.remove.mockResolvedValueOnce({revizyon:2});fireEvent.click(screen.getByText('Ayarlar'));fireEvent.click(await screen.findByText('Sil'));await screen.findByText('Buluttaki aktif çalışma alanı silindi; ekran örnek başlangıç durumuna döndü.');expect(m.remove.mock.calls[0][1]).toBe(1);fireEvent.click(screen.getByText('Veri'));fireEvent.click(await screen.findByText('Kaydet'));await waitFor(()=>expect(m.save).toHaveBeenCalledTimes(1));expect(m.save.mock.calls[0][3]).toBe(2);
});
it('eski sürümle silme çakışırsa kullanıcıyı yenilemeye yönlendirir',async()=>{
 render(<WorkspaceOturumu/>);await openData();m.remove.mockRejectedValueOnce(new CalismaAlaniCakismaHatasi(2,'çakışma'));fireEvent.click(screen.getByText('Ayarlar'));fireEvent.click(await screen.findByText('Sil'));await screen.findByText('Çalışma alanı başka bir oturumda değiştiği için silinmedi. Önce en son sürümü yükleyin.');expect(screen.getByText('En son sürümü yükle')).toBeTruthy();
});
