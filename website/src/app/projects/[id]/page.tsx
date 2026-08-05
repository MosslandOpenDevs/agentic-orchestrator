import { Metadata } from 'next';
import { detailMetadata } from '@/lib/metadata';
import { ProjectDetailPage } from '@/components/pages/ProjectDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return detailMetadata('Project', `/projects/${id}`);
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <ProjectDetailPage id={id} />;
}
