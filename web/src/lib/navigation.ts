/**
 * Çalışma alanı navigasyonunun tek kaynağı.
 *
 * Kullanıcı beş ekran görür; her ekran kendi içinde sekmelere ayrılır.
 * Sekme kimlikleri (`id`) App.tsx'teki yönlendirmeyle birebir aynıdır —
 * yeni gruplama hiçbir sekmeyi kaldırmaz, yalnızca kapı sayısını azaltır.
 */

import {
  BarChart2,
  Bot,
  FileText,
  Gauge,
  Landmark,
  LayoutDashboard,
  Leaf,
  PieChart,
  Scale,
  Settings2,
  Sliders,
  TrendingUp,
  UploadCloud,
  Users,
  Wallet,
} from 'lucide-react';
import type React from 'react';

export type EkranSekmesi = {
  /** App.tsx'in tanıdığı sekme kimliği. */
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  /** İzleyici rolüne kapalı sekmeler. */
  restrictedForViewer?: boolean;
};

export type Ekran = {
  id: string;
  label: string;
  /** Kullanıcının bu ekrana gelirken sorduğu soru. */
  soru: string;
  icon: React.ComponentType<{ className?: string }>;
  tabs: EkranSekmesi[];
};

export const EKRANLAR: Ekran[] = [
  {
    id: 'durum',
    label: 'Durum',
    soru: 'Şirketim nasıl?',
    icon: Gauge,
    tabs: [
      { id: 'overview', label: 'Genel', description: 'Sağlık skoru, kritik uyarılar ve bu ayın aksiyonları', icon: LayoutDashboard },
      { id: 'benchmarking', label: 'Sektör Karşılaştırma', description: 'Sektör referanslarına göre konum', icon: BarChart2 },
    ],
  },
  {
    id: 'para',
    label: 'Para',
    soru: 'Param yetiyor mu?',
    icon: Wallet,
    tabs: [
      { id: 'cashflow', label: 'Nakit & Borç', description: '13 haftalık nakit, borç servisi ve ödeme takvimi', icon: Wallet },
      { id: 'cash-statement', label: 'Nakit Akış Tablosu', description: 'Faaliyet, yatırım ve finansman köprüsü', icon: Landmark },
      { id: 'scenario', label: 'Senaryo & Tahmin', description: 'Stres testi, projeksiyon ve yatırım ön değerlendirmesi', icon: Sliders },
    ],
  },
  {
    id: 'kar',
    label: 'Kâr',
    soru: 'Kâr ediyor muyum?',
    icon: TrendingUp,
    tabs: [
      { id: 'income-statement', label: 'Gelir Tablosu', description: 'Ciro, maliyet ve kârlılık köprüsü', icon: TrendingUp },
      { id: 'balance-sheet', label: 'Bilanço', description: 'Varlık, yükümlülük ve özkaynak', icon: Scale },
      { id: 'customer', label: 'Müşteri & Ürün', description: 'Alacak, yoğunlaşma ve ürün kârlılığı', icon: Users },
      { id: 'budget', label: 'Bütçe & Gerçek', description: 'Plan, gerçekleşen ve sapma', icon: PieChart },
    ],
  },
  {
    id: 'cfo',
    label: "CFO'ya Sor",
    soru: 'Ne yapmalıyım?',
    icon: Bot,
    tabs: [
      { id: 'cfo-agent', label: "CFO'ya Sor", description: 'Uzman ajan bulguları, uyarılar ve aksiyon planı', icon: Bot },
    ],
  },
  {
    id: 'veri',
    label: 'Veri & Rapor',
    soru: 'Veriyi ver, raporu al',
    icon: FileText,
    tabs: [
      { id: 'data-entry', label: 'Veri Girişi', description: 'Excel, Google Sheets veya manuel girişle veriyi doğrula', icon: UploadCloud, restrictedForViewer: true },
      { id: 'reports', label: 'Rapor Merkezi', description: 'Geçmiş analizler, karşılaştırmalar ve dışa aktarma', icon: FileText },
      { id: 'compliance', label: 'ESG & TFRS', description: 'Kanıt, belge ve uzman onayı hazırlık kontrolü', icon: Leaf },
      { id: 'settings', label: 'Şirket Ayarları', description: 'Şirket kimliği, kullanıcı rolleri ve veri sahipliği', icon: Settings2, restrictedForViewer: true },
    ],
  },
];

/** Ekranlara bağlı olmayan, yalnızca yetkili kullanıcıya görünen sekme. */
export const PLATFORM_ADMIN_TAB_ID = 'platform-admin';

/** Aranabilir düz sekme listesi. */
export const TUM_SEKMELER: EkranSekmesi[] = EKRANLAR.flatMap((ekran) => ekran.tabs);

/** Bir sekmenin hangi ekrana ait olduğunu bulur. */
export function sekmeninEkrani(tabId: string): Ekran | undefined {
  return EKRANLAR.find((ekran) => ekran.tabs.some((tab) => tab.id === tabId));
}

/** Bir sekmeyi kimliğinden bulur. */
export function sekmeyiBul(tabId: string): EkranSekmesi | undefined {
  return TUM_SEKMELER.find((tab) => tab.id === tabId);
}

/** Bir ekrana tıklandığında açılacak varsayılan sekme. */
export function ekraninIlkSekmesi(ekranId: string): string {
  const ekran = EKRANLAR.find((item) => item.id === ekranId);
  return ekran?.tabs[0]?.id || EKRANLAR[0].tabs[0].id;
}
