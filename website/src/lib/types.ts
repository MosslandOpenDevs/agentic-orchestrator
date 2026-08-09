
export type SystemHealth = 'operational' | 'degraded' | 'unknown';

export interface SystemStats {
  /** What /status actually reported, not an assumption. */
  systemStatus: SystemHealth;
  totalIdeas: number;
  totalPlans: number;
  plansRejected: number;
  inDevelopment: number;
  trendsAnalyzed: number;
  /** When the pipeline last actually produced something. Absent when the
   *  API exposes nothing to derive it from -- it must never be the
   *  viewer's own clock dressed up as a pipeline run. */
  lastRun?: string;
  /** Absent: the API does not report the scheduler's next tick. */
  nextRun?: string;
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
  /** Display number (position in the list), not an API identifier. */
  id: number;
  /** The backend's UUID. Detail lookups must use this, never `id`. */
  apiId: string;
  title: string;
  status: string;
  source: string;
  created: string;
  issueUrl?: string;
}

export interface Plan {
  /** Display number (position in the list), not an API identifier. */
  id: number;
  /** The backend's UUID. Detail lookups must use this, never `id`. */
  apiId: string;
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
    title_ko: string | null;
    summary: string;
    summary_ko: string | null;
    description: string | null;
    description_ko: string | null;
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
  title_ko: string | null;
  version: number;
  status: string;
  final_plan: string | null;
  final_plan_ko: string | null;
  created_at: string | null;
}

export interface TimelineEvent {
  timestamp: string;
  type: 'signal' | 'trend' | 'idea' | 'debate' | 'plan' | 'status_change';
  title: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

// Adapter types
export interface AdapterInfo {
  name: string;
  category: string;
  description: string;
  description_en: string;
  enabled: boolean;
  last_fetch: string | null;
  health: Record<string, unknown>;
  sources?: string[];
  source_count?: number;
  error?: string;
}

// Project types
export interface Project {
  id: string;
  plan_id: string;
  name: string;
  directory_path: string | null;
  tech_stack: {
    frontend?: string;
    backend?: string;
    database?: string;
    blockchain?: string;
    additional?: string[];
  };
  status: 'pending' | 'generating' | 'ready' | 'ready_with_warnings' | 'error';
  files_generated: number;
  generation_log?: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface GenerateProjectResponse {
  job_id: string;
  status: 'accepted' | 'exists' | 'in_progress';
  message: string;
}

export interface ProjectJobStatus {
  job_id: string;
  plan_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: {
    success: boolean;
    project_id?: string;
    project_path?: string;
    files_generated?: number;
    error?: string;
  };
}

// ---------------------------------------------------------------------------
// ERC-1155 On-Chain Tournament Passes — Mossland Competitors
// ---------------------------------------------------------------------------

/** Tier of a tournament pass, ordered by prestige. */
export type TournamentPassTier = 'bronze' | 'silver' | 'gold' | 'platinum' | 'legendary';

/** On-chain status of a single ERC-1155 token id within a season. */
export type TournamentPassStatus = 'active' | 'expired' | 'revoked' | 'transferable';

/**
 * Represents a single ERC-1155 tournament pass token.
 * Each `tokenId` maps to a unique (season, tier, slot) combination on-chain.
 */
export interface TournamentPass {
  /** ERC-1155 token id (uint256 as string to avoid JS precision loss). */
  tokenId: string;
  /** Human-readable display name, e.g. "Season 3 Gold Pass". */
  name: string;
  /** IPFS or HTTPS URI pointing to the token metadata JSON. */
  metadataUri: string;
  tier: TournamentPassTier;
  status: TournamentPassStatus;
  /** Mossland season identifier this pass belongs to. */
  seasonId: string;
  /** EVM address of the current holder. Lowercase checksummed hex. */
  holderAddress: string;
  /** Maximum number of passes at this tier for the season (supply cap). */
  maxSupply: number;
  /** How many of this token id have been minted so far. */
  mintedSupply: number;
  /** ISO-8601 timestamp when this pass was minted. */
  mintedAt: string | null;
  /** ISO-8601 timestamp when this pass expires (season end). */
  expiresAt: string | null;
}

/**
 * Liquidity-locked season configuration.
 *
 * During a season the contract holds a liquidity reserve that is only
 * unlocked after `endsAt`. This prevents wash-trading of passes and
 * guarantees prize-pool solvency throughout the competition window.
 */
export interface TournamentSeason {
  /** Unique season identifier (slug or UUID). */
  id: string;
  /** Display name, e.g. "Mossland Open — Season 3". */
  name: string;
  /** EVM address of the ERC-1155 contract managing this season's passes. */
  contractAddress: string;
  /** ISO-8601 start timestamp. */
  startsAt: string;
  /** ISO-8601 end timestamp — also when liquidity lock is released. */
  endsAt: string;
  /** Whether the liquidity reserve is currently locked. */
  liquidityLocked: boolean;
  /**
   * Total MOC (or other token) amount locked as prize / liquidity reserve.
   * Stored as a string to avoid uint256 precision loss.
   */
  lockedAmount: string;
  /** ERC-20 token address of the locked asset (e.g. MOC token). */
  lockedTokenAddress: string;
  /** Aggregate pass counts per tier for this season. */
  passCounts: Record<TournamentPassTier, number>;
  /** ISO-8601 timestamp when this season record was last synced from chain. */
  syncedAt: string | null;
}

/**
 * Summary of a competitor's tournament pass holdings for a given season.
 * Returned by the `/tournament/seasons/{seasonId}/competitors/{address}`
 * endpoint.
 */
export interface CompetitorPassSummary {
  /** EVM address of the competitor. */
  address: string;
  /** Display name (from Mossland profile, if available). */
  displayName: string | null;
  seasonId: string;
  passes: TournamentPass[];
  /** Aggregate score accumulated in this season (off-chain leaderboard). */
  seasonScore: number;
  /** Current rank within the season (1-indexed). null if unranked. */
  rank: number | null;
}

/**
 * API response shape for listing tournament passes.
 * Follows the same pagination convention used by ideas/plans endpoints.
 */
export interface TournamentPassListResponse {
  items: TournamentPass[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * API response shape for listing tournament seasons.
 */
export interface TournamentSeasonListResponse {
  items: TournamentSeason[];
  total: number;
  page: number;
  pageSize: number;
}
