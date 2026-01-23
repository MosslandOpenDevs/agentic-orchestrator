'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ApiClient } from '@/lib/api';
import type { ModalData } from '../modals/ModalProvider';

interface StatsDetailProps {
  data: ModalData;
}

interface UsageData {
  today: {
    total_cost: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_requests: number;
  };
  today_by_provider: Record<string, {
    cost: number;
    input_tokens: number;
    output_tokens: number;
    requests: number;
  }>;
  month_total: number;
  history: Array<{
    date: string;
    cost: number;
    requests: number;
  }>;
}

export function StatsDetail({ data }: StatsDetailProps) {
  const [loading, setLoading] = useState(true);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [statusData, setStatusData] = useState<any>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [usageRes, statusRes] = await Promise.all([
          ApiClient.getUsage(30),
          ApiClient.getStatus(),
        ]);

        if (usageRes.data) {
          setUsage(usageRes.data);
        }
        if (statusRes.data) {
          setStatusData(statusRes.data);
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="text-[#ff6b35] animate-pulse">
          Loading statistics...
          <span className="cursor-blink">_</span>
        </div>
      </div>
    );
  }

  const statType = data.statType as string;

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="text-center border-b border-[#21262d] pb-4">
        <div className="text-2xl font-bold text-[#39ff14]">
          {data.value as number}
        </div>
        <div className="text-xs text-[#6b7280] uppercase tracking-wider">
          {data.label as string}
        </div>
      </div>

      {/* Stats breakdown based on type */}
      {statType === 'ideas' && statusData && (
        <div className="space-y-4">
          <div className="text-xs text-[#6b7280]">
            <span className="text-[#bd93f9]"># </span>
            Ideas breakdown by status
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="Pending" value={statusData.stats?.ideas_generated || 0} color="cyan" />
            <StatBox label="In Progress" value={0} color="orange" />
            <StatBox label="Completed" value={0} color="green" />
            <StatBox label="Rejected" value={0} color="purple" />
          </div>
        </div>
      )}

      {statType === 'plans' && statusData && (
        <div className="space-y-4">
          <div className="text-xs text-[#6b7280]">
            <span className="text-[#bd93f9]"># </span>
            Plans breakdown by status
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="Draft" value={statusData.stats?.plans_created || 0} color="cyan" />
            <StatBox label="Review" value={0} color="orange" />
            <StatBox label="Approved" value={0} color="green" />
            <StatBox label="Rejected" value={data.rejected as number || 0} color="purple" />
          </div>
        </div>
      )}

      {statType === 'development' && (
        <div className="space-y-4">
          <div className="text-xs text-[#6b7280]">
            <span className="text-[#bd93f9]"># </span>
            Development status
          </div>
          <div className="text-center py-4">
            <div className="text-[#6b7280] text-sm">No active development projects</div>
            <div className="text-[10px] text-[#3b3b3b] mt-2">
              Projects will appear here when plans are approved
            </div>
          </div>
        </div>
      )}

      {statType === 'trends' && statusData && (
        <div className="space-y-4">
          <div className="text-xs text-[#6b7280]">
            <span className="text-[#bd93f9]"># </span>
            Trend analysis overview
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="Total Trends" value={data.value as number} color="purple" />
            <StatBox label="Signals Today" value={statusData.stats?.signals_today || 0} color="cyan" />
            <StatBox label="Debates Today" value={statusData.stats?.debates_today || 0} color="orange" />
            <StatBox label="Agents Active" value={statusData.stats?.agents_active || 34} color="green" />
          </div>
        </div>
      )}

      {/* API Usage Stats */}
      {usage && (
        <div className="border-t border-[#21262d] pt-4">
          <div className="text-xs text-[#6b7280] mb-3">
            <span className="text-[#bd93f9]"># </span>
            API usage today
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-2 bg-[#0d1117] rounded border border-[#21262d]">
              <div className="text-lg font-bold text-[#f1fa8c]">
                ${usage.today.total_cost.toFixed(4)}
              </div>
              <div className="text-[10px] text-[#6b7280]">Cost Today</div>
            </div>
            <div className="p-2 bg-[#0d1117] rounded border border-[#21262d]">
              <div className="text-lg font-bold text-[#00ffff]">
                {usage.today.total_requests}
              </div>
              <div className="text-[10px] text-[#6b7280]">Requests Today</div>
            </div>
          </div>

          {/* Provider breakdown */}
          {Object.keys(usage.today_by_provider).length > 0 && (
            <div className="mt-4">
              <div className="text-[10px] text-[#6b7280] mb-2">By provider:</div>
              {Object.entries(usage.today_by_provider).map(([provider, stats]) => (
                <div key={provider} className="flex justify-between text-xs py-1">
                  <span className="text-[#c0c0c0]">{provider}</span>
                  <span className="text-[#f1fa8c]">${stats.cost.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses = {
    cyan: 'text-[#00ffff] border-[#00ffff]/30',
    green: 'text-[#39ff14] border-[#39ff14]/30',
    orange: 'text-[#ff6b35] border-[#ff6b35]/30',
    purple: 'text-[#bd93f9] border-[#bd93f9]/30',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-3 rounded border ${colorClasses[color as keyof typeof colorClasses] || colorClasses.cyan} bg-[#0d1117]`}
    >
      <div className={`text-xl font-bold ${colorClasses[color as keyof typeof colorClasses]?.split(' ')[0]}`}>
        {value}
      </div>
      <div className="text-[10px] text-[#6b7280]">{label}</div>
    </motion.div>
  );
}
