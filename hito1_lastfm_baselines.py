from __future__ import annotations

import math
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/Last.fm_data.csv")
REPORT_PATH = Path("resultados_hito1_lastfm.md")
TOP_K = 10
RANDOM_SEED = 42


def precision_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    if not recommended:
        return 0.0
    return sum(item in relevant for item in recommended[:k]) / k


def hit_rate_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    return float(any(item in relevant for item in recommended[:k]))


def average_precision_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    score = 0.0
    hits = 0
    for rank, item in enumerate(recommended[:k], start=1):
        if item in relevant:
            hits += 1
            score += hits / rank
    return score / min(len(relevant), k)


def ndcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    dcg = 0.0
    for rank, item in enumerate(recommended[:k], start=1):
        if item in relevant:
            dcg += 1.0 / math.log2(rank + 1)
    ideal_hits = min(len(relevant), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Username": "user_id",
            "Artist": "artist_name",
            "Track": "track_name",
            "Album": "album_name",
        }
    )
    df["item_id"] = df["artist_name"].astype(str) + " - " + df["track_name"].astype(str)
    df["timestamp"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        format="%d %b %Y %H:%M",
        errors="coerce",
    )
    return df.sort_values(["user_id", "timestamp"])


def temporal_split(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple[pd.DataFrame, dict[str, set[str]]]:
    train_parts = []
    test_relevant: dict[str, set[str]] = {}

    for user_id, user_df in df.groupby("user_id", sort=False):
        split_idx = max(1, int(len(user_df) * train_ratio))
        train_user = user_df.iloc[:split_idx]
        test_user = user_df.iloc[split_idx:]
        seen_train = set(train_user["item_id"])
        future_unseen = set(test_user["item_id"]) - seen_train
        if future_unseen:
            train_parts.append(train_user)
            test_relevant[user_id] = future_unseen

    return pd.concat(train_parts, ignore_index=True), test_relevant


def recommend_random(catalog: list[str], seen: set[str], k: int, rng: random.Random) -> list[str]:
    candidates = [item for item in catalog if item not in seen]
    if len(candidates) <= k:
        return candidates
    return rng.sample(candidates, k)


def recommend_most_popular(popular_items: list[str], seen: set[str], k: int) -> list[str]:
    return [item for item in popular_items if item not in seen][:k]


def recommend_favorite_artist(
    user_artist_counts: pd.Series,
    artist_popular_items: dict[str, list[str]],
    popular_items: list[str],
    seen: set[str],
    k: int,
) -> list[str]:
    recommendations: list[str] = []
    used = set(seen)

    for artist in user_artist_counts.index:
        for item in artist_popular_items.get(artist, []):
            if item not in used:
                recommendations.append(item)
                used.add(item)
                if len(recommendations) == k:
                    return recommendations

    for item in popular_items:
        if item not in used:
            recommendations.append(item)
            used.add(item)
            if len(recommendations) == k:
                break

    return recommendations


def evaluate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    train_df, test_relevant = temporal_split(df)
    users = sorted(test_relevant)
    rng = random.Random(RANDOM_SEED)

    user_seen = train_df.groupby("user_id")["item_id"].apply(set).to_dict()
    popular_items = train_df["item_id"].value_counts().index.tolist()
    catalog = sorted(train_df["item_id"].unique())

    artist_popular_items: dict[str, list[str]] = {}
    for artist, artist_df in train_df.groupby("artist_name"):
        artist_popular_items[artist] = artist_df["item_id"].value_counts().index.tolist()

    user_artist_profile = {
        user_id: user_df["artist_name"].value_counts()
        for user_id, user_df in train_df.groupby("user_id")
    }

    rows = []
    recommenders = {
        "Random": lambda user: recommend_random(catalog, user_seen[user], TOP_K, rng),
        "Most Popular": lambda user: recommend_most_popular(popular_items, user_seen[user], TOP_K),
        "Favorite Artist Popular": lambda user: recommend_favorite_artist(
            user_artist_profile[user],
            artist_popular_items,
            popular_items,
            user_seen[user],
            TOP_K,
        ),
    }

    for name, recommender in recommenders.items():
        metrics = defaultdict(float)
        for user in users:
            relevant = test_relevant[user]
            recs = recommender(user)
            metrics["HitRate@10"] += hit_rate_at_k(recs, relevant, TOP_K)
            metrics["Precision@10"] += precision_at_k(recs, relevant, TOP_K)
            metrics["MAP@10"] += average_precision_at_k(recs, relevant, TOP_K)
            metrics["nDCG@10"] += ndcg_at_k(recs, relevant, TOP_K)

        rows.append(
            {
                "model": name,
                **{metric: value / len(users) for metric, value in metrics.items()},
            }
        )

    stats = {
        "rows": len(df),
        "users": df["user_id"].nunique(),
        "artists": df["artist_name"].nunique(),
        "tracks": df["track_name"].nunique(),
        "items": df["item_id"].nunique(),
        "albums": df["album_name"].nunique(),
        "duplicates": int(df.duplicated().sum()),
        "missing_albums": int(df["album_name"].isna().sum()),
        "date_min": df["timestamp"].min(),
        "date_max": df["timestamp"].max(),
        "sparsity": 1
        - len(df.drop_duplicates(["user_id", "item_id"]))
        / (df["user_id"].nunique() * df["item_id"].nunique()),
        "train_rows": len(train_df),
        "eval_users": len(users),
        "avg_test_relevant": sum(len(v) for v in test_relevant.values()) / len(users),
    }

    return pd.DataFrame(rows), stats


def write_report(results: pd.DataFrame, stats: dict[str, object]) -> None:
    metric_columns = ["model", "HitRate@10", "Precision@10", "MAP@10", "nDCG@10"]
    table_lines = [
        "| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in results[metric_columns].itertuples(index=False):
        table_lines.append(
            f"| {row.model} | {row._1:.4f} | {row._2:.4f} | {row._3:.4f} | {row._4:.4f} |"
        )
    metrics_md = "\n".join(table_lines)
    report = f"""# Resultados preliminares Hito 1 - Last.fm

## Dataset

- Registros: {stats["rows"]:,}
- Usuarios: {stats["users"]:,}
- Artistas: {stats["artists"]:,}
- Tracks unicos por nombre: {stats["tracks"]:,}
- Items unicos artista-track: {stats["items"]:,}
- Albumes: {stats["albums"]:,}
- Duplicados exactos: {stats["duplicates"]:,}
- Albumes faltantes: {stats["missing_albums"]:,}
- Rango temporal: {stats["date_min"]} a {stats["date_max"]}
- Sparsity usuario-item: {stats["sparsity"]:.4f}

## Evaluacion

Se uso split temporal por usuario con 80% de interacciones para train y 20% para test. Para evaluar recomendacion de descubrimiento, los items relevantes del test son canciones futuras que el usuario no habia escuchado en train.

- Filas de train: {stats["train_rows"]:,}
- Usuarios evaluados: {stats["eval_users"]:,}
- Items relevantes promedio por usuario: {stats["avg_test_relevant"]:.2f}

## Baselines

{metrics_md}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    df = load_data(DATA_PATH)
    results, stats = evaluate(df)
    write_report(results, stats)

    print("Dataset:")
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("\nBaselines:")
    print(results.to_string(index=False))
    print(f"\nReporte escrito en {REPORT_PATH}")


if __name__ == "__main__":
    main()
