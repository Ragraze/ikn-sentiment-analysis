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
    const desktop = window.matchMedia('(min-width: 80rem)');
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
            <span className="brand-caption">Analisis opini publik</span>
          </Link>
          {mobile && <button type="button" className="sidebar-close" onClick={closeMenu} aria-label="Tutup menu navigasi">×</button>}
        </div>
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
          <span className="menu-glyph" aria-hidden="true"><span /><span /><span /></span>Menu
        </button>
      </div>
      <dialog ref={dialog} id="mobile-sidebar" className="mobile-sidebar" aria-label="Menu navigasi" onClose={() => setMenuOpen(false)} onCancel={() => setMenuOpen(false)} onClick={event => { if (event.target === event.currentTarget) closeMenu(); }}>
        {sidebar(true)}
      </dialog>
      <div className="workspace">
        <main id="main" tabIndex={-1}>
          <header className="workspace-heading">
            <div>
              <h1>{page?.title || 'Halaman tidak ditemukan'}</h1>
              {page && <p className="workspace-description">{page.description}</p>}
            </div>
            {pathname === '/' && <Link href="/analysis" className="button primary">Analisis kalimat</Link>}
          </header>
          <div className="page-content">{children}</div>
        </main>
      </div>
      <a className="github-link" href="https://github.com/Ragraze/ikn-sentiment-analysis" target="_blank" rel="noopener noreferrer" aria-label="Buka repositori GitHub (tab baru)" title="Lihat kode di GitHub">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .75a11.25 11.25 0 0 0-3.56 21.92c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.72 2.63 1.22 3.27.93.1-.73.39-1.22.71-1.5-2.5-.29-5.13-1.25-5.13-5.56 0-1.23.44-2.23 1.16-3.02-.12-.29-.5-1.43.11-2.98 0 0 .95-.3 3.1 1.15a10.8 10.8 0 0 1 5.63 0c2.15-1.46 3.1-1.15 3.1-1.15.61 1.55.23 2.69.11 2.98.72.79 1.16 1.79 1.16 3.02 0 4.32-2.64 5.27-5.15 5.55.4.35.76 1.04.76 2.1v3.09c0 .3.2.65.78.54A11.25 11.25 0 0 0 12 .75Z" /></svg>
      </a>
    </ModelHealthProvider>
  );
}
