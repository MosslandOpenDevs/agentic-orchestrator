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
 * - Auto-deploy: pulls origin/main every 5 minutes (opt-in, see MOSS_AO_AUTO_DEPLOY)
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

// Auto-deploy is opt-in per machine: the moss-ao-deploy poller is only
// registered when MOSS_AO_AUTO_DEPLOY=1 is present in .env (loaded above).
// Without that gate every checkout of this repo -- a laptop, a second box, a
// staging clone -- would start fast-forwarding itself to origin/main as soon
// as someone ran `pm2 start ecosystem.config.js`. See docs/deployment.md.
const AUTO_DEPLOY = process.env.MOSS_AO_AUTO_DEPLOY === '1';

// Cron minutes are staggered so the PM2 workers do not all fire on the
// hour and flood the single-instance Ollama queue (which returned HTTP
// 503 'maximum pending requests exceeded' under the previous schedule).
//   signals  → :05 of every 30 min  (cheap, no LLM)
//   trends   → :15 of every 2 h     (LLM-bound)
//   debate   → :25 of every 6 h     (LLM-bound, longest)
//   backlog  → :45 of every 4 h     (mostly DB / retention)
//   health   → :02/:07/.../:57      (cheap, no LLM)
//   deploy   → :04/:09/.../:59      (cheap; no-op unless origin/main moved)
const SCHEDULES = {
  test: {
    signals: '5,35 * * * *',    // :05 and :35 every hour
    trends: '15 */1 * * *',     // :15 every hour
    debate: '25 * * * *',       // :25 every hour
    backlog: '45 * * * *',      // :45 every hour
    health: '2-57/5 * * * *',   // every 5 min, offset by 2 to avoid :00
    deploy: '4-59/5 * * * *',   // every 5 min, offset by 4 (staggered off health)
  },
  production: {
    signals: '5,35 * * * *',    // :05 and :35 every hour (= every 30 min)
    trends: '15 */2 * * *',     // :15 every 2 hours
    debate: '25 */6 * * *',     // :25 every 6 hours
    backlog: '45 */4 * * *',    // :45 every 4 hours
    health: '2-57/5 * * * *',   // every 5 min, offset by 2
    deploy: '4-59/5 * * * *',   // every 5 min, offset by 4
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

    // Auto-Deploy - fast-forwards this checkout to origin/main every 5 minutes.
    // Only registered when MOSS_AO_AUTO_DEPLOY=1 (see AUTO_DEPLOY above).
    // Exits immediately when the remote has not moved, so the steady-state cost
    // is one `git fetch`. All DEPLOY_* knobs are documented in scripts/deploy.sh
    // and are read from .env -- they are forwarded explicitly here because PM2
    // otherwise hands the app whatever environment the daemon was started with.
    ...(AUTO_DEPLOY ? [{
      name: 'moss-ao-deploy',
      script: 'scripts/deploy.sh',
      interpreter: 'bash',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '1G',  // headroom for `npm run build`
      cron_restart: schedule.deploy,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        DEPLOY_BRANCH: process.env.DEPLOY_BRANCH || 'main',
        DEPLOY_REQUIRE_CI: process.env.DEPLOY_REQUIRE_CI || '1',
        DEPLOY_ALERT_WEBHOOK: process.env.DEPLOY_ALERT_WEBHOOK || '',
        GITHUB_TOKEN: process.env.GITHUB_TOKEN || '',
      },
      error_file: './logs/deploy-error.log',
      out_file: './logs/deploy-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    }] : []),
  ],

  // NOTE: the `pm2 deploy` (SSH push) block that used to live here was removed
  // with the auto-deploy work. It had never been runnable -- it pointed at a host that does not
  // exist (server1.moss.land), the wrong repo (mossland/ instead of
  // MosslandOpenDevs/) and a requirements.txt this project does not have. It
  // also could not work by design: the app server has no public inbound route,
  // so nothing can SSH into it from outside the tailnet. Deployment is the
  // pull-based moss-ao-deploy poller above -- see docs/deployment.md.
};
