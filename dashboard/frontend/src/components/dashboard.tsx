'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ModelHealthProvider } from '@/hooks/use-model-health';

const navigation = [
  { href: '/', label: 'Dashboard', title: 'Dashboard penelitian', icon: 'overview', description: 'Gambaran sentimen dan topik percakapan tentang Ibu Kota Nusantara.' },
  { href: '/analysis', label: 'Analisis kalimat', title: 'Analisis kalimat', icon: 'analysis', description: 'Baca sentimen dan temukan topik dari sebuah opini tentang IKN.' },
  { href: '/dataset', label: 'Dataset opini', title: 'Dataset opini', icon: 'dataset', description: 'Telusuri teks penelitian, label sentimen, dan pembagian datanya.' },
  { href: '/topics', label: 'Pemodelan topik', title: 'Pemodelan topik', icon: 'topics', description: 'Jelajahi kata kunci dan kelompok percakapan yang ditemukan Top2Vec.' },
  { href: '/evaluation', label: 'Evaluasi model', title: 'Evaluasi model', icon: 'evaluation', description: 'Periksa hasil klasifikasi IndoBERT melalui metrik dan confusion matrix.' },
] as const;

function NavigationIcon({ name }: { name: typeof navigation[number]['icon'] }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {name === 'overview' && <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>}
      {name === 'analysis' && <><path d="M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-6 3V6a2 2 0 0 1 2-2Z" /><path d="M7 9h10M7 13h6" /></>}
      {name === 'dataset' && <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 9h18M3 14h18M9 4v16" /></>}
      {name === 'topics' && <><circle cx="12" cy="5" r="3" /><circle cx="5" cy="18" r="3" /><circle cx="19" cy="18" r="3" /><path d="m10.5 7.5-4 8m7-8 4 8M8 18h8" /></>}
      {name === 'evaluation' && <><path d="M4 3v18h17M8 16v-4m5 4V8m5 8V5" /></>}
    </svg>
  );
}

export default function Dashboard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const page = navigation.find(item => item.href === pathname);
  const [menuOpen, setMenuOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);

  function closeMenu() {
    dialog.current?.close();
    setMenuOpen(false);
  }

  useEffect(() => {
    if (!menuOpen) return;
    const panel = dialog.current;
    panel?.showModal();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const desktop = window.matchMedia('(min-width: 64rem)');
    function onResize() {
      if (desktop.matches) {
        panel?.close();
        setMenuOpen(false);
      }
    }
    desktop.addEventListener('change', onResize);
    return () => {
      panel?.close();
      document.body.style.overflow = previousOverflow;
      desktop.removeEventListener('change', onResize);
    };
  }, [menuOpen]);

  useEffect(() => {
    dialog.current?.close();
    setMenuOpen(false);
  }, [pathname]);

  function sidebar(mobile: boolean) {
    return (
      <div className="sidebar-content">
        <div className="sidebar-brand-row">
          <Link href="/" className="brand" onClick={mobile ? closeMenu : undefined}>
            <span className="brand-name">IKN <strong>Sentiment Lab</strong></span>
            <span className="brand-caption">Analisis opini Nusantara</span>
          </Link>
          {mobile && <button type="button" className="sidebar-close" onClick={closeMenu} aria-label="Tutup menu navigasi">×</button>}
        </div>
        <p className="sidebar-label">Ruang penelitian</p>
        <nav className="sidebar-navigation" aria-label={mobile ? 'Navigasi utama seluler' : 'Navigasi utama'}>
          {navigation.map(item => (
            <Link key={item.href} href={item.href} aria-current={pathname === item.href ? 'page' : undefined} onClick={mobile ? closeMenu : undefined}>
              <NavigationIcon name={item.icon} /><span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span>Metode penelitian</span>
          <strong>IndoBERT <span>+ </span>Top2Vec</strong>
          <p>Klasifikasi sentimen dan pemodelan topik berbahasa Indonesia.</p>
        </div>
      </div>
    );
  }

  return (
    <ModelHealthProvider>
      <a className="skip-link" href="#main">Langsung ke konten</a>
      <aside className="desktop-sidebar" aria-label="Sidebar penelitian">{sidebar(false)}</aside>
      <div className="mobile-toolbar">
        <Link href="/" className="mobile-brand">IKN Sentiment Lab</Link>
        <button className="menu-button" type="button" aria-expanded={menuOpen} aria-controls="mobile-sidebar" aria-haspopup="dialog" onClick={() => setMenuOpen(true)}>
          <span className="menu-glyph" aria-hidden="true"><span /><span /></span>Menu
        </button>
      </div>
      <dialog ref={dialog} id="mobile-sidebar" className="mobile-sidebar" aria-label="Menu navigasi" onClose={() => setMenuOpen(false)} onCancel={() => setMenuOpen(false)} onClick={event => { if (event.target === event.currentTarget) closeMenu(); }}>
        {sidebar(true)}
      </dialog>
      <div className="workspace">
        <main id="main" tabIndex={-1}>
          <header className="workspace-heading">
            <div>
              <p className="workspace-context">Penelitian Ibu Kota Nusantara</p>
              <h1>{page?.title || 'Halaman tidak ditemukan'}</h1>
              {page && <p className="workspace-description">{page.description}</p>}
            </div>
            {pathname === '/' && <Link href="/analysis" className="button primary">Analisis kalimat</Link>}
          </header>
          <div className="page-content">{children}</div>
          <footer className="workspace-footer"><span>IKN Sentiment Lab</span><span>Data penelitian · Bahasa Indonesia</span></footer>
        </main>
      </div>
    </ModelHealthProvider>
  );
}
