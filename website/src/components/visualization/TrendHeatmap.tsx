'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiTrend } from '@/lib/api';

interface TrendHeatmapProps {
  trends: ApiTrend[];
  onCellClick?: (category: string, day: string) => void;
}

interface HeatmapCell {
  category: string;
  day: string;
  value: number;
  trends: ApiTrend[];
}

const CATEGORIES = ['AI', 'Crypto', 'Web3', 'DeFi', 'NFT', 'Gaming', 'Metaverse', 'Other'];
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function TrendHeatmap({ trends, onCellClick }: TrendHeatmapProps) {
  const { t } = useI18n();
  const [hoveredCell, setHoveredCell] = useState<HeatmapCell | null>(null);

  // Generate heatmap data
  const heatmapData = useMemo(() => {
    const data: HeatmapCell[][] = [];

    // Group trends by category and day
    const grouped: Record<string, Record<string, ApiTrend[]>> = {};

    CATEGORIES.forEach(cat => {
      grouped[cat] = {};
      DAYS.forEach(day => {
        grouped[cat][day] = [];
      });
    });

    trends.forEach(trend => {
      const category = CATEGORIES.find(
        cat => trend.category?.toLowerCase().includes(cat.toLowerCase())
      ) || 'Other';

      const dayIndex = trend.analyzed_at
        ? new Date(trend.analyzed_at).getDay()
        : Math.floor(Math.random() * 7);
      const day = DAYS[dayIndex === 0 ? 6 : dayIndex - 1]; // Convert Sunday=0 to index 6

      if (grouped[category] && grouped[category][day]) {
        grouped[category][day].push(trend);
      }
    });

    // Convert to array format
    CATEGORIES.forEach(category => {
      const row: HeatmapCell[] = [];
      DAYS.forEach(day => {
        const cellTrends = grouped[category][day] || [];
        const avgScore = cellTrends.length > 0
          ? cellTrends.reduce((sum, t) => sum + t.score, 0) / cellTrends.length
          : 0;
        row.push({
          category,
          day,
          value: avgScore,
          trends: cellTrends,
        });
      });
      data.push(row);
    });

    return data;
  }, [trends]);

  // Calculate max value for normalization
  const maxValue = useMemo(() => {
    return Math.max(
      ...heatmapData.flatMap(row => row.map(cell => cell.value)),
      1
    );
  }, [heatmapData]);

  const getHeatColor = (value: number) => {
    const intensity = value / maxValue;
    if (intensity === 0) return 'bg-[#0d1117]';
    if (intensity < 0.2) return 'bg-[#0e4429]';
    if (intensity < 0.4) return 'bg-[#006d32]';
    if (intensity < 0.6) return 'bg-[#26a641]';
    if (intensity < 0.8) return 'bg-[#39d353]';
    return 'bg-[#39ff14]';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('trendHeatmap.title')}
        </span>
        <span className="text-xs text-[#6b7280]">
          {trends.length} {t('trendHeatmap.trends')}
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[400px]">
          {/* Day Headers */}
          <div className="flex mb-2">
            <div className="w-20" /> {/* Spacer for category labels */}
            {DAYS.map(day => (
              <div key={day} className="flex-1 text-center text-xs text-[#6b7280]">
                {day}
              </div>
            ))}
          </div>

          {/* Heatmap Rows */}
          {heatmapData.map((row, rowIdx) => (
            <motion.div
              key={row[0].category}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: rowIdx * 0.05 }}
              className="flex mb-1"
            >
              {/* Category Label */}
              <div className="w-20 text-xs text-[#6b7280] flex items-center pr-2 truncate">
                {row[0].category}
              </div>

              {/* Cells */}
              {row.map((cell, cellIdx) => (
                <motion.div
                  key={`${cell.category}-${cell.day}`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: rowIdx * 0.05 + cellIdx * 0.02 }}
                  className={`
                    flex-1 h-6 m-0.5 rounded cursor-pointer transition-all
                    ${getHeatColor(cell.value)}
                    ${cell.trends.length > 0 ? 'hover:ring-2 hover:ring-[#00ffff]' : ''}
                  `}
                  onMouseEnter={() => setHoveredCell(cell)}
                  onMouseLeave={() => setHoveredCell(null)}
                  onClick={() => cell.trends.length > 0 && onCellClick?.(cell.category, cell.day)}
                >
                  {cell.trends.length > 0 && (
                    <div className="w-full h-full flex items-center justify-center text-[10px] font-bold text-black/70">
                      {cell.trends.length}
                    </div>
                  )}
                </motion.div>
              ))}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between pt-3 border-t border-[#21262d]">
        <span className="text-[10px] text-[#6b7280]">{t('trendHeatmap.less')}</span>
        <div className="flex gap-1">
          {['bg-[#0d1117]', 'bg-[#0e4429]', 'bg-[#006d32]', 'bg-[#26a641]', 'bg-[#39d353]', 'bg-[#39ff14]'].map((color, i) => (
            <div key={i} className={`w-3 h-3 rounded-sm ${color}`} />
          ))}
        </div>
        <span className="text-[10px] text-[#6b7280]">{t('trendHeatmap.more')}</span>
      </div>

      {/* Hover Tooltip */}
      {hoveredCell && hoveredCell.trends.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-cli p-3 mt-2"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#00ffff]">
              {hoveredCell.category} - {hoveredCell.day}
            </span>
            <span className="text-xs text-[#6b7280]">
              {hoveredCell.trends.length} {t('trendHeatmap.trends')}
            </span>
          </div>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {hoveredCell.trends.slice(0, 3).map(trend => (
              <div key={trend.id} className="text-xs text-[#c0c0c0] flex items-center justify-between">
                <span className="truncate flex-1">{trend.name}</span>
                <span className="text-[#39ff14] ml-2">{trend.score.toFixed(1)}</span>
              </div>
            ))}
            {hoveredCell.trends.length > 3 && (
              <div className="text-[10px] text-[#6b7280]">
                +{hoveredCell.trends.length - 3} {t('trendHeatmap.more')}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}

// Mini version for dashboard widgets
export function TrendHeatmapMini({ trends }: { trends: ApiTrend[] }) {
  const weekData = useMemo(() => {
    const days = Array(7).fill(0);
    trends.forEach(trend => {
      if (trend.analyzed_at) {
        const dayIndex = new Date(trend.analyzed_at).getDay();
        days[dayIndex === 0 ? 6 : dayIndex - 1]++;
      }
    });
    return days;
  }, [trends]);

  const maxCount = Math.max(...weekData, 1);

  const getColor = (count: number) => {
    const intensity = count / maxCount;
    if (intensity === 0) return 'bg-[#21262d]';
    if (intensity < 0.5) return 'bg-[#006d32]';
    return 'bg-[#39ff14]';
  };

  return (
    <div className="flex gap-0.5">
      {DAYS.map((day, i) => (
        <div
          key={day}
          className={`w-4 h-4 rounded-sm ${getColor(weekData[i])}`}
          title={`${day}: ${weekData[i]} trends`}
        />
      ))}
    </div>
  );
}
