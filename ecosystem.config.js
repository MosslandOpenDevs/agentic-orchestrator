/**
 * PM2 Ecosystem Configuration for Mossland Agentic Orchestrator
 *
 * This configuration manages all services:
 * - Signal collector: Fetches signals every 10 minutes (TEST) / 30 minutes (PROD)
 * - Trend analyzer: Analyzes trends every 30 minutes (TEST) / 2 hours (PROD)
 * - Debate runner: Runs debates every 1 hour (TEST) / 6 hours (PROD)
 * - Backlog processor: Processes every 30 minutes (TEST) / 4 hours (PROD)
 * - Web interface: Next.js dashboard (port 3000)
 * - API server: FastAPI backend (port 3001)
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only moss-ao-signals
 *   pm2 logs moss-ao-web
 *   pm2 monit
 *
 * TEST MODE SCHEDULE:
 *   Signals:  every 10 minutes
 *   Trends:   every 30 minutes
 *   Debate:   every 1 hour
 *   Backlog:  every 30 minutes
 *
 * PRODUCTION SCHEDULE:
 *   Signals:  every 30 minutes
 *   Trends:   every 2 hours
 *   Debate:   every 6 hours
 *   Backlog:  every 4 hours
 */

// Load .env into process.env so PM2 child processes (and the env: blocks
// below) can pick up secrets without requiring the operator to export them
// in the shell before running `pm2 start`. Lightweight inline parser so we
// don't add a `dotenv` dependency to a Python project's repo root.
(() => {
  const fs = require('fs');
  const path = require('path');
  const envPath = path.join(__dirname, '.env');
  if (!fs.existsSync(envPath)) return;
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    let val = line.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
})();

// Toggle between TEST and PRODUCTION schedules
const TEST_MODE = false;  // Set to false for production schedules

// Cron minutes are staggered so the PM2 workers do not all fire on the
// hour and flood the single-instance Ollama queue (which returned HTTP
// 503 'maximum pending requests exceeded' under the previous schedule).
//   signals  → :05 of every 30 min  (cheap, no LLM)
//   trends   → :15 of every 2 h     (LLM-bound)
//   debate   → :25 of every 6 h     (LLM-bound, longest)
//   backlog  → :45 of every 4 h     (mostly DB / retention)
//   health   → :02/:07/.../:57      (cheap, no LLM)
const SCHEDULES = {
  test: {
    signals: '5,35 * * * *',    // :05 and :35 every hour
    trends: '15 */1 * * *',     // :15 every hour
    debate: '25 * * * *',       // :25 every hour
    backlog: '45 * * * *',      // :45 every hour
    health: '2-57/5 * * * *',   // every 5 min, offset by 2 to avoid :00
  },
  production: {
    signals: '5,35 * * * *',    // :05 and :35 every hour (= every 30 min)
    trends: '15 */2 * * *',     // :15 every 2 hours
    debate: '25 */6 * * *',     // :25 every 6 hours
    backlog: '45 */4 * * *',    // :45 every 4 hours
    health: '2-57/5 * * * *',   // every 5 min, offset by 2
  },
};

const schedule = TEST_MODE ? SCHEDULES.test : SCHEDULES.production;

module.exports = {
  apps: [
    // Signal Collector
    // Note: Uses cron_restart for scheduled execution (runs once, waits for next cron trigger)
    {
      name: 'moss-ao-signals',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler signal-collect',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '500M',
      cron_restart: schedule.signals,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/signals-error.log',
      out_file: './logs/signals-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Trend Analyzer
    // Analyzes signals to identify trends using local LLM (Ollama)
    {
      name: 'moss-ao-trends',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler analyze-trends',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '1G',
      cron_restart: schedule.trends,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: process.env.OLLAMA_HOST || 'http://localhost:11434',
      },
      error_file: './logs/trends-error.log',
      out_file: './logs/trends-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Debate Runner
    {
      name: 'moss-ao-debate',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler run-debate',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '2G',
      cron_restart: schedule.debate,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: process.env.OLLAMA_HOST || 'http://localhost:11434',
      },
      error_file: './logs/debate-error.log',
      out_file: './logs/debate-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Backlog Processor
    // Processes idea queue, generates status reports
    {
      name: 'moss-ao-backlog',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler process-backlog',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '1G',
      cron_restart: schedule.backlog,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/backlog-error.log',
      out_file: './logs/backlog-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Web Interface - Next.js Dashboard
    {
      name: 'moss-ao-web',
      script: 'npm',
      args: 'start',
      cwd: './website',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
      error_file: './logs/web-error.log',
      out_file: './logs/web-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // API Server - FastAPI (long-running service)
    {
      name: 'moss-ao-api',
      script: '.venv/bin/python',
      args: '-m uvicorn agentic_orchestrator.api.main:app --host 0.0.0.0 --port 3001',
      cwd: __dirname,
      instances: 1,
      autorestart: true,  // Keep running
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Health Monitor - Checks system health every 5 minutes
    {
      name: 'moss-ao-health',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler health-check',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '200M',
      cron_restart: schedule.health,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/health-error.log',
      out_file: './logs/health-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: 'deploy',
      host: ['server1.moss.land'],
      ref: 'origin/main',
      repo: 'git@github.com:mossland/agentic-orchestrator.git',
      path: '/var/www/moss-ao',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      env: {
        NODE_ENV: 'production',
      },
    },
    staging: {
      user: 'deploy',
      host: ['staging.moss.land'],
      ref: 'origin/develop',
      repo: 'git@github.com:mossland/agentic-orchestrator.git',
      path: '/var/www/moss-ao-staging',
      'post-deploy': 'npm install && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env development',
      env: {
        NODE_ENV: 'development',
      },
    },
  },
};
