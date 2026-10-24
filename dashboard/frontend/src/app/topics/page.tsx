import { TopicModelling } from '@/features/topic-modelling';

export default async function TopicsPage({ searchParams }: { searchParams: Promise<{ source?: string | string[] }> }) {
  const params = await searchParams;
  const source = params.source === 'notebook' ? 'notebook' : 'trained';
  return <TopicModelling key={source} initialSource={source} />;
}
