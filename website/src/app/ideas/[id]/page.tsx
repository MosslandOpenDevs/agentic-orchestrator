import { Metadata } from 'next';
import { detailMetadata } from '@/lib/metadata';
import { IdeaDetailPage } from '@/components/pages/IdeaDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return detailMetadata('Idea', `/ideas/${id}`);
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <IdeaDetailPage id={id} />;
}
