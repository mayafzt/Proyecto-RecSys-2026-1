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
RESULT_CSV = Path("resultados_hito2_midterm.csv")
RESULT_MD = Path("resultados_hito2_midterm.md")

SAMPLE_PERCENT = int(os.getenv("MIDTERM_SAMPLE_PERCENT", "12"))
TOP_K = 10
RANDOM_SEED = 42
MAX_EVAL_PLAYLISTS = int(os.getenv("MIDTERM_MAX_EVAL_PLAYLISTS", "20000"))

# Retrieval + reranking configuration.
MAX_ITEMS_PER_PLAYLIST_FOR_COOC = 80
MAX_NEIGHBORS_PER_SEED = 150
MAX_CANDIDATES = 400

# Midterm main method weights.
W_COOC = 0.55
W_POP = 0.15
W_ARTIST = 0.10
W_NAME = 0.10
W_LASTFM = 0.10


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


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


def hit_rate_at_k(recommended: list[str], relevant: str, k: int) -> float:
    return float(relevant in recommended[:k])


def precision_at_k(recommended: list[str], relevant: str, k: int) -> float:
    return float(relevant in recommended[:k]) / k


def average_precision_at_k(recommended: list[str], relevant: str, k: int) -> float:
    for rank, item in enumerate(recommended[:k], start=1):
        if item == relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(recommended: list[str], relevant: str, k: int) -> float:
    for rank, item in enumerate(recommended[:k], start=1):
        if item == relevant:
            return 1.0 / math.log2(rank + 1)
    return 0.0


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


def load_playlist_sample(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    log(f"Cargando muestra deterministica del {SAMPLE_PERCENT}% por playlist")
    query = f"""
    WITH data AS (
      SELECT
        user_id,
        artistname,
        trackname,
        playlistname,
        lower(trim(artistname)) || ' - ' || lower(trim(trackname)) AS item_id,
        lower(trim(artistname)) AS artist_norm,
        lower(trim(trackname)) AS track_norm,
        user_id || '||' || playlistname AS playlist_id
      FROM {base_relation()}
      WHERE user_id IS NOT NULL
        AND artistname IS NOT NULL
        AND trackname IS NOT NULL
        AND playlistname IS NOT NULL
    )
    SELECT *
    FROM data
    WHERE hash(playlist_id) % 100 < {SAMPLE_PERCENT}
    """
    return con.execute(query).fetchdf()


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


def recommend_most_popular(popular_items: list[str], seen: set[str]) -> list[str]:
    recommendations = []
    for item in popular_items:
        if item not in seen:
            recommendations.append(item)
            if len(recommendations) == TOP_K:
                break
    return recommendations


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


class LastFMSimilarity:
    def __init__(self, api_key: str | None, timeout_s: int = 3) -> None:
        self.api_key = api_key or ""
        self.timeout_s = timeout_s
        self.cache: dict[tuple[str, str], float] = {}
        self.enabled = bool(self.api_key)

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

        url = (
            "https://ws.audioscrobbler.com/2.0/?method=artist.getsimilar"
            f"&artist={parse.quote(left)}"
            f"&api_key={self.api_key}"
            "&format=json&limit=100"
        )

        try:
            with request.urlopen(url, timeout=self.timeout_s) as response:
                payload = response.read().decode("utf-8", errors="ignore")
            # Light JSON parsing without external dependency.
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


def rerank_candidates(
    playlist_name: str,
    context_items: list[str],
    seen: set[str],
    retrieved: Counter[str],
    artifacts: TwoStageArtifacts,
    use_lastfm: bool,
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
        if use_lastfm and seed_artists and artist:
            sims = [artifacts.lastfm.artist_similarity(artist, seed_artist) for seed_artist in seed_artists]
            if sims:
                s_lastfm = sum(sims) / len(sims)

        score = (
            W_COOC * s_cooc
            + W_POP * s_pop
            + W_ARTIST * s_artist
            + W_NAME * s_name
            + W_LASTFM * s_lastfm
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


def recommend_two_stage(
    playlist_name: str,
    context_items: list[str],
    artifacts: TwoStageArtifacts,
    use_lastfm: bool,
) -> list[str]:
    seen = set(context_items)
    retrieved = retrieve_candidates(context_items, artifacts.neighbors, seen)
    if not retrieved:
        # Backoff to name-based prior if co-occurrence is sparse.
        return recommend_playlist_name(playlist_name, artifacts.token_to_items, artifacts.popular_items, seen)
    return rerank_candidates(
        playlist_name=playlist_name,
        context_items=context_items,
        seen=seen,
        retrieved=retrieved,
        artifacts=artifacts,
        use_lastfm=use_lastfm,
    )


def evaluate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    train_playlists, test_items, playlist_names, item_meta = build_split(df)
    log(f"Evaluando {len(test_items):,} playlists")

    train_items = [item for playlist in train_playlists for item in playlist]
    catalog = sorted(set(train_items))
    popular_items = [item for item, _ in Counter(train_items).most_common()]

    token_item_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for playlist, playlist_name in zip(train_playlists, playlist_names):
        for token in tokenize(playlist_name):
            token_item_counts[token].update(playlist[:80])
    token_to_items = {
        token: [item for item, _ in counter.most_common()]
        for token, counter in token_item_counts.items()
    }

    item_counts, _pair_counts, neighbors = build_cooccurrence(train_playlists)
    lastfm = LastFMSimilarity(os.getenv("LASTFM_API_KEY"))
    artifacts = TwoStageArtifacts(
        item_counts=item_counts,
        neighbors=neighbors,
        item_meta=item_meta,
        popular_items=popular_items,
        token_to_items=token_to_items,
        lastfm=lastfm,
    )

    rng = random.Random(RANDOM_SEED)
    recommenders = {
        "Random": lambda i: recommend_random(catalog, set(train_playlists[i]), rng),
        "Most Popular": lambda i: recommend_most_popular(popular_items, set(train_playlists[i])),
        "Playlist Name Popular": lambda i: recommend_playlist_name(
            playlist_names[i], token_to_items, popular_items, set(train_playlists[i])
        ),
        "Two-Stage Cooc+Rerank": lambda i: recommend_two_stage(
            playlist_names[i], train_playlists[i], artifacts, use_lastfm=False
        ),
        "Two-Stage + LastFM": lambda i: recommend_two_stage(
            playlist_names[i], train_playlists[i], artifacts, use_lastfm=True
        ),
    }

    rows = []
    for model_name, recommender in recommenders.items():
        log(f"Evaluando modelo: {model_name}")
        metrics = defaultdict(float)
        for i, relevant in enumerate(test_items):
            recs = recommender(i)
            metrics["HitRate@10"] += hit_rate_at_k(recs, relevant, TOP_K)
            metrics["Precision@10"] += precision_at_k(recs, relevant, TOP_K)
            metrics["MAP@10"] += average_precision_at_k(recs, relevant, TOP_K)
            metrics["nDCG@10"] += ndcg_at_k(recs, relevant, TOP_K)
        rows.append({"Modelo": model_name, **{k: v / len(test_items) for k, v in metrics.items()}})

    eval_stats = {
        "eval_playlists": len(test_items),
        "catalog_train_items": len(catalog),
        "lastfm_enabled": lastfm.enabled,
    }
    return pd.DataFrame(rows), eval_stats


def write_report(results: pd.DataFrame, eval_stats: dict[str, object]) -> None:
    results.to_csv(RESULT_CSV, index=False)

    metrics_lines = [
        "| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in results.itertuples(index=False):
        metrics_lines.append(
            f"| {row.Modelo} | {row._1:.4f} | {row._2:.4f} | {row._3:.4f} | {row._4:.4f} |"
        )

    report = f"""# Resultados Midterm Hito 2 - Spotify + LastFM

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: {TOP_K}
- Playlists evaluadas: {eval_stats['eval_playlists']:,}
- Catalogo train: {eval_stats['catalog_train_items']:,} items
- LastFM activo (API key en entorno): {eval_stats['lastfm_enabled']}

## Modelos comparados

- Random
- Most Popular
- Playlist Name Popular
- Two-Stage Cooc+Rerank
- Two-Stage + LastFM

## Resultados

{chr(10).join(metrics_lines)}
"""
    RESULT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    start = time.time()
    con = duckdb.connect()
    df = load_playlist_sample(con)
    results, eval_stats = evaluate(df)
    write_report(results, eval_stats)

    print("\nResultados Midterm:")
    print(results.to_string(index=False))
    print(f"\nReporte escrito en {RESULT_MD}")
    print(f"Tiempo total: {time.time() - start:.2f} segundos")


if __name__ == "__main__":
    main()
