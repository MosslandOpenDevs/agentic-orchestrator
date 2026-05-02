'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiProject, type ApiPlan } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';
import { useModal } from '@/components/modals/useModal';

interface ProjectWithPlan extends ApiProject {
  plan?: ApiPlan | null;
}

export default function ProjectsPage() {
  const { t, locale } = useI18n();
  const { openModal } = useModal();
  const [projects, setProjects] = useState<ProjectWithPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    async function fetchProjects() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getProjects({ limit: 50 });
        if (response.data) {
          setProjects(response.data.projects);
        } else {
          setError(response.error || 'Failed to fetch projects');
        }
      } catch {
        setError('Failed to fetch projects');
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
  }, []);

  const filteredProjects = statusFilter === 'all'
    ? projects
    : projects.filter(p => p.status === statusFilter);

  const statusCounts = projects.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const getStatusColor = (status: string): 'green' | 'cyan' | 'orange' | 'purple' => {
    switch (status) {
      case 'ready': return 'green';
      case 'generating': return 'cyan';
      case 'error': return 'orange';
      default: return 'purple';
    }
  };

  return (
    <div className="min-h-screen pt-14 py-8 px-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-2xl font-bold text-[#39ff14] mb-2">
            {locale === 'ko' ? '프로젝트' : 'Projects'}
          </h1>
          <p className="text-[#6b7280] text-sm">
            {locale === 'ko'
              ? 'Plan에서 자동 생성된 프로젝트 스캐폴드'
              : 'Auto-generated project scaffolds from approved Plans'}
          </p>
        </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {['all', 'ready', 'generating', 'error'].map((status) => {
          const count = status === 'all' ? projects.length : (statusCounts[status] || 0);
          const isActive = statusFilter === status;
          return (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`
                card-cli p-4 text-left transition-all
                ${isActive ? 'border-[#39ff14] bg-[#39ff14]/5' : 'hover:border-[#6b7280]'}
              `}
            >
              <div className="text-2xl font-bold text-[#c0c0c0]">{count}</div>
              <div className="text-xs text-[#6b7280] uppercase">
                {status === 'all'
                  ? (locale === 'ko' ? '전체' : 'Total')
                  : status === 'ready'
                    ? (locale === 'ko' ? '완료' : 'Ready')
                    : status === 'generating'
                      ? (locale === 'ko' ? '생성 중' : 'Generating')
                      : (locale === 'ko' ? '오류' : 'Error')
                }
              </div>
            </button>
          );
        })}
      </div>

      {/* Project List */}
      <TerminalWindow title="projects.list">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-[#00ffff] animate-pulse">
              $ {locale === 'ko' ? '프로젝트 로딩 중...' : 'Loading projects...'}
              <span className="cursor-blink">▋</span>
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="text-[#ff5555]">[ERROR] {error}</div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-[#6b7280] text-4xl mb-4">📁</div>
            <div className="text-[#6b7280]">
              {locale === 'ko'
                ? '프로젝트가 없습니다'
                : 'No projects yet'}
            </div>
            <div className="text-[#6b7280] text-sm mt-2">
              {locale === 'ko'
                ? '승인된 Plan에서 프로젝트를 생성하세요'
                : 'Generate projects from approved Plans'}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-[#21262d]">
            {filteredProjects.map((project, index) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 hover:bg-[#161b22] cursor-pointer transition-colors"
                onClick={() => openModal('project', { id: project.id, title: project.name })}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <TerminalBadge variant={getStatusColor(project.status)}>
                        {project.status.toUpperCase()}
                      </TerminalBadge>
                      {project.tech_stack?.frontend && (
                        <TerminalBadge variant="cyan">
                          {project.tech_stack.frontend}
                        </TerminalBadge>
                      )}
                      {project.tech_stack?.backend && (
                        <TerminalBadge variant="purple">
                          {project.tech_stack.backend}
                        </TerminalBadge>
                      )}
                      {project.tech_stack?.blockchain && (
                        <TerminalBadge variant="orange">
                          {project.tech_stack.blockchain}
                        </TerminalBadge>
                      )}
                    </div>
                    <h3 className="text-[#c0c0c0] font-medium truncate">
                      {project.name}
                    </h3>
                    {project.directory_path && (
                      <div className="text-xs text-[#6b7280] mt-1 font-mono truncate">
                        <span className="text-[#00ffff]">→</span> {project.directory_path}
                      </div>
                    )}
                  </div>
                  <div className="text-right text-xs text-[#6b7280] whitespace-nowrap">
                    <div>
                      {project.files_generated > 0 && (
                        <span className="text-[#39ff14]">{project.files_generated} files</span>
                      )}
                    </div>
                    <div className="mt-1">
                      {formatLocalDateTime(project.created_at, locale)}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </TerminalWindow>

      {/* Info Section */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-3">
          {locale === 'ko' ? '프로젝트 생성 파이프라인' : 'Project Generation Pipeline'}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-[#c0c0c0]">Plan</span>
          <span className="text-[#6b7280]">→</span>
          <span className="text-[#00ffff]">{locale === 'ko' ? '마크다운 파싱' : 'Parse Markdown'}</span>
          <span className="text-[#6b7280]">→</span>
          <span className="text-[#bd93f9]">{locale === 'ko' ? '스택 감지' : 'Detect Stack'}</span>
          <span className="text-[#6b7280]">→</span>
          <span className="text-[#ff6b35]">{locale === 'ko' ? 'LLM 코드 생성' : 'LLM Code Gen'}</span>
          <span className="text-[#6b7280]">→</span>
          <span className="text-[#39ff14]">{locale === 'ko' ? '프로젝트' : 'Project'}</span>
        </div>
        <div className="mt-3 grid grid-cols-2 md:grid-cols-2 gap-2 text-xs">
          <div className="p-2 border border-[#21262d] rounded">
            <div className="text-[#6b7280]">{locale === 'ko' ? '채팅 / 생성' : 'Chat / Gen'}</div>
            <div className="text-[#bd93f9] font-mono">qwen3.5:9b</div>
          </div>
          <div className="p-2 border border-[#21262d] rounded">
            <div className="text-[#6b7280]">{locale === 'ko' ? '임베딩' : 'Embedding'}</div>
            <div className="text-[#00ffff] font-mono">qwen3-embedding:0.6b</div>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
}
