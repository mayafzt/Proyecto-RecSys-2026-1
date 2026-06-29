from __future__ import annotations

import math
import os
import random
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib import parse, request

import duckdb
import pandas as pd


DATA_PATH = Path("data/spotify_dataset.csv")
OUTPUT_PREFIX = os.getenv("MIDTERM_OUTPUT_PREFIX", "resultados_hito2_midterm")
RESULT_CSV = Path(f"{OUTPUT_PREFIX}.csv")
RESULT_MD = Path(f"{OUTPUT_PREFIX}.md")
EXAMPLES_CSV = Path(f"{OUTPUT_PREFIX}_ejemplos.csv")
SEGMENTS_CSV = Path(f"{OUTPUT_PREFIX}_segmentos.csv")

SAMPLE_PERCENT = int(os.getenv("MIDTERM_SAMPLE_PERCENT", "30"))
TOP_K = 10
RANDOM_SEED = 42
MAX_EVAL_PLAYLISTS = int(os.getenv("MIDTERM_MAX_EVAL_PLAYLISTS", "20000"))
MAX_SAMPLE_PLAYLISTS = int(os.getenv("MIDTERM_MAX_SAMPLE_PLAYLISTS", "0"))

# Retrieval + reranking configuration.
MAX_ITEMS_PER_PLAYLIST_FOR_COOC = 80
MAX_NEIGHBORS_PER_SEED = 150
MAX_CANDIDATES = 400

# LastFM is optional and bounded by a max number of API calls.
ENABLE_LASTFM = os.getenv("MIDTERM_ENABLE_LASTFM", "0") == "1"
LASTFM_MAX_CALLS = int(os.getenv("MIDTERM_LASTFM_MAX_CALLS", "1500"))

BASE_WEIGHTS = {
    "cooc": 0.55,
    "pop": 0.15,
    "artist": 0.15,
    "name": 0.15,
    "lastfm": 0.0,
}


# Simple timestamped logger for long-running experiment steps.
def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


# Normalize free text into a compact token set used by name-based features.
def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    stop = {
        "the",
        "and",
        "for",
        "con",
        "las",
        "los",
        "una",
        "de",
        "la",
        "el",
        "in",
        "to",
        "of",
        "my",
        "mix",
        "playlist",
        "music",
    }
    return {token for token in tokens if len(token) > 2 and token not in stop}


# HitRate is 1 when the held-out item appears inside the top-k list.
def hit_rate_at_k(recommended: list[str], relevant: str, k: int) -> float:
    return float(relevant in recommended[:k])


# With one relevant item per playlist, Precision@k is either 0 or 1/k.
def precision_at_k(recommended: list[str], relevant: str, k: int) -> float:
    return float(relevant in recommended[:k]) / k


# Average precision collapses to the inverse rank of the held-out item.
def average_precision_at_k(recommended: list[str], relevant: str, k: int) -> float:
    for rank, item in enumerate(recommended[:k], start=1):
        if item == relevant:
            return 1.0 / rank
    return 0.0


# nDCG rewards placing the held-out item as high as possible in the list.
def ndcg_at_k(recommended: list[str], relevant: str, k: int) -> float:
    for rank, item in enumerate(recommended[:k], start=1):
        if item == relevant:
            return 1.0 / math.log2(rank + 1)
    return 0.0


# Intra-list diversity using artist mismatch ratio in pairwise comparisons.
def artist_diversity_at_k(recommended: list[str], item_meta: dict[str, tuple[str, str]], k: int) -> float:
    items = recommended[:k]
    n = len(items)
    if n < 2:
        return 0.0
    diff_pairs = 0
    total_pairs = 0
    for i in range(n):
        ai = item_meta.get(items[i], ("", ""))[0]
        for j in range(i + 1, n):
            aj = item_meta.get(items[j], ("", ""))[0]
            total_pairs += 1
            diff_pairs += int(ai != aj)
    return diff_pairs / total_pairs if total_pairs else 0.0


# Novelty from training popularity as self-information in bits.
def novelty_at_k(
    recommended: list[str],
    item_counts: Counter[str],
    total_train_interactions: int,
    k: int,
) -> float:
    items = recommended[:k]
    if not items or total_train_interactions <= 0:
        return 0.0
    smooth = max(1, len(item_counts))
    denom = total_train_interactions + smooth
    score = 0.0
    for item in items:
        p = (item_counts.get(item, 0) + 1) / denom
        score += -math.log2(p)
    return score / len(items)


# Utility percentile function that avoids external dependencies.
def percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    sorted_vals = sorted(values)
    idx = int(round((len(sorted_vals) - 1) * q))
    idx = min(max(idx, 0), len(sorted_vals) - 1)
    return sorted_vals[idx]


# Bucket playlist size to analyze where each model helps more.
def playlist_size_bucket(context_len: int) -> str:
    full_len = context_len + 1
    if full_len <= 10:
        return "short"
    if full_len <= 30:
        return "medium"
    return "long"


# Bucket target-item popularity to separate head/mid/tail behavior.
def target_pop_bucket(target_pop: int, p33: int, p66: int) -> str:
    if target_pop <= p33:
        return "tail"
    if target_pop <= p66:
        return "mid"
    return "head"


# Base DuckDB relation used to scan the raw CSV with normalized column names.
def base_relation() -> str:
    return f"""
    read_csv(
      '{DATA_PATH.as_posix()}',
      header=true,
      ignore_errors=true,
      all_varchar=true,
      normalize_names=true
    )
    """


# Build the deterministic playlist sample used in the experiments.
def load_playlist_sample(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    log(f"Cargando muestra deterministica del {SAMPLE_PERCENT}% por playlist")
    if MAX_SAMPLE_PLAYLISTS > 0:
        query = f"""
            WITH data AS (
                SELECT
                    playlistname,
                    lower(trim(artistname)) || ' - ' || lower(trim(trackname)) AS item_id,
                    user_id || '||' || playlistname AS playlist_id
                FROM {base_relation()}
                WHERE user_id IS NOT NULL
                    AND artistname IS NOT NULL
                    AND trackname IS NOT NULL
                    AND playlistname IS NOT NULL
            ),
            sampled AS (
                SELECT playlistname, item_id, playlist_id
                FROM data
                WHERE hash(playlist_id) % 100 < {SAMPLE_PERCENT}
            ),
            keep_playlists AS (
                SELECT playlist_id
                FROM sampled
                GROUP BY playlist_id
                ORDER BY playlist_id
                LIMIT {MAX_SAMPLE_PLAYLISTS}
            )
            SELECT s.playlistname, s.item_id, s.playlist_id
            FROM sampled s
            JOIN keep_playlists k USING (playlist_id)
            """
    else:
        query = f"""
            WITH data AS (
                SELECT
                    playlistname,
                    lower(trim(artistname)) || ' - ' || lower(trim(trackname)) AS item_id,
                    user_id || '||' || playlistname AS playlist_id
                FROM {base_relation()}
                WHERE user_id IS NOT NULL
                    AND artistname IS NOT NULL
                    AND trackname IS NOT NULL
                    AND playlistname IS NOT NULL
            )
            SELECT playlistname, item_id, playlist_id
            FROM data
            WHERE hash(playlist_id) % 100 < {SAMPLE_PERCENT}
            """
    return con.execute(query).fetchdf()


# Split each playlist into context items and one held-out target song.
def build_split(
    df: pd.DataFrame,
) -> tuple[list[list[str]], list[str], list[str], dict[str, tuple[str, str]]]:
    grouped = df.groupby("playlist_id", sort=False).agg(
        item_id=("item_id", list),
        playlistname=("playlistname", "first"),
    )
    grouped["size"] = grouped["item_id"].str.len()
    grouped = grouped[grouped["size"] >= 3]
    if MAX_EVAL_PLAYLISTS > 0 and len(grouped) > MAX_EVAL_PLAYLISTS:
        grouped = grouped.iloc[:MAX_EVAL_PLAYLISTS]

    train_playlists = [items[:-1] for items in grouped["item_id"]]
    test_items = [items[-1] for items in grouped["item_id"]]
    playlist_names = grouped["playlistname"].astype(str).tolist()

    item_meta: dict[str, tuple[str, str]] = {}
    for item in set(df["item_id"].tolist()):
        if " - " in item:
            artist, track = item.split(" - ", 1)
        else:
            artist, track = item, ""
        item_meta[item] = (artist, track)

    return train_playlists, test_items, playlist_names, item_meta


# Random baseline used as a lower bound for recommendation quality.
def recommend_random(catalog: list[str], seen: set[str], rng: random.Random) -> list[str]:
    recommendations: list[str] = []
    used = set(seen)
    max_attempts = TOP_K * 120
    attempts = 0
    while len(recommendations) < TOP_K and attempts < max_attempts:
        attempts += 1
        item = rng.choice(catalog)
        if item not in used:
            recommendations.append(item)
            used.add(item)
    return recommendations


# Global popularity baseline with seen-item filtering.
def recommend_most_popular(popular_items: list[str], seen: set[str]) -> list[str]:
    recommendations = []
    for item in popular_items:
        if item not in seen:
            recommendations.append(item)
            if len(recommendations) == TOP_K:
                break
    return recommendations


# Baseline that backs off to items associated with playlist-name tokens.
def recommend_playlist_name(
    playlist_name: str,
    token_to_items: dict[str, list[str]],
    popular_items: list[str],
    seen: set[str],
) -> list[str]:
    scores: Counter[str] = Counter()
    for token in tokenize(playlist_name):
        for rank, item in enumerate(token_to_items.get(token, [])[:120]):
            if item not in seen:
                scores[item] += 1.0 / (rank + 1)

    recommendations = [item for item, _ in scores.most_common(TOP_K)]
    used = set(seen) | set(recommendations)
    for item in popular_items:
        if len(recommendations) == TOP_K:
            break
        if item not in used:
            recommendations.append(item)
            used.add(item)
    return recommendations


# Build item frequencies and cosine-normalized item neighbors.
def build_cooccurrence(
    train_playlists: list[list[str]],
) -> tuple[Counter[str], dict[str, Counter[str]], dict[str, list[tuple[str, float]]]]:
    log("Construyendo estadisticas de co-ocurrencia item-item")
    item_counts: Counter[str] = Counter()
    pair_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for playlist in train_playlists:
        uniq = list(dict.fromkeys(playlist))
        uniq = uniq[:MAX_ITEMS_PER_PLAYLIST_FOR_COOC]
        item_counts.update(uniq)
        n = len(uniq)
        for i in range(n):
            a = uniq[i]
            for j in range(i + 1, n):
                b = uniq[j]
                pair_counts[a][b] += 1
                pair_counts[b][a] += 1

    neighbors: dict[str, list[tuple[str, float]]] = {}
    for item, linked in pair_counts.items():
        scored = []
        ci = item_counts[item]
        for other, cij in linked.items():
            cj = item_counts[other]
            sim = cij / math.sqrt(ci * cj)
            scored.append((other, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        neighbors[item] = scored[:MAX_NEIGHBORS_PER_SEED]

    return item_counts, pair_counts, neighbors


# Build first-order transitions for a simple sequential APC comparator.
def build_markov_transitions(train_playlists: list[list[str]]) -> dict[str, Counter[str]]:
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    for playlist in train_playlists:
        seq = list(dict.fromkeys(playlist))
        for i in range(len(seq) - 1):
            transitions[seq[i]][seq[i + 1]] += 1
    return transitions


# Sequential recommender using recent seeds with rank-decayed voting.
def recommend_markov(
    context_items: list[str],
    transitions: dict[str, Counter[str]],
    popular_items: list[str],
    seen: set[str],
) -> list[str]:
    scores: Counter[str] = Counter()
    seeds = list(reversed(context_items[-3:]))
    for depth, seed in enumerate(seeds, start=1):
        for nxt, cnt in transitions.get(seed, {}).items():
            if nxt not in seen:
                scores[nxt] += cnt / depth

    ranked = [item for item, _ in scores.most_common(TOP_K)]
    used = set(seen) | set(ranked)
    for item in popular_items:
        if len(ranked) == TOP_K:
            break
        if item not in used:
            ranked.append(item)
            used.add(item)
    return ranked


# Collaborative item-kNN style recommender from item-item neighbors.
def recommend_item_knn(
    context_items: list[str],
    neighbors: dict[str, list[tuple[str, float]]],
    popular_items: list[str],
    seen: set[str],
) -> list[str]:
    scores: Counter[str] = Counter()
    for seed in context_items:
        for rank, (cand, sim) in enumerate(neighbors.get(seed, [])):
            if cand not in seen:
                scores[cand] += sim / (rank + 1)

    ranked = [item for item, _ in scores.most_common(TOP_K)]
    used = set(seen) | set(ranked)
    for item in popular_items:
        if len(ranked) == TOP_K:
            break
        if item not in used:
            ranked.append(item)
            used.add(item)
    return ranked


# Lightweight wrapper around LastFM artist similarity with local caching and budget.
class LastFMSimilarity:
    def __init__(self, api_key: str | None, timeout_s: int = 3, max_calls: int = 0) -> None:
        self.api_key = api_key or ""
        self.timeout_s = timeout_s
        self.max_calls = max_calls
        self.calls = 0
        self.cache: dict[tuple[str, str], float] = {}
        self.enabled = bool(self.api_key and self.max_calls > 0)

    # Query LastFM once per artist pair and reuse cached similarities afterwards.
    def artist_similarity(self, a: str, b: str) -> float:
        if not self.enabled:
            return 0.0
        left = a.strip().lower()
        right = b.strip().lower()
        if not left or not right:
            return 0.0
        if left == right:
            return 1.0
        key = tuple(sorted((left, right)))
        if key in self.cache:
            return self.cache[key]
        if self.calls >= self.max_calls:
            return 0.0

        self.calls += 1
        url = (
            "https://ws.audioscrobbler.com/2.0/?method=artist.getsimilar"
            f"&artist={parse.quote(left)}"
            f"&api_key={self.api_key}"
            "&format=json&limit=100"
        )

        try:
            with request.urlopen(url, timeout=self.timeout_s) as response:
                payload = response.read().decode("utf-8", errors="ignore")
            pattern = re.compile(r'"name"\s*:\s*"([^"]+)"\s*,\s*"match"\s*:\s*"([0-9.]+)"')
            similars = {name.lower(): float(score) for name, score in pattern.findall(payload)}
            value = float(similars.get(right, 0.0))
        except Exception:
            value = 0.0

        self.cache[key] = value
        return value


@dataclass
class TwoStageArtifacts:
    item_counts: Counter[str]
    neighbors: dict[str, list[tuple[str, float]]]
    item_meta: dict[str, tuple[str, str]]
    popular_items: list[str]
    token_to_items: dict[str, list[str]]
    lastfm: LastFMSimilarity


# Retrieve a bounded candidate set by aggregating neighbors of context items.
def retrieve_candidates(
    context_items: list[str],
    neighbors: dict[str, list[tuple[str, float]]],
    seen: set[str],
) -> Counter[str]:
    candidate_scores: Counter[str] = Counter()
    for seed in context_items:
        for rank, (cand, sim) in enumerate(neighbors.get(seed, [])):
            if cand in seen:
                continue
            candidate_scores[cand] += sim / (rank + 1)

    if len(candidate_scores) > MAX_CANDIDATES:
        trimmed = Counter()
        for cand, score in candidate_scores.most_common(MAX_CANDIDATES):
            trimmed[cand] = score
        return trimmed
    return candidate_scores


# Build candidate pool when co-occurrence signal is intentionally removed.
def build_non_cooc_candidates(
    playlist_name: str,
    seen: set[str],
    artifacts: TwoStageArtifacts,
) -> Counter[str]:
    candidates: Counter[str] = Counter()
    for rank, item in enumerate(artifacts.popular_items[:MAX_CANDIDATES * 2], start=1):
        if item not in seen:
            candidates[item] += 1.0 / rank

    for token in tokenize(playlist_name):
        for rank, item in enumerate(artifacts.token_to_items.get(token, [])[:200], start=1):
            if item not in seen:
                candidates[item] += 1.0 / rank

    if len(candidates) > MAX_CANDIDATES:
        trimmed = Counter()
        for cand, score in candidates.most_common(MAX_CANDIDATES):
            trimmed[cand] = score
        return trimmed
    return candidates


# Normalize signal weights after removing one or more components.
def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in weights.values())
    if total <= 0:
        return {key: 0.0 for key in weights}
    return {key: max(0.0, value) / total for key, value in weights.items()}


# Generate standard ablation settings expected by the final report.
def build_weight_sets(lastfm_enabled: bool) -> dict[str, dict[str, float]]:
    base = BASE_WEIGHTS.copy()
    base["lastfm"] = 0.10 if lastfm_enabled else 0.0
    if lastfm_enabled:
        base["cooc"] = 0.50
        base["pop"] = 0.15
        base["artist"] = 0.15
        base["name"] = 0.10
    base = normalize_weights(base)

    variants = {
        "Two-Stage Hybrid": base,
    }

    signals = ["cooc", "pop", "artist", "name"]
    if lastfm_enabled:
        signals.append("lastfm")

    for signal in signals:
        variant = base.copy()
        variant[signal] = 0.0
        variants[f"Ablation sin {signal}"] = normalize_weights(variant)

    if lastfm_enabled:
        local_only = base.copy()
        local_only["lastfm"] = 0.0
        variants["Two-Stage sin LastFM"] = normalize_weights(local_only)

    return variants


# Combine retrieval, popularity, artist, name and optional LastFM signals.
def rerank_candidates(
    playlist_name: str,
    context_items: list[str],
    seen: set[str],
    retrieved: Counter[str],
    artifacts: TwoStageArtifacts,
    weights: dict[str, float],
) -> list[str]:
    if not retrieved:
        return recommend_most_popular(artifacts.popular_items, seen)

    playlist_tokens = tokenize(playlist_name)
    seed_artists = {
        artifacts.item_meta[item][0]
        for item in context_items
        if item in artifacts.item_meta
    }

    max_retrieval = max(retrieved.values()) if retrieved else 1.0
    max_pop = max(artifacts.item_counts.values()) if artifacts.item_counts else 1

    final_scores: Counter[str] = Counter()
    for cand, retrieval_score in retrieved.items():
        artist, track = artifacts.item_meta.get(cand, ("", ""))
        cand_tokens = tokenize(f"{artist} {track}")

        s_cooc = retrieval_score / max_retrieval
        s_pop = math.log1p(artifacts.item_counts.get(cand, 0)) / math.log1p(max_pop)
        s_artist = 1.0 if artist in seed_artists else 0.0
        s_name = 1.0 if (playlist_tokens and cand_tokens and playlist_tokens & cand_tokens) else 0.0

        s_lastfm = 0.0
        if weights.get("lastfm", 0.0) > 0 and seed_artists and artist:
            sims = [artifacts.lastfm.artist_similarity(artist, seed_artist) for seed_artist in seed_artists]
            if sims:
                s_lastfm = sum(sims) / len(sims)

        score = (
            weights.get("cooc", 0.0) * s_cooc
            + weights.get("pop", 0.0) * s_pop
            + weights.get("artist", 0.0) * s_artist
            + weights.get("name", 0.0) * s_name
            + weights.get("lastfm", 0.0) * s_lastfm
        )
        final_scores[cand] = score

    ranked = [item for item, _ in final_scores.most_common(TOP_K)]
    used = set(seen) | set(ranked)
    for item in artifacts.popular_items:
        if len(ranked) == TOP_K:
            break
        if item not in used:
            ranked.append(item)
            used.add(item)
    return ranked


# Main APC recommender: retrieve candidates first, then rerank them.
def recommend_two_stage(
    playlist_name: str,
    context_items: list[str],
    artifacts: TwoStageArtifacts,
    weights: dict[str, float],
) -> list[str]:
    seen = set(context_items)
    if weights.get("cooc", 0.0) > 0:
        retrieved = retrieve_candidates(context_items, artifacts.neighbors, seen)
    else:
        retrieved = build_non_cooc_candidates(playlist_name, seen, artifacts)

    if not retrieved:
        return recommend_playlist_name(playlist_name, artifacts.token_to_items, artifacts.popular_items, seen)

    return rerank_candidates(
        playlist_name=playlist_name,
        context_items=context_items,
        seen=seen,
        retrieved=retrieved,
        artifacts=artifacts,
        weights=weights,
    )


# Evaluate all baselines, stronger comparators, and ablations.
def evaluate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    train_playlists, test_items, playlist_names, item_meta = build_split(df)
    log(f"Evaluando {len(test_items):,} playlists")

    train_items = [item for playlist in train_playlists for item in playlist]
    catalog = sorted(set(train_items))
    item_counts_global = Counter(train_items)
    popular_items = [item for item, _ in item_counts_global.most_common()]

    token_item_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for playlist, playlist_name in zip(train_playlists, playlist_names):
        for token in tokenize(playlist_name):
            token_item_counts[token].update(playlist[:80])
    token_to_items = {
        token: [item for item, _ in counter.most_common()]
        for token, counter in token_item_counts.items()
    }

    item_counts, _pair_counts, neighbors = build_cooccurrence(train_playlists)
    transitions = build_markov_transitions(train_playlists)

    lastfm_key = os.getenv("LASTFM_API_KEY") if ENABLE_LASTFM else None
    lastfm = LastFMSimilarity(lastfm_key, max_calls=LASTFM_MAX_CALLS)
    artifacts = TwoStageArtifacts(
        item_counts=item_counts,
        neighbors=neighbors,
        item_meta=item_meta,
        popular_items=popular_items,
        token_to_items=token_to_items,
        lastfm=lastfm,
    )

    rng = random.Random(RANDOM_SEED)
    recommenders: dict[str, callable] = {
        "Random": lambda i: recommend_random(catalog, set(train_playlists[i]), rng),
        "Most Popular": lambda i: recommend_most_popular(popular_items, set(train_playlists[i])),
        "Playlist Name Popular": lambda i: recommend_playlist_name(
            playlist_names[i], token_to_items, popular_items, set(train_playlists[i])
        ),
        "Sequential Markov": lambda i: recommend_markov(
            train_playlists[i], transitions, popular_items, set(train_playlists[i])
        ),
        "Collaborative ItemKNN": lambda i: recommend_item_knn(
            train_playlists[i], neighbors, popular_items, set(train_playlists[i])
        ),
    }

    weight_sets = build_weight_sets(lastfm.enabled)
    for model_name, weights in weight_sets.items():
        recommenders[model_name] = (
            lambda i, w=weights: recommend_two_stage(playlist_names[i], train_playlists[i], artifacts, w)
        )

    target_pops = [item_counts_global.get(target, 0) for target in test_items]
    p33 = percentile(target_pops, 0.33)
    p66 = percentile(target_pops, 0.66)

    rows = []
    examples_rows = []
    segment_rows = []

    total_train_interactions = len(train_items)
    main_model_name = "Two-Stage Hybrid"

    for model_name, recommender in recommenders.items():
        log(f"Evaluando modelo: {model_name}")
        metrics = defaultdict(float)
        unique_recommended = set()
        segment_stats: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for i, relevant in enumerate(test_items):
            recs = recommender(i)
            recs = recs[:TOP_K]
            unique_recommended.update(recs)

            hr = hit_rate_at_k(recs, relevant, TOP_K)
            p10 = precision_at_k(recs, relevant, TOP_K)
            ap10 = average_precision_at_k(recs, relevant, TOP_K)
            ndcg10 = ndcg_at_k(recs, relevant, TOP_K)
            ild10 = artist_diversity_at_k(recs, item_meta, TOP_K)
            nov10 = novelty_at_k(recs, item_counts_global, total_train_interactions, TOP_K)

            metrics["HitRate@10"] += hr
            metrics["Precision@10"] += p10
            metrics["MAP@10"] += ap10
            metrics["nDCG@10"] += ndcg10
            metrics["ILD@10"] += ild10
            metrics["Novelty@10"] += nov10

            len_bucket = playlist_size_bucket(len(train_playlists[i]))
            pop_bucket = target_pop_bucket(item_counts_global.get(relevant, 0), p33, p66)
            key = (len_bucket, pop_bucket)
            segment_stats[key]["count"] += 1
            segment_stats[key]["HitRate@10"] += hr
            segment_stats[key]["MAP@10"] += ap10

            if model_name == main_model_name and len(examples_rows) < 20:
                examples_rows.append(
                    {
                        "playlist_index": i,
                        "playlist_name": playlist_names[i],
                        "profile": f"size={len_bucket}; target_pop={pop_bucket}",
                        "context_preview": " | ".join(train_playlists[i][:5]),
                        "target": relevant,
                        "recs_top10": " | ".join(recs),
                        "hit@10": int(hr > 0),
                    }
                )

        n_eval = len(test_items)
        row = {
            "Modelo": model_name,
            "HitRate@10": metrics["HitRate@10"] / n_eval,
            "Precision@10": metrics["Precision@10"] / n_eval,
            "MAP@10": metrics["MAP@10"] / n_eval,
            "nDCG@10": metrics["nDCG@10"] / n_eval,
            "ILD@10": metrics["ILD@10"] / n_eval,
            "Novelty@10": metrics["Novelty@10"] / n_eval,
            "CatalogCoverage@10": len(unique_recommended) / max(1, len(catalog)),
        }
        rows.append(row)

        if model_name == main_model_name:
            for (len_bucket, pop_bucket), values in sorted(segment_stats.items()):
                count = int(values["count"])
                if count == 0:
                    continue
                segment_rows.append(
                    {
                        "modelo": model_name,
                        "playlist_size_bucket": len_bucket,
                        "target_pop_bucket": pop_bucket,
                        "n": count,
                        "HitRate@10": values["HitRate@10"] / count,
                        "MAP@10": values["MAP@10"] / count,
                    }
                )

    eval_stats = {
        "eval_playlists": len(test_items),
        "catalog_train_items": len(catalog),
        "lastfm_enabled": lastfm.enabled,
        "lastfm_calls": lastfm.calls,
        "lastfm_call_budget": LASTFM_MAX_CALLS if lastfm.enabled else 0,
    }

    return pd.DataFrame(rows), pd.DataFrame(examples_rows), pd.DataFrame(segment_rows), eval_stats


# Persist result tables for quantitative + qualitative final-report evidence.
def write_report(
    results: pd.DataFrame,
    examples: pd.DataFrame,
    segments: pd.DataFrame,
    eval_stats: dict[str, object],
) -> None:
    results = results.sort_values("MAP@10", ascending=False).reset_index(drop=True)
    results.to_csv(RESULT_CSV, index=False)
    examples.to_csv(EXAMPLES_CSV, index=False)
    segments.to_csv(SEGMENTS_CSV, index=False)

    metrics_lines = [
        "| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 | ILD@10 | Novelty@10 | CatalogCoverage@10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in results.to_dict(orient="records"):
        metrics_lines.append(
            "| {Modelo} | {HitRate@10:.4f} | {Precision@10:.4f} | {MAP@10:.4f} | {nDCG@10:.4f} | {ILD@10:.4f} | {Novelty@10:.4f} | {CatalogCoverage@10:.4f} |".format(
                **row
            )
        )

    report = f"""# Resultados Finales APC - Spotify

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: {TOP_K}
- Playlists evaluadas: {eval_stats['eval_playlists']:,}
- Catalogo train: {eval_stats['catalog_train_items']:,} items
- LastFM activo: {eval_stats['lastfm_enabled']}
- LastFM llamadas usadas: {eval_stats['lastfm_calls']} / {eval_stats['lastfm_call_budget']}

## Modelos comparados

- Baselines: Random, Most Popular, Playlist Name Popular.
- Comparadores mas fuertes: Sequential Markov, Collaborative ItemKNN.
- Metodo principal y ablations: Two-Stage Hybrid + variantes sin cada senal.

## Resultados

{chr(10).join(metrics_lines)}

## Archivos para paper/poster

- Tabla principal: {RESULT_CSV}
- Ejemplos cualitativos (recomendaciones y perfiles): {EXAMPLES_CSV}
- Analisis por segmentos (tamano playlist x popularidad objetivo): {SEGMENTS_CSV}
"""
    RESULT_MD.write_text(report, encoding="utf-8")


# Entry point that runs sampling, evaluation and artifact generation end to end.
def main() -> None:
    start = time.time()
    log(
        "Configuracion -> "
        f"sample_percent={SAMPLE_PERCENT}, "
        f"max_sample_playlists={MAX_SAMPLE_PLAYLISTS}, "
        f"max_eval_playlists={MAX_EVAL_PLAYLISTS}, "
        f"output_prefix={OUTPUT_PREFIX}, "
        f"enable_lastfm={ENABLE_LASTFM}, "
        f"lastfm_max_calls={LASTFM_MAX_CALLS}"
    )
    con = duckdb.connect()
    df = load_playlist_sample(con)
    results, examples, segments, eval_stats = evaluate(df)
    write_report(results, examples, segments, eval_stats)

    print("\nResultados APC:")
    print(results.to_string(index=False))
    print(f"\nReporte escrito en {RESULT_MD}")
    print(f"Ejemplos escritos en {EXAMPLES_CSV}")
    print(f"Segmentos escritos en {SEGMENTS_CSV}")
    print(f"Tiempo total: {time.time() - start:.2f} segundos")


if __name__ == "__main__":
    main()
