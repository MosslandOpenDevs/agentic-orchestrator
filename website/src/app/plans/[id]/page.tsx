import { Metadata } from 'next';
import { detailMetadata } from '@/lib/metadata';
import { PlanDetailPage } from '@/components/pages/PlanDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return detailMetadata('Plan', `/plans/${id}`);
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <PlanDetailPage id={id} />;
}
