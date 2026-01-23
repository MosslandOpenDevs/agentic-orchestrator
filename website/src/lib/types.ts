export interface SystemStats {
  totalIdeas: number;
  totalPlans: number;
  plansRejected: number;
  inDevelopment: number;
  trendsAnalyzed: number;
  lastRun: string;
  nextRun: string;
}

export interface ActivityItem {
  time: string;
  type: string;
  message: string;
}

export interface Trend {
  title: string;
  score: number;
  category: string;
  articles: number;
  summary?: string;
  ideaSeeds?: string[];
  analyzedAt?: string;
}

export interface Idea {
  id: number;
  title: string;
  status: string;
  source: string;
  created: string;
  issueUrl?: string;
}

export interface Plan {
  id: number;
  title: string;
  ideaId: number;
  status: string;
  debateRounds: number;
  created: string;
  issueUrl?: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  count: number;
  status: 'active' | 'completed' | 'idle';
}

// Transparency Dashboard Types
export interface SignalDetail {
  id: string;
  source: string;
  category: string;
  title: string;
  summary: string | null;
  url: string | null;
  score: number;
  sentiment: string | null;
  topics: string[];
  entities: string[];
  collected_at: string | null;
}

export interface TrendDetail {
  id: string;
  period: string;
  name: string;
  description: string | null;
  score: number;
  signal_count: number;
  category: string | null;
  keywords: string[];
  analyzed_at: string | null;
  related_signals?: SignalDetail[];
  generated_ideas?: string[];
}

export interface IdeaJourney {
  idea: {
    id: string;
    title: string;
    summary: string;
    source_type: string;
    status: string;
    score: number;
    created_at: string | null;
  };
  source_trend?: TrendDetail;
  debates: DebateSession[];
  plans: PlanVersion[];
  timeline: TimelineEvent[];
}

export interface DebateSession {
  id: string;
  idea_id: string;
  phase: string;
  round_number: number;
  max_rounds: number;
  status: string;
  participants: string[];
  outcome: string | null;
  started_at: string | null;
  completed_at: string | null;
  message_count?: number;
}

export interface DebateMessage {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_handle: string | null;
  message_type: string;
  content: string;
  content_ko: string | null;
  created_at: string | null;
}

export interface DebateTranscript {
  debate: DebateSession;
  messages: DebateMessage[];
  participants: Array<{
    id: string;
    name: string;
    role: string;
  }>;
}

export interface PlanVersion {
  id: string;
  idea_id: string;
  title: string;
  version: number;
  status: string;
  created_at: string | null;
}

export interface TimelineEvent {
  timestamp: string;
  type: 'signal' | 'trend' | 'idea' | 'debate' | 'plan' | 'status_change';
  title: string;
  description?: string;
  metadata?: Record<string, unknown>;
}
