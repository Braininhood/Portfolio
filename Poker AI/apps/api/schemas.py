"""Pydantic API models (Phase 10)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    schema_revision: str | None = None
    hands_in_store: int | None = None
    offline_mode: bool = True


# ---------------------------------------------------------------------------
# Hardware / system status schemas
# ---------------------------------------------------------------------------


class CpuInfoSchema(BaseModel):
    name: str
    physical_cores: int
    logical_cores: int
    arch: str


class GpuInfoSchema(BaseModel):
    name: str
    vram_gb: float
    driver_version: str
    cuda_version: str | None = None
    cuda_available: bool = False


class RamInfoSchema(BaseModel):
    total_gb: float
    available_gb: float


class WorkerRecommendationSchema(BaseModel):
    recommended: int = Field(description="Recommended POKER_AI_NUM_WORKERS value")
    max_safe: int = Field(description="Maximum without degrading system responsiveness")
    current_env: int = Field(description="Current POKER_AI_NUM_WORKERS value (0 = not set)")
    warning: str | None = Field(default=None, description="Non-null if current setting looks wrong")
    explanation: str = Field(description="Plain-English explanation for why this value is recommended")
    by_task: dict[str, int] = Field(
        default_factory=dict,
        description="Per-task recommended worker counts",
    )


class ModelStatusSchema(BaseModel):
    name: str
    ready: bool
    path: str | None = None
    trained_at: str | None = None
    note: str | None = None
    job_type: str | None = Field(
        default=None,
        description="Background task that produces this artifact (links Status → Tasks)",
    )
    why: str | None = Field(default=None, description="Plain-English reason this artifact matters")


class TexasSolverStatusSchema(BaseModel):
    found: bool
    exe_path: str | None = None
    version: str | None = None
    note: str | None = None


class DiskInfoSchema(BaseModel):
    free_gb: float
    total_gb: float
    path: str


class SystemStatusResponse(BaseModel):
    """Full system status — hardware, models, database, and worker recommendations."""

    version: str
    os_name: str
    os_platform: str
    cpu: CpuInfoSchema
    gpu: GpuInfoSchema | None = None
    ram: RamInfoSchema
    disk: DiskInfoSchema
    workers: WorkerRecommendationSchema
    db_hands: int | None = None
    db_revision: str | None = None
    models: list[ModelStatusSchema] = Field(default_factory=list)
    texas_solver: TexasSolverStatusSchema
    jobs_running: int = 0
    jobs_queued: int = 0


# ---------------------------------------------------------------------------
# Health check (first-load page)
# ---------------------------------------------------------------------------


class HealthCheckItem(BaseModel):
    """Single check result with cross-platform remediation advice."""

    id: str
    name: str
    status: str = Field(description="pass | warn | fail")
    value: str = Field(description="Human-readable current state")
    advice: str | None = Field(default=None, description="What to do if warn/fail")
    fix_windows: str | None = Field(default=None, description="Exact fix command for Windows")
    fix_linux: str | None = Field(default=None, description="Exact fix command for Linux")
    fix_macos: str | None = Field(default=None, description="Exact fix command for macOS")
    can_skip: bool = Field(default=True, description="Whether app works without this")
    can_auto_install: bool = Field(default=False, description="Whether the API can auto-install this component")
    docs_section: str | None = Field(default=None, description="Relevant section in WEB_IMPLEMENTATION_GUIDE.md")


class HealthCheckResponse(BaseModel):
    """Structured health check result for the first-load page."""

    os_name: str
    os_platform: str  # "win32" | "linux" | "darwin"
    all_passed: bool
    has_warnings: bool
    checks: list[HealthCheckItem]


class ActionProb(BaseModel):
    kind: str
    amount_chips: int
    seat: int
    prob: float
    label: str | None = None


class DecideRequest(BaseModel):
    hand_id: int | None = Field(default=None, description="Canonical store hand_id.")
    step_index: int = Field(
        default=0,
        ge=0,
        description="Actions applied before decision (0 = first voluntary node).",
    )
    game_state: dict[str, Any] | None = Field(
        default=None,
        description="Live engine state from play session (see play_session_snapshot.game_state_to_dict).",
    )
    profile_id: str = "hero"
    policy: str = Field(default="distilled", description="distilled | best | heuristic")
    thinking_ms: int = Field(default=0, ge=0, le=500)
    deep_search: bool = Field(
        default=False,
        description="Enable depth-limited re-solver (auto when thinking_ms > 200 if unset).",
    )
    include_equity: bool = Field(
        default=False,
        description="Attach live MC hero equity (HUD / play hints).",
    )


class DecideResponse(BaseModel):
    policy_name: str
    policy_version: str
    latency_ms: float
    actions: list[ActionProb]
    explanation: str
    street: str | None = None
    acting_seat: int | None = None
    hero_equity: float | None = Field(
        default=None,
        description="Live MC pot equity when include_equity=true.",
    )


class HandListItem(BaseModel):
    hand_id: int
    stakes: str
    num_players: int
    hero_position: str | None
    hero_cards: str | None
    board_preview: str | None
    num_actions: int
    label: str


class HandListResponse(BaseModel):
    total: int
    hands: list[HandListItem]
    hint: str | None = None


class DrillHandListItem(HandListItem):
    has_decision_point: bool
    hero_decision_count: int = 0


class DrillHandsResponse(BaseModel):
    total: int
    hands: list[DrillHandListItem]
    hint: str | None = None


class DrillSpotRequest(BaseModel):
    hand_id: int
    step_index: int = Field(ge=0, description="Hero decision index (same as /decide step_index).")
    policy: str = Field(default="best", description="distilled | best | heuristic")
    thinking_ms: int = Field(default=0, ge=0, le=500)
    deep_search: bool = False
    include_equity: bool = Field(default=True, description="Attach live MC hero equity.")


class DrillSpotResponse(BaseModel):
    policy_name: str
    policy_version: str
    latency_ms: float
    actions: list[ActionProb]
    explanation: str
    street: str | None = None
    acting_seat: int | None = None
    step_index: int
    actual_action: str
    actual_amount: float | None = None
    hero_cards: str | None = None
    board: str | None = None
    position: str | None = None
    pot_bb: float | None = None
    stack_bb: float | None = None
    spr: float | None = None
    action_comparison: str
    policy_vs_human: str
    ai_top_action: str | None = None
    ai_top_prob: float | None = None
    hero_equity: float | None = None


class DrillCompareActionRow(BaseModel):
    label: str
    prob: float


class DrillCompareColumn(BaseModel):
    policy_key: str
    policy_label: str
    policy_name: str
    latency_ms: float
    actions: list[DrillCompareActionRow]


class DrillCompareRequest(BaseModel):
    hand_id: int
    step_index: int = Field(ge=0)
    thinking_ms: int = Field(default=0, ge=0, le=500)
    deep_search: bool = False


class DrillCompareResponse(BaseModel):
    policies: list[DrillCompareColumn]
    consensus: str
    actual_action: str
    actual_amount: float | None = None
    hero_cards: str | None = None
    board: str | None = None
    street: str | None = None
    position: str | None = None
    pot_bb: float | None = None
    stack_bb: float | None = None
    spr: float | None = None


class DrillStepsResponse(BaseModel):
    hand_id: int
    step_indices: list[int]


class ReplayActionOverlay(BaseModel):
    index: int
    street: str
    position: str
    action_type: str
    amount: float
    amount_bb: float | None = None
    description: str
    overlay: list[ActionProb] | None = None
    hero_equity: float | None = Field(
        default=None,
        description="Backfilled or live hero equity at this street (0–1).",
    )


class ReplayResponse(BaseModel):
    hand_id: int
    num_actions: int
    pot_trace_ok: bool
    action_sequence_ok: bool
    hero_position: str | None
    hero_cards: str | None
    board_cards: str | None
    stakes: str | None = None
    big_blind: float | None = None
    num_players: int | None = None
    actions: list[ReplayActionOverlay]
    summary: str | None = None
    overlay_enabled: bool = False
    overlay_steps: int = 0


class LeaderboardRow(BaseModel):
    agent_id: str
    elo: float | None = None
    hands: int | None = None
    bb_per_100: float | None = None
    aivat_bb_per_100: float | None = None


class LeaderboardResponse(BaseModel):
    finished_at: str | None = None
    hands_played: int | None = None
    promoted: bool | None = None
    rows: list[LeaderboardRow]


class CheckpointRow(BaseModel):
    checkpoint_id: str
    created_at: str | None = None
    main_elo: float | None = None
    hands: int | None = None
    promoted: bool | None = None
    note: str | None = None
    is_current: bool = False


class CheckpointsResponse(BaseModel):
    current: str | None = None
    rows: list[CheckpointRow]


class ReplayAgentRow(BaseModel):
    agent_id: str
    hands: int | None = None
    hero_decisions: int | None = None
    bb_per_100: float | None = None
    aivat_bb_per_100: float | None = None
    action_match_pct: float | None = None


class ReplayLeagueResponse(BaseModel):
    finished_at: str | None = None
    hands_scored: int | None = None
    hero_decisions: int | None = None
    aivat_mode: str | None = None
    agents: list[ReplayAgentRow] = Field(default_factory=list)
    by_format: dict[str, dict[str, float]] = Field(default_factory=dict)


class AivatAuditResponse(BaseModel):
    finished_at: str | None = None
    aivat_mode: str | None = None
    hands: int | None = None
    naive_stderr: float | None = None
    full_stderr: float | None = None
    stderr_reduction_pct: float | None = None
    report_path: str | None = None


class BlueprintSection(BaseModel):
    id: str
    title: str
    body: str


class BlueprintResponse(BaseModel):
    title: str
    version: str
    sections: list[BlueprintSection]
    raw_yaml: str | None = None


class SimEvent(BaseModel):
    event: str
    payload: dict[str, Any]


class PlayerSummaryRow(BaseModel):
    player_uid: str
    display_name: str
    hands: int
    source: str = "import"


class PlayerListResponse(BaseModel):
    total: int
    players: list[PlayerSummaryRow]
    hint: str | None = None


class StyleStatsRow(BaseModel):
    vpip_pct: float
    pfr_pct: float
    aggression_factor: float
    hands_dealt: int


class NeighbourRow(BaseModel):
    player_uid: str
    display_name: str
    similarity_pct: float
    example_hand_id: int


class ChangepointBrief(BaseModel):
    detected_at: str
    description: str
    confidence: float


class PlayerProfileResponse(BaseModel):
    player_uid: str
    display_name: str
    hands_in_sample: int
    summary: str
    player_type: str
    stats: StyleStatsRow
    similar_players: list[NeighbourRow]
    changepoint: ChangepointBrief | None = None


class RangeBucketRow(BaseModel):
    tier: str
    label: str
    mass_pct: float


class PlayerRangeResponse(BaseModel):
    player_uid: str
    observed_actions: int
    buckets: list[RangeBucketRow]
    confidence_label: str
    confidence_pct: float
    last_updated_at: str | None = None
    last_hand_id: int | None = None
    note: str | None = None


class LeakRowSchema(BaseModel):
    rank: int
    title: str
    bb_per_100: float
    description: str


class CounterfactualExampleSchema(BaseModel):
    hand_id: int
    street: str
    actual_action: str
    counterfactual_action: str
    ev_delta_bb: float
    narrative: str


class PlayerCausalResponse(BaseModel):
    player_uid: str
    hands_analyzed: int
    counterfactual: CounterfactualExampleSchema | None = None
    leaks: list[LeakRowSchema]
    total_leak_bb_per_100: float
    note: str | None = None


class SolverSpotSummary(BaseModel):
    cache_key: str
    board: str
    backend: str
    top_action: str
    top_frequency_pct: float


class SolverSpotsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    spots: list[SolverSpotSummary]


class SolverActionRow(BaseModel):
    action: str
    frequency_pct: float


class SolverSpotDetail(BaseModel):
    cache_key: str
    board: str
    backend: str
    summary: str
    board_note: str | None = None
    actions: list[SolverActionRow]
    meta: dict[str, Any] = Field(default_factory=dict)


class SolverStatsResponse(BaseModel):
    total_spots: int
    backends: dict[str, int]
    cache_dir: str


# ---------------------------------------------------------------------------
# Background jobs (Phase W1)
# ---------------------------------------------------------------------------


class JobProgressEvent(BaseModel):
    pct: int = 0
    msg: str = ""
    detail: dict[str, Any] | None = None
    status: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class JobRequest(BaseModel):
    type: str = Field(..., description="Job type key (ingest, features_build, …)")
    params: dict[str, Any] = Field(default_factory=dict)


class JobCreatedResponse(BaseModel):
    job_id: str


class JobSummary(BaseModel):
    job_id: str
    type: str
    status: str
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    progress: JobProgressEvent | None = None
    error: str | None = None


class JobNextStep(BaseModel):
    label: str
    path: str
    hint: str | None = None
    action: str | None = Field(
        default=None,
        description="'start_job' runs a background task; default is navigate to path",
    )
    job_type: str | None = None
    job_params: dict[str, Any] = Field(default_factory=dict)


class JobFriendlySummary(BaseModel):
    headline: str
    explanation: str
    advice: list[str] = Field(default_factory=list)
    next_steps: list[JobNextStep] = Field(default_factory=list)
    severity: str = "info"


class JobDetailResponse(JobSummary):
    params: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    friendly: JobFriendlySummary | None = None


class JobListResponse(BaseModel):
    jobs: list[JobSummary]
    total: int


class ScheduleEntrySchema(BaseModel):
    job_type: str
    label: str
    enabled: bool
    time_local: str
    frequency: str
    day_of_week: str | None = None
    os_installed: bool = False
    last_run_at: str | None = None
    last_run_status: str | None = None


class ScheduleListResponse(BaseModel):
    platform: str
    scheduler_available: bool
    nightly_enabled: bool
    nightly_start_time: str = "00:00"
    entries: list[ScheduleEntrySchema]
    last_nightly_run_at: str | None = None
    message: str | None = None


class ScheduleRequest(BaseModel):
    job_type: str = Field(..., description="features_build, train_hhformer, …")
    enabled: bool = True
    time_local: str = Field(default="00:00", description="Local time HH:MM")
    frequency: str = Field(default="daily", description="daily | weekly")
    day_of_week: str | None = Field(default=None, description="SUN … SAT when weekly")


class NightlyScheduleRequest(BaseModel):
    enabled: bool
    start_time: str = Field(default="00:00", description="First job start (others staggered)")


class ScheduleUpdateResponse(BaseModel):
    ok: bool = True
    entries: list[ScheduleEntrySchema]
    message: str | None = None


# ---------------------------------------------------------------------------
# Equity calculator (Phase W5)
# ---------------------------------------------------------------------------


class EquityRequest(BaseModel):
    hero_cards: str = Field(..., description="Two cards, e.g. 'Ah Kd'")
    board_cards: str = Field(default="", description="0–5 board cards, space-separated")
    villain_range: str = Field(
        default="random",
        description="'random' | 'TT+' | 'AKs,AQs' | specific 'AhKd'",
    )
    mode: str = Field(
        default="exact",
        description="'exact' | 'mc' | 'auto' — MC for preflop or very wide ranges",
    )
    num_samples: int = Field(default=5000, ge=500, le=500_000)


class EquityResponse(BaseModel):
    hero_equity: float = Field(description="Hero pot share (wins + half ties)")
    villain_equity: float = Field(description="Villain pot share (1 - hero_equity)")
    tie_equity: float = Field(description="Fraction of runouts that chop")
    hero_cards: str
    board_cards: str | None = None
    villain_range: str
    mode_used: str
    latency_ms: float
    breakdown: dict[str, float] = Field(default_factory=dict)
    insight: str | None = None


# ---------------------------------------------------------------------------
# Play vs AI (Phase W7)
# ---------------------------------------------------------------------------


class PlayBotInfo(BaseModel):
    id: str
    name: str
    difficulty: str


class PlayBotsResponse(BaseModel):
    bots: list[PlayBotInfo]


class PlaySessionConfigRequest(BaseModel):
    seats: int = Field(default=6, ge=2, le=9)
    user_seat: int = Field(default=0, ge=0)
    bots: list[str] = Field(default_factory=list)
    buy_in_bb: int = Field(default=100, ge=20, le=500)
    small_blind_bb: float = Field(default=0.5, gt=0)
    big_blind_bb: float = Field(default=1.0, gt=0)
    ante_bb: float = Field(default=0.0, ge=0, le=10)
    timeout_ms: int = Field(default=10_000, ge=3_000, le=60_000)


class PlaySessionCreateResponse(BaseModel):
    session_id: str


class PlaySessionSummary(BaseModel):
    session_id: str
    created_at: str | None = None
    status: str
    hands_played: int
    net_bb: float
    vpip_pct: float
    pfr_pct: float
    table_config: dict[str, Any] = Field(default_factory=dict)


class PlaySessionListResponse(BaseModel):
    sessions: list[PlaySessionSummary]


class PlayHandSummary(BaseModel):
    hand_no: int
    result_bb: float
    went_showdown: bool
    board: str | None = None
    hero_cards: str | None = None
    hero_hand_name: str | None = None
    winner_name: str | None = None
    all_in_count: int = 0


class PlayHandDetail(BaseModel):
    hand_no: int
    result_bb: float
    went_showdown: bool
    board: str | None = None
    hero_cards: str | None = None
    hero_hand: dict[str, Any] = Field(default_factory=dict)
    action_log: list[dict[str, Any]] = Field(default_factory=list)
    showdown: list[dict[str, Any]] = Field(default_factory=list)
    winner: dict[str, Any] | None = None
    all_in_count: int = 0
    bot_lineup: dict[str, str | None] = Field(default_factory=dict)
    ending_street: str | None = None


class PlayStudyHandsResponse(BaseModel):
    session_id: str
    hands: list[PlayHandDetail] = Field(default_factory=list)
    note: str | None = None


class PlaySessionResumeInfo(BaseModel):
    phase: str | None = None
    hand_no: int | None = None
    street: str | None = None
    updated_at: str | None = None


class PlaySessionResumeResponse(BaseModel):
    session: PlaySessionSummary
    persisted_hands: int = 0
    resume: PlaySessionResumeInfo | None = None
    can_resume: bool = False


class PlayStudySessionCatalogItem(BaseModel):
    session_id: str
    status: str | None = None
    hands_played: int = 0
    persisted_hands: int = 0
    net_bb: float = 0.0
    table_config: dict[str, Any] = Field(default_factory=dict)
    updated_at: str | None = None


class PlayStudyCatalogResponse(BaseModel):
    sessions: list[PlayStudySessionCatalogItem] = Field(default_factory=list)
    total_sessions: int = 0
    total_persisted_hands: int = 0
    note: str | None = None


class PlayStudyExportHand(BaseModel):
    session_id: str
    session_status: str | None = None
    table_config: dict[str, Any] = Field(default_factory=dict)
    hand_no: int
    result_bb: float
    went_showdown: bool
    board: str | None = None
    hero_cards: str | None = None
    hand_record: dict[str, Any] = Field(default_factory=dict)


class PlayStudyExportResponse(BaseModel):
    hands: list[PlayStudyExportHand] = Field(default_factory=list)
    count: int = 0


class PlayStudyStatusResponse(BaseModel):
    database_path: str
    database_exists: bool
    sessions: int = 0
    hands: int = 0
    hero_decisions: int = 0
    hero_decisions_hu: int = 0
    hero_decisions_multiway: int = 0
    hero_decisions_skipped: int = 0
    showdown_hands: int = 0
    ready_for_training: bool = False
    manifest_path: str | None = None
    manifest: dict[str, Any] | None = None
    note: str | None = None


class PlayStudyTrainJobInfo(BaseModel):
    job_id: str
    job_type: str
    route: str
    output: str
    decision_count: int = 0


class PlayStudyPrepareResponse(BaseModel):
    job_id: str
    message: str


class PlayStudyTrainResponse(BaseModel):
    job_id: str
    message: str
    manifest_path: str
    hero_decisions: int = 0
    hero_decisions_hu: int = 0
    hero_decisions_multiway: int = 0
    jobs: list[PlayStudyTrainJobInfo] = Field(default_factory=list)


class PlaySessionDetailResponse(BaseModel):
    session: PlaySessionSummary
    hands: list[PlayHandSummary] = Field(default_factory=list)


class PlaySessionEndResponse(BaseModel):
    status: str
    summary: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Phase W9 — Hardening, packaging & compliance
# ---------------------------------------------------------------------------


class SmokeCheck(BaseModel):
    name: str
    passed: bool
    latency_ms: float
    detail: str | None = None


class SmokeResponse(BaseModel):
    all_passed: bool
    checks: list[SmokeCheck]


class LicenseEntry(BaseModel):
    package: str
    version: str
    license_type: str
    url: str | None = None
    note: str | None = None


class LicensesResponse(BaseModel):
    entries: list[LicenseEntry]
    generated_note: str | None = None


class ModelCardResponse(BaseModel):
    name: str
    version: str | None = None
    markdown: str
    path: str | None = None


class ComplianceResponse(BaseModel):
    owned_data_only: bool = True
    no_external_ai_services: bool = True
    offline_mode_verified: bool
    tos_note: str
    datasheet_url: str | None = None
    licenses_count: int
    agpl_packages: list[str] = Field(default_factory=list)
