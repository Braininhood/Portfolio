from poker_ai.league.bench import measure_sim_throughput


def test_sim_throughput_at_least_100_hands_per_minute() -> None:
    stats = measure_sim_throughput(wall_sec=10.0, num_seats=6)
    assert stats["hands"] >= 10
    assert stats["hands_per_minute"] >= 100.0, stats
