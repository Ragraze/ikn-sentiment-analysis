import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Dashboard from '@/components/dashboard';
import { AnalysisSessionProvider } from '@/hooks/use-analysis-session';
import './globals.css';
import './feature-polish.css';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'IKN Sentiment Lab · IndoBERT & Top2Vec',
  description: 'Dashboard penelitian IKN dengan Next.js, klasifikasi IndoBERT, dan topic modelling Top2Vec.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="id"><body><AnalysisSessionProvider><Dashboard>{children}</Dashboard></AnalysisSessionProvider></body></html>;
}
