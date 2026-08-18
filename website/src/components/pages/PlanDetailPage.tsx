'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiPlan } from '@/lib/api';
import { localizedTitle } from '@/lib/markdown';
import { DetailPageLayout } from '../DetailPageLayout';
import { PlanDetail } from '../details/PlanDetail';

interface PlanDetailPageProps {
  id: string;
}

export function PlanDetailPage({ id }: PlanDetailPageProps) {
  const { locale } = useI18n();
  const [plan, setPlan] = useState<ApiPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPlan() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getPlanDetail(id);
        if (response.data) {
          setPlan(response.data);
        } else {
          setError(response.error || (locale === 'ko' ? '플랜을 찾을 수 없습니다' : 'Plan not found'));
        }
      } catch {
        setError(locale === 'ko' ? '데이터를 불러올 수 없습니다' : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }

    fetchPlan();
  }, [id, locale]);

  const title = plan
    ? localizedTitle(plan.title, plan.title_ko, locale)
    : (locale === 'ko' ? '플랜 상세' : 'Plan Detail');

  return (
    <DetailPageLayout
      title={title}
      backUrl="/ideas"
      backLabel={locale === 'ko' ? '플랜 목록' : 'Back to Plans'}
      loading={loading}
      error={error}
    >
      {plan && (
        <PlanDetail data={{ id: plan.id, title: plan.title }} />
      )}
    </DetailPageLayout>
  );
}
