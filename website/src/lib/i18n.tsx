'use client';

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

type Locale = 'en' | 'ko';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const translations: Record<Locale, Record<string, string>> = {
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.trends': 'Trends',
    'nav.backlog': 'Backlog',
    'nav.system': 'System',
    'nav.running': 'RUNNING',
    
    'dashboard.title': 'Agentic Orchestrator',
    'dashboard.subtitle': 'Autonomous AI orchestration system for the Mossland ecosystem',
    'dashboard.lastRun': 'Last run:',
    'dashboard.nextRun': 'Next run:',
    
    'stats.totalIdeas': 'Total Ideas',
    'stats.plansGenerated': 'Plans',
    'stats.plansRejected': 'Rejected',
    'stats.inDevelopment': 'In Development',
    'stats.trendsAnalyzed': 'Trends Analyzed',
    
    'pipeline.title': 'Pipeline Status',
    'pipeline.ideas': 'Ideas',
    'pipeline.plans': 'Plans',
    'pipeline.inDev': 'In Dev',
    'pipeline.active': 'Active',
    'pipeline.completed': 'Completed',
    'pipeline.idle': 'Idle',
    
    'activity.title': 'Activity Log',
    'activity.streaming': 'streaming',
    'activity.trend': 'TREND',
    'activity.idea': 'IDEA',
    'activity.plan': 'PLAN',
    'activity.debate': 'DEBATE',
    'activity.dev': 'DEV',
    'activity.system': 'SYSTEM',
    
    'feeds.title': 'RSS Feed Sources',
    'feeds.total': 'Total Feeds',
    
    'providers.title': 'AI Providers',
    'providers.rotation': 'Roles rotate each round',
    
    'trends.title': 'Trend Analysis',
    'trends.subtitle': 'Trend analysis results from 17 RSS feeds',
    'trends.articles': 'articles',
    'trends.score': 'score',
    'trends.ideaSeeds': 'Idea seeds:',
    'trends.schedule': 'Analysis Schedule',
    'trends.scheduleTime': 'Daily at 08:00 KST (23:00 UTC)',
    'trends.scheduleDesc': 'Automated via GitHub Actions',
    
    'backlog.title': 'Backlog',
    'backlog.subtitle': 'Idea and plan management based on GitHub Issues',
    'backlog.ideas': 'Ideas',
    'backlog.plans': 'Plans',
    'backlog.inDevelopment': 'In Development',
    'backlog.debateHistory': 'Debate History',
    'backlog.rounds': 'rounds',
    'backlog.viewOnGithub': 'View on GitHub',
    'backlog.viewAllIssues': 'View All Issues on GitHub',
    
    'system.title': 'System Architecture',
    'system.subtitle': 'Mossland Agentic Orchestrator system structure',
    'system.pipelineStages': 'Pipeline Stages',
    'system.techStack': 'Tech Stack',
    'system.workflow': 'Workflow',
    'system.debate.title': 'Multi-Agent Debate System',
    'system.debate.rotation': 'AI providers rotate each round for diverse perspectives',
    'system.planGenerated': 'Plan Generated',
    
    'system.stage.ideation': 'Idea generation',
    'system.stage.planningDraft': 'PRD/Architecture draft',
    'system.stage.planningReview': 'Multi-agent debate',
    'system.stage.dev': 'Development scaffolding',
    'system.stage.qa': 'Quality assurance',
    'system.stage.done': 'Complete',
    
    'system.workflow.1': 'RSS Feed Collection',
    'system.workflow.1.desc': 'Collect latest articles from 17 feeds',
    'system.workflow.2': 'Trend Analysis',
    'system.workflow.2.desc': 'Extract trends and analyze Web3 relevance with Claude',
    'system.workflow.3': 'Idea Generation',
    'system.workflow.3.desc': 'Generate micro-service ideas based on trends',
    'system.workflow.4': 'Human-in-the-Loop',
    'system.workflow.4.desc': 'Humans decide promotions via labels',
    'system.workflow.5': 'Multi-Agent Debate',
    'system.workflow.5.desc': '4 roles × 3 AI rotation refines plans',
    'system.workflow.6': 'Development Scaffolding',
    'system.workflow.6.desc': 'Auto-generate project structure',
    
    'role.founder': 'Founder',
    'role.founder.perspective': 'Vision, conviction, execution',
    'role.vc': 'VC',
    'role.vc.perspective': 'Market viability, investment value, scalability',
    'role.accelerator': 'Accelerator',
    'role.accelerator.perspective': 'Feasibility, MVP, validation',
    'role.founderFriend': 'Founder Friend',
    'role.founderFriend.perspective': 'Peer perspective, creative ideas',
    
    'common.viewSource': 'View Source Code',
  },
  ko: {
    'nav.dashboard': '대시보드',
    'nav.trends': '트렌드',
    'nav.backlog': '백로그',
    'nav.system': '시스템',
    'nav.running': '실행중',
    
    'dashboard.title': 'Agentic Orchestrator',
    'dashboard.subtitle': '모스랜드 생태계를 위한 자율 AI 오케스트레이션 시스템',
    'dashboard.lastRun': '마지막 실행:',
    'dashboard.nextRun': '다음 실행:',
    
    'stats.totalIdeas': '전체 아이디어',
    'stats.plansGenerated': '플랜',
    'stats.plansRejected': '거부됨',
    'stats.inDevelopment': '개발 중',
    'stats.trendsAnalyzed': '분석된 트렌드',
    
    'pipeline.title': '파이프라인 상태',
    'pipeline.ideas': 'Ideas',
    'pipeline.plans': 'Plans',
    'pipeline.inDev': 'In Dev',
    'pipeline.active': '활성',
    'pipeline.completed': '완료',
    'pipeline.idle': '대기',
    
    'activity.title': '활동 로그',
    'activity.streaming': '스트리밍',
    'activity.trend': 'TREND',
    'activity.idea': 'IDEA',
    'activity.plan': 'PLAN',
    'activity.debate': 'DEBATE',
    'activity.dev': 'DEV',
    'activity.system': 'SYSTEM',
    
    'feeds.title': 'RSS 피드 소스',
    'feeds.total': '전체 피드',
    
    'providers.title': 'AI 프로바이더',
    'providers.rotation': '라운드마다 역할 순환 배정',
    
    'trends.title': '트렌드 분석',
    'trends.subtitle': '17개 RSS 피드에서 수집한 트렌드 분석 결과',
    'trends.articles': '기사',
    'trends.score': '점수',
    'trends.ideaSeeds': '아이디어 씨앗:',
    'trends.schedule': '분석 스케줄',
    'trends.scheduleTime': '매일 08:00 KST (23:00 UTC)',
    'trends.scheduleDesc': 'GitHub Actions 자동 실행',
    
    'backlog.title': '백로그',
    'backlog.subtitle': 'GitHub Issues 기반 아이디어 및 플랜 관리',
    'backlog.ideas': '아이디어',
    'backlog.plans': '플랜',
    'backlog.inDevelopment': '개발 중',
    'backlog.debateHistory': '토론 이력',
    'backlog.rounds': '라운드',
    'backlog.viewOnGithub': 'GitHub에서 보기',
    'backlog.viewAllIssues': 'GitHub에서 전체 이슈 보기',
    
    'system.title': '시스템 아키텍처',
    'system.subtitle': 'Mossland Agentic Orchestrator 시스템 구조',
    'system.pipelineStages': '파이프라인 단계',
    'system.techStack': '기술 스택',
    'system.workflow': '워크플로우',
    'system.debate.title': '멀티 에이전트 토론 시스템',
    'system.debate.rotation': 'AI 프로바이더가 라운드마다 순환하여 다양한 관점 제공',
    'system.planGenerated': 'Plan 생성 완료',
    
    'system.stage.ideation': '아이디어 생성',
    'system.stage.planningDraft': 'PRD/아키텍처 초안',
    'system.stage.planningReview': '멀티 에이전트 토론',
    'system.stage.dev': '개발 스캐폴딩',
    'system.stage.qa': '품질 검증',
    'system.stage.done': '완료',
    
    'system.workflow.1': 'RSS 피드 수집',
    'system.workflow.1.desc': '17개 피드에서 최신 기사 수집',
    'system.workflow.2': '트렌드 분석',
    'system.workflow.2.desc': 'Claude로 트렌드 추출 및 Web3 연관성 분석',
    'system.workflow.3': '아이디어 생성',
    'system.workflow.3.desc': '트렌드 기반 마이크로 서비스 아이디어 생성',
    'system.workflow.4': 'Human-in-the-Loop',
    'system.workflow.4.desc': '사람이 라벨로 프로모션 결정',
    'system.workflow.5': '멀티 에이전트 토론',
    'system.workflow.5.desc': '4역할 × 3 AI 순환으로 플랜 정제',
    'system.workflow.6': '개발 스캐폴딩',
    'system.workflow.6.desc': '프로젝트 구조 자동 생성',
    
    'role.founder': 'Founder',
    'role.founder.perspective': '비전, 확신, 실행력',
    'role.vc': 'VC',
    'role.vc.perspective': '시장성, 투자 가치, 확장성',
    'role.accelerator': 'Accelerator',
    'role.accelerator.perspective': '실행 가능성, MVP, 검증',
    'role.founderFriend': 'Founder Friend',
    'role.founderFriend.perspective': '동료 관점, 창의적 아이디어',
    
    'common.viewSource': '소스 코드 보기',
  },
};

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>('en');

  const t = useCallback(
    (key: string): string => {
      return translations[locale][key] || key;
    },
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}

export function LanguageToggle() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-700 bg-zinc-800/50 p-0.5">
      <button
        onClick={() => setLocale('en')}
        className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
          locale === 'en'
            ? 'bg-zinc-600 text-white'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLocale('ko')}
        className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
          locale === 'ko'
            ? 'bg-zinc-600 text-white'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        KO
      </button>
    </div>
  );
}
