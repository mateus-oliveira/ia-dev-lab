"""Generate synthetic raw player event data for the Player Modeling Lab POC.

Simulates an unprocessed event stream as it would arrive from a game
platform: events from different players are interleaved by arrival time,
some optional fields may be missing, and the numeric column reused across
event types (`event_value`) has a meaning that depends on `event_type`.
The output feeds the pipeline's Validation/Extract stages and must not be
edited afterwards.
"""

from __future__ import annotations

import csv
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "player_events.csv"
RANDOM_SEED = 42
TOTAL_EVENTS = 1000
NUM_PLAYERS = 80
DUPLICATE_RATE = 0.015
MISSING_PLATFORM_RATE = 0.05
MISSING_SCENARIO_RATE = 0.03

FIELDNAMES = [
    "event_id",
    "player_id",
    "session_id",
    "timestamp",
    "event_type",
    "game_scenario",
    "social_mode",
    "platform",
    "player_level",
    "event_value",
    "reported_flag",
]

PLATFORMS = ["pc", "console", "mobile"]
SOCIAL_MODES = ["singleplayer", "multiplayer_coop", "multiplayer_pvp"]

NON_QUEST_SCENARIOS = ["menu", "lobby", "shop", "tutorial"]
LEVEL_SCENARIOS = [f"level_{n}" for n in range(1, 6)]
QUEST_SCENARIOS = [
    "quest_forest_rescue",
    "quest_dragon_hunt",
    "quest_lost_relic",
    "quest_castle_siege",
    "quest_goblin_camp",
]
PRIMARY_SCENARIO_POOL = (
    QUEST_SCENARIOS * 4
    + LEVEL_SCENARIOS * 3
    + ["pvp_arena"] * 2
    + NON_QUEST_SCENARIOS
)

MID_SESSION_EVENT_TYPES = [
    "level_start",
    "level_complete",
    "level_fail",
    "quest_accept",
    "quest_complete",
    "quest_abandon",
    "item_pickup",
    "item_purchase",
    "item_sell",
    "player_death",
    "enemy_kill",
    "damage_taken",
    "level_up",
    "achievement_unlocked",
    "chat_message",
    "friend_request_sent",
    "party_join",
    "party_leave",
    "matchmaking_start",
    "matchmaking_complete",
    "rage_quit",
    "afk_timeout",
]


def scenario_for_event(event_type: str, primary_scenario: str) -> str:
    """Pick the game scenario/location associated with an event.

    :param event_type: The kind of action the player performed.
    :param primary_scenario: The dominant scenario chosen for the session.

    :return: The scenario label to record for this event.
    """
    if event_type in {"session_start", "session_end", "login", "logout"}:
        return "lobby"
    if event_type in {"quest_accept", "quest_complete", "quest_abandon"}:
        return primary_scenario if primary_scenario in QUEST_SCENARIOS else random.choice(QUEST_SCENARIOS)
    if event_type in {"level_start", "level_complete", "level_fail"}:
        return primary_scenario if primary_scenario in LEVEL_SCENARIOS else random.choice(LEVEL_SCENARIOS)
    if event_type in {"matchmaking_start", "matchmaking_complete", "party_join", "party_leave"}:
        return "lobby"
    if event_type == "chat_message":
        return random.choice(["lobby", "menu", primary_scenario])
    return primary_scenario


def event_value_for(event_type: str) -> float | None:
    """Compute the numeric payload for an event, when the event type carries one.

    The column is intentionally overloaded (raw telemetry style): its unit
    depends on `event_type` (damage points, currency, XP, seconds, ...) and
    must be disambiguated during the Transform stage.

    :param event_type: The kind of action the player performed.

    :return: A numeric value for events that carry one, otherwise None.
    """
    if event_type == "damage_taken":
        return random.randint(1, 100)
    if event_type == "enemy_kill":
        return random.randint(1, 3)
    if event_type in {"item_purchase", "item_sell"}:
        return random.randint(5, 500)
    if event_type == "quest_complete":
        return random.randint(50, 500)
    if event_type == "level_up":
        return random.randint(100, 1000)
    if event_type == "achievement_unlocked":
        return random.randint(10, 200)
    return None


def build_event(
    player_id: str,
    session_id: str,
    timestamp: datetime,
    event_type: str,
    game_scenario: str,
    social_mode: str,
    platform: str,
    player_level: int,
) -> dict[str, Any]:
    """Assemble a single raw event row.

    :param player_id: Synthetic identifier of the player who triggered the event.
    :param session_id: Identifier of the play session the event belongs to.
    :param timestamp: Moment the event occurred.
    :param event_type: The kind of action the player performed.
    :param game_scenario: Quest/level/menu context in which the event happened.
    :param social_mode: Whether the session was singleplayer or multiplayer.
    :param platform: Device the player used.
    :param player_level: Player's progression level at event time.

    :return: A dict matching FIELDNAMES, ready to be written to CSV.
    """
    reported_flag: int | str = ""
    if event_type == "chat_message":
        reported_flag = 1 if random.random() < 0.08 else 0

    return {
        "event_id": uuid.uuid4().hex[:12],
        "player_id": player_id,
        "session_id": session_id,
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": event_type,
        "game_scenario": game_scenario,
        "social_mode": social_mode,
        "platform": platform,
        "player_level": player_level,
        "event_value": event_value_for(event_type) if event_type != "" else "",
        "reported_flag": reported_flag,
    }


def generate_player_events(player_id: str, reference_time: datetime) -> list[dict[str, Any]]:
    """Generate the full event history for a single synthetic player.

    :param player_id: Synthetic identifier of the player.
    :param reference_time: Upper bound timestamp used to anchor the player's activity window.

    :return: List of raw event rows for this player, in chronological order.
    """
    events: list[dict[str, Any]] = []
    current_level = random.randint(1, 5)
    num_sessions = random.randint(1, 4)
    platform = random.choice(PLATFORMS)
    session_time = reference_time - timedelta(days=random.randint(0, 45))

    for session_index in range(num_sessions):
        session_id = f"{player_id}_s{session_index + 1}"
        social_mode = random.choices(SOCIAL_MODES, weights=[0.4, 0.35, 0.25])[0]
        primary_scenario = random.choice(PRIMARY_SCENARIO_POOL)
        num_mid_events = random.randint(4, 16)

        session_time += timedelta(hours=random.uniform(2, 96))
        events.append(
            build_event(
                player_id, session_id, session_time, "session_start",
                "lobby", social_mode, platform, current_level,
            )
        )

        for _ in range(num_mid_events):
            session_time += timedelta(seconds=random.randint(5, 240))
            event_type = random.choice(MID_SESSION_EVENT_TYPES)
            if event_type == "level_up":
                current_level += 1
            scenario = scenario_for_event(event_type, primary_scenario)
            events.append(
                build_event(
                    player_id, session_id, session_time, event_type,
                    scenario, social_mode, platform, current_level,
                )
            )

        session_time += timedelta(seconds=random.randint(5, 120))
        events.append(
            build_event(
                player_id, session_id, session_time, "session_end",
                "lobby", social_mode, platform, current_level,
            )
        )

    return events


def apply_raw_data_noise(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Blank out a few optional fields and inject duplicate rows.

    Mimics common raw-telemetry defects (dropped fields, retried sends) so
    the pipeline's future Validation stage has something real to catch.

    :param events: Clean event rows, in chronological order.

    :return: The same rows with missing values and duplicates injected.
    """
    for event in events:
        if random.random() < MISSING_PLATFORM_RATE:
            event["platform"] = ""
        if random.random() < MISSING_SCENARIO_RATE:
            event["game_scenario"] = ""

    num_duplicates = int(len(events) * DUPLICATE_RATE)
    duplicates = [dict(event) for event in random.sample(events, num_duplicates)]
    return events + duplicates


def main() -> None:
    """Generate the synthetic raw event CSV and write it to data/raw/."""
    random.seed(RANDOM_SEED)
    reference_time = datetime.now(timezone.utc).replace(microsecond=0)

    all_events: list[dict[str, Any]] = []
    for player_index in range(NUM_PLAYERS):
        player_id = f"player_{player_index + 1:04d}"
        all_events.extend(generate_player_events(player_id, reference_time))

    all_events = apply_raw_data_noise(all_events)
    all_events.sort(key=lambda event: event["timestamp"])

    if len(all_events) > TOTAL_EVENTS:
        all_events = all_events[:TOTAL_EVENTS]
    elif len(all_events) < TOTAL_EVENTS:
        missing = TOTAL_EVENTS - len(all_events)
        extra_player_id = f"player_{NUM_PLAYERS + 1:04d}"
        while len(all_events) < TOTAL_EVENTS:
            all_events.extend(generate_player_events(extra_player_id, reference_time))
        all_events.sort(key=lambda event: event["timestamp"])
        all_events = all_events[:TOTAL_EVENTS]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_events)

    print(f"Wrote {len(all_events)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
