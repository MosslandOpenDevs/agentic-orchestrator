"""
Scheduled task implementations.

These tasks are executed by PM2 on a schedule.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def _signal_collect_async():
    """Async implementation of signal collection."""
    from ..signals import SignalAggregator, SignalStorage

    logger.info("=" * 60)
    logger.info("Starting signal collection cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        # Initialize aggregator (uses default adapters internally)
        aggregator = SignalAggregator()
        storage = SignalStorage()

        # Fetch and score signals from all adapters
        # Note: collect_all() handles fetching, scoring, and saving to DB
        logger.info("Fetching signals from all adapters...")
        signals = await aggregator.collect_all(save_to_db=True, deduplicate=True)
        logger.info(f"Collected {len(signals)} signals")

        # Cleanup old signals
        logger.info("Cleaning up old signals...")
        deleted_count = storage.cleanup_old_signals(days=30)
        logger.info(f"Deleted {deleted_count} old signals")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Signal collection completed in {duration:.1f}s")
        logger.info(f"Summary: {len(signals)} collected, {deleted_count} old signals deleted")

    except Exception as e:
        logger.error(f"Signal collection failed: {e}", exc_info=True)
        raise


def signal_collect():
    """Collect signals from all adapters."""
    asyncio.run(_signal_collect_async())


async def _run_debate_async(topic: Optional[str] = None):
    """Async implementation of debate execution."""
    from ..llm import HybridLLMRouter
    from ..debate import MultiStageDebate, run_multi_stage_debate
    from ..signals import SignalStorage
    from ..db import get_database, SignalRepository, DebateRepository

    logger.info("=" * 60)
    logger.info("Starting multi-stage debate cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()
    debate_session = None
    db = None

    try:
        # Initialize components
        db = get_database()
        session = db.get_session()
        signal_repo = SignalRepository(session)
        debate_repo = DebateRepository(session)

        # Get topic from high-relevance signals if not provided
        if not topic:
            logger.info("Selecting topic from recent high-relevance signals...")
            signals = signal_repo.get_recent(limit=10, min_score=0.7)
            if signals:
                # Create topic from top signals
                topics = [s.title for s in signals[:3]]
                topic = f"Mossland 생태계 전략 토론: {', '.join(topics)}"
            else:
                topic = "Mossland 생태계의 다음 분기 전략 방향"

        logger.info(f"Debate topic: {topic}")

        # Get context from recent signals
        context_signals = signal_repo.get_recent(limit=20)
        context = "\n".join([
            f"- [{s.source}] {s.title}: {s.summary[:200] if s.summary else 'No summary'}"
            for s in context_signals
        ])

        # Create debate session in database BEFORE starting
        import uuid
        session_id = str(uuid.uuid4())[:8]
        debate_session = debate_repo.create_session({
            'id': session_id,
            'topic': topic,
            'context': context,
            'phase': 'divergence',
            'round_number': 1,
            'max_rounds': 3,
            'status': 'active',
            'participants': [],
            'started_at': start_time,
        })
        session.commit()
        logger.info(f"Created debate session: {session_id}")

        # Initialize LLM router
        router = HybridLLMRouter()

        # Collect participants during debate
        all_participants = set()

        # Callback for progress logging and saving messages
        def on_message(msg):
            logger.info(f"[{msg.phase.value}] {msg.agent_name}: {msg.message_type.value}")
            all_participants.add(msg.agent_name)
            # Save message to database
            try:
                debate_repo.add_message({
                    'session_id': session_id,
                    'agent_id': msg.agent_id,
                    'agent_name': msg.agent_name,
                    'agent_handle': getattr(msg, 'agent_handle', None),
                    'message_type': msg.message_type.value,
                    'content': msg.content if hasattr(msg, 'content') else '',
                    'token_count': getattr(msg, 'token_count', 0),
                    'model_used': getattr(msg, 'model', None),
                })
            except Exception as e:
                logger.warning(f"Failed to save message: {e}")

        def on_phase_complete(result):
            logger.info(f"Phase {result.phase.value} completed: {result.duration_seconds:.1f}s, ${result.total_cost:.4f}")
            # Update session phase
            try:
                debate_repo.update_session(
                    session_id,
                    phase=result.phase.value,
                    round_number=result.round_number if hasattr(result, 'round_number') else 1,
                    participants=list(all_participants),
                )
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to update session phase: {e}")

        # Run debate
        logger.info("Starting multi-stage debate...")
        result = await run_multi_stage_debate(
            router=router,
            topic=topic,
            context=context,
            on_message=on_message,
            on_phase_complete=on_phase_complete,
        )

        # Save final results to database
        try:
            ideas_data = [idea.to_dict() for idea in result.all_ideas] if result.all_ideas else []
            debate_repo.update_session(
                session_id,
                status='completed',
                phase='planning',
                outcome='completed',
                final_plan=result.final_plan,
                ideas_generated=ideas_data,
                summary=f"Generated {len(result.all_ideas)} ideas, selected {len(result.selected_ideas)}",
                total_tokens=result.total_tokens,
                total_cost=result.total_cost,
                completed_at=datetime.utcnow(),
                participants=list(all_participants),
            )
            session.commit()
            logger.info(f"Saved debate results to database: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save debate results: {e}", exc_info=True)

        # Log results
        logger.info("Debate results summary:")
        logger.info(f"  Session ID: {result.session_id}")
        logger.info(f"  Topic: {result.topic}")
        logger.info(f"  Final plan length: {len(result.final_plan) if result.final_plan else 0} chars")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Debate completed in {duration:.1f}s")
        logger.info(f"Total cost: ${result.total_cost:.4f}")
        logger.info(f"Ideas generated: {len(result.all_ideas)}")
        logger.info(f"Ideas selected: {len(result.selected_ideas)}")

        # Log final plan summary
        if result.final_plan:
            logger.info("Final plan generated successfully")
            logger.info(f"Plan length: {len(result.final_plan)} characters")

    except Exception as e:
        logger.error(f"Debate execution failed: {e}", exc_info=True)
        # Mark session as failed if it was created
        if debate_session and db:
            try:
                session = db.get_session()
                debate_repo = DebateRepository(session)
                debate_repo.update_session(
                    debate_session.id,
                    status='cancelled',
                    outcome='error',
                    summary=f"Error: {str(e)}",
                    completed_at=datetime.utcnow(),
                )
                session.commit()
            except Exception:
                pass
        raise


def run_debate(topic: Optional[str] = None):
    """Run multi-stage debate."""
    asyncio.run(_run_debate_async(topic))


def _process_backlog():
    """Implementation of backlog processing."""
    from ..db import get_database, IdeaRepository, PlanRepository

    logger.info("=" * 60)
    logger.info("Starting backlog processing cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        db = get_database()
        idea_repo = IdeaRepository(db.get_session())
        plan_repo = PlanRepository(db.get_session())

        # Get pending ideas
        pending_ideas = idea_repo.get_by_status('pending')
        logger.info(f"Found {len(pending_ideas)} pending ideas")

        # Get approved plans awaiting implementation
        approved_plans = plan_repo.get_by_status('approved')
        logger.info(f"Found {len(approved_plans)} approved plans")

        # Get ideas by status for summary
        idea_counts = idea_repo.count_by_status()
        logger.info(f"Idea status summary: {idea_counts}")

        # Generate report
        stats = {
            'pending_ideas': len(pending_ideas),
            'approved_plans': len(approved_plans),
            'idea_counts': idea_counts,
        }

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Backlog processing completed in {duration:.1f}s")
        logger.info(f"Stats: {stats}")

    except Exception as e:
        logger.error(f"Backlog processing failed: {e}", exc_info=True)
        raise


def process_backlog():
    """Process pending backlog items."""
    _process_backlog()


async def _health_check_async():
    """Async implementation of health check."""
    from ..llm import HybridLLMRouter
    from ..db import get_database
    from ..cache import get_cache
    from ..providers.ollama import OllamaProvider

    logger.info("Running system health check...")

    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'components': {},
    }

    try:
        # Check database
        try:
            db = get_database()
            db.get_session()
            health_status['components']['database'] = {'status': 'healthy'}
            logger.info("Database: healthy")
        except Exception as e:
            health_status['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'
            logger.error(f"Database: unhealthy - {e}")

        # Check cache
        try:
            cache = get_cache()
            cache.set('health_check', 'ok', ttl=60)
            result = cache.get('health_check')
            cache_health = cache.health_check()
            if result == 'ok':
                health_status['components']['cache'] = {
                    'status': 'healthy',
                    'type': cache_health.get('type', 'unknown'),
                }
                logger.info(f"Cache: healthy ({cache_health.get('type', 'unknown')})")
            else:
                health_status['components']['cache'] = {'status': 'degraded'}
                logger.warning("Cache: degraded")
        except Exception as e:
            health_status['components']['cache'] = {'status': 'unhealthy', 'error': str(e)}
            logger.warning(f"Cache: unhealthy - {e}")

        # Check Ollama
        try:
            ollama = OllamaProvider()
            ollama_health = await ollama.health_check()
            if ollama_health.get('status') == 'healthy':
                health_status['components']['ollama'] = {
                    'status': 'healthy',
                    'models': ollama_health.get('models', []),
                }
                logger.info(f"Ollama: healthy ({len(ollama_health.get('models', []))} models)")
            else:
                health_status['components']['ollama'] = {'status': 'degraded'}
                health_status['status'] = 'degraded'
                logger.warning("Ollama: degraded")
        except Exception as e:
            health_status['components']['ollama'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'
            logger.error(f"Ollama: unhealthy - {e}")

        # Check LLM router
        try:
            router = HybridLLMRouter()
            router_health = await router.health_check()
            health_status['components']['llm_router'] = {
                'status': router_health.get('status', 'unknown'),
                'budget': router_health.get('budget', {}),
            }
            logger.info(f"LLM Router: {router_health.get('status')}")
        except Exception as e:
            health_status['components']['llm_router'] = {'status': 'unhealthy', 'error': str(e)}
            logger.error(f"LLM Router: unhealthy - {e}")

        # Log final status
        logger.info(f"Health check completed: {health_status['status']}")

        # Store health status in cache
        try:
            cache = get_cache()
            cache.set('system_health', health_status, ttl=300)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status


def health_check():
    """Check system health."""
    result = asyncio.run(_health_check_async())
    if result['status'] != 'healthy':
        sys.exit(1)
