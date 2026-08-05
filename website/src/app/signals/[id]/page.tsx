import { Metadata } from 'next';
import { detailMetadata } from '@/lib/metadata';
import { SignalDetailPage } from '@/components/pages/SignalDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return detailMetadata('Signal', `/signals/${id}`);
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <SignalDetailPage id={id} />;
}
