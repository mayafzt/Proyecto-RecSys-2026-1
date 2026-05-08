from __future__ import annotations

import math
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = Path("data/spotify_dataset.csv")
REPORT_MD = Path("resultados_hito1_spotify.md")
REPORT_CSV = Path("resultados_hito1_spotify.csv")
FIG_DIR = Path("figures")

SAMPLE_PERCENT = 30
TOP_K = 10
RANDOM_SEED = 42


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    stop = {"the", "and", "for", "con", "las", "los", "una", "de", "la", "el", "in", "to", "of", "my"}
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


def full_dataset_stats(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    log("Calculando estadisticas globales del CSV completo")
    query = f"""
    WITH data AS (
      SELECT
        user_id,
        artistname,
        trackname,
        playlistname,
        artistname || ' - ' || trackname AS item_id,
        user_id || '||' || playlistname AS playlist_id
      FROM {base_relation()}
      WHERE user_id IS NOT NULL
        AND artistname IS NOT NULL
        AND trackname IS NOT NULL
        AND playlistname IS NOT NULL
    )
    SELECT
      count(*) AS rows,
      count(DISTINCT user_id) AS users,
      count(DISTINCT artistname) AS artists,
      count(DISTINCT trackname) AS tracks,
      count(DISTINCT item_id) AS items,
      count(DISTINCT playlist_id) AS playlists
    FROM data
    """
    row = con.execute(query).fetchone()
    keys = ["rows", "users", "artists", "tracks", "items", "playlists"]
    return dict(zip(keys, row))


def load_playlist_sample(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    log(f"Cargando muestra deterministica del {SAMPLE_PERCENT}% por playlist")
    query = f"""
    WITH data AS (
      SELECT
        user_id,
        artistname,
        trackname,
        playlistname,
        artistname || ' - ' || trackname AS item_id,
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


def describe_sample(df: pd.DataFrame) -> dict[str, object]:
    log("Calculando estadisticas descriptivas de la muestra")
    playlist_sizes = df.groupby("playlist_id").size()
    return {
        "rows": len(df),
        "users": df["user_id"].nunique(),
        "artists": df["artistname"].nunique(),
        "tracks": df["trackname"].nunique(),
        "items": df["item_id"].nunique(),
        "playlists": df["playlist_id"].nunique(),
        "playlist_sizes": playlist_sizes,
        "item_counts": df["item_id"].value_counts(),
        "artist_counts": df["artistname"].value_counts(),
    }


def build_split(df: pd.DataFrame) -> tuple[list[list[str]], list[str], list[str]]:
    log("Construyendo split leave-last-out por playlist")
    grouped = df.groupby("playlist_id", sort=False).agg(
        item_id=("item_id", list),
        playlistname=("playlistname", "first"),
    )
    grouped["size"] = grouped["item_id"].str.len()
    grouped = grouped[grouped["size"] >= 3]

    train_playlists = [items[:-1] for items in grouped["item_id"]]
    test_items = [items[-1] for items in grouped["item_id"]]
    playlist_names = grouped["playlistname"].astype(str).tolist()
    return train_playlists, test_items, playlist_names


def recommend_random(catalog: list[str], seen: set[str], rng: random.Random) -> list[str]:
    recommendations: list[str] = []
    used = set(seen)
    max_attempts = TOP_K * 100
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
        for rank, item in enumerate(token_to_items.get(token, [])[:100]):
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


def evaluate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    train_playlists, test_items, playlist_names = build_split(df)
    log(f"Evaluando {len(test_items):,} playlists")

    train_items = [item for playlist in train_playlists for item in playlist]
    catalog = sorted(set(train_items))
    popular_items = [item for item, _ in Counter(train_items).most_common()]

    log("Construyendo indice texto playlist -> canciones populares")
    token_item_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for playlist, playlist_name in zip(train_playlists, playlist_names):
        for token in tokenize(playlist_name):
            token_item_counts[token].update(playlist[:80])
    token_to_items = {
        token: [item for item, _ in counter.most_common()]
        for token, counter in token_item_counts.items()
    }

    rng = random.Random(RANDOM_SEED)
    recommenders = {
        "Random": lambda i, seen: recommend_random(catalog, seen, rng),
        "Most Popular": lambda i, seen: recommend_most_popular(popular_items, seen),
        "Playlist Name Popular": lambda i, seen: recommend_playlist_name(
            playlist_names[i], token_to_items, popular_items, seen
        ),
    }

    rows = []
    for model_name, recommender in recommenders.items():
        log(f"Evaluando baseline: {model_name}")
        metrics = defaultdict(float)
        for i, relevant in enumerate(test_items):
            seen = set(train_playlists[i])
            recs = recommender(i, seen)
            metrics["HitRate@10"] += hit_rate_at_k(recs, relevant, TOP_K)
            metrics["Precision@10"] += precision_at_k(recs, relevant, TOP_K)
            metrics["MAP@10"] += average_precision_at_k(recs, relevant, TOP_K)
            metrics["nDCG@10"] += ndcg_at_k(recs, relevant, TOP_K)
        rows.append({"Modelo": model_name, **{k: v / len(test_items) for k, v in metrics.items()}})

    eval_stats = {
        "eval_playlists": len(test_items),
        "catalog_train_items": len(catalog),
    }
    return pd.DataFrame(rows), eval_stats


def make_figures(sample_stats: dict[str, object], results: pd.DataFrame) -> None:
    log("Generando figuras")
    FIG_DIR.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    playlist_sizes: pd.Series = sample_stats["playlist_sizes"]  # type: ignore[assignment]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    playlist_sizes[playlist_sizes <= playlist_sizes.quantile(0.99)].plot(kind="hist", bins=50, ax=ax, color="#3b6ea8")
    ax.set_title("Distribucion de canciones por playlist", fontsize=13, weight="bold")
    ax.set_xlabel("Canciones por playlist")
    ax.set_ylabel("Numero de playlists")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "spotify_tamano_playlists.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    artist_counts: pd.Series = sample_stats["artist_counts"]  # type: ignore[assignment]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    artist_counts.head(10).sort_values().plot(kind="barh", ax=ax, color="#4f8f59", edgecolor="white")
    ax.set_title("Top 10 artistas por apariciones en playlists", fontsize=13, weight="bold")
    ax.set_xlabel("Apariciones")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "spotify_top_artistas.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    item_counts: pd.Series = sample_stats["item_counts"]  # type: ignore[assignment]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.plot(range(1, len(item_counts) + 1), item_counts.values, color="#d55e00", linewidth=1.3)
    ax.set_title("Distribucion de popularidad de canciones", fontsize=13, weight="bold")
    ax.set_xlabel("Canciones ordenadas por popularidad")
    ax.set_ylabel("Apariciones")
    ax.set_xscale("log")
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "spotify_distribucion_popularidad.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    results.set_index("Modelo").plot(kind="bar", ax=ax, color=["#4c78a8", "#f58518", "#54a24b", "#e45756"])
    ax.set_title("Comparacion de baselines en top-10", fontsize=13, weight="bold")
    ax.set_xlabel("Modelo")
    ax.set_ylabel("Valor de metrica")
    ax.tick_params(axis="x", labelrotation=0)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "spotify_metricas_baselines.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_report(
    full_stats: dict[str, int],
    sample_stats: dict[str, object],
    eval_stats: dict[str, object],
    results: pd.DataFrame,
) -> None:
    log("Escribiendo reportes")
    results.to_csv(REPORT_CSV, index=False)
    metrics_lines = [
        "| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in results.itertuples(index=False):
        metrics_lines.append(
            f"| {row.Modelo} | {row._1:.4f} | {row._2:.4f} | {row._3:.4f} | {row._4:.4f} |"
        )

    playlist_sizes: pd.Series = sample_stats["playlist_sizes"]  # type: ignore[assignment]
    report = f"""# Resultados preliminares Hito 1 - Spotify Playlists

## Dataset completo

- Registros: {full_stats["rows"]:,}
- Usuarios: {full_stats["users"]:,}
- Artistas: {full_stats["artists"]:,}
- Tracks por nombre: {full_stats["tracks"]:,}
- Items artista-track: {full_stats["items"]:,}
- Playlists usuario-nombre: {full_stats["playlists"]:,}

## Muestra utilizada

Para este Hito 1 se uso una muestra deterministica del {SAMPLE_PERCENT}% de las playlists, preservando playlists completas mediante hashing de `user_id` y `playlistname`. Esto reduce el costo computacional sobre un CSV de 1.18 GB, mantiene reproducibilidad y es suficiente para el objetivo del hito: exploracion preliminar e implementacion de baselines.

- Registros en muestra: {sample_stats["rows"]:,}
- Usuarios en muestra: {sample_stats["users"]:,}
- Playlists en muestra: {sample_stats["playlists"]:,}
- Items artista-track en muestra: {sample_stats["items"]:,}
- Mediana de canciones por playlist: {playlist_sizes.median():.1f}
- Promedio de canciones por playlist: {playlist_sizes.mean():.2f}

## Evaluacion

Para cada playlist con al menos 3 canciones, se oculto la ultima cancion como test y se entreno con el resto.

- Playlists evaluadas: {eval_stats["eval_playlists"]:,}
- Catalogo de entrenamiento: {eval_stats["catalog_train_items"]:,} items

## Baselines

{chr(10).join(metrics_lines)}
"""
    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    start = time.time()
    con = duckdb.connect()
    full_stats = full_dataset_stats(con)
    df = load_playlist_sample(con)
    sample_stats = describe_sample(df)
    results, eval_stats = evaluate(df)
    make_figures(sample_stats, results)
    write_report(full_stats, sample_stats, eval_stats, results)

    print("\nDataset completo:")
    for key, value in full_stats.items():
        print(f"{key}: {value}")
    print("\nMuestra:")
    for key in ["rows", "users", "artists", "tracks", "items", "playlists"]:
        print(f"{key}: {sample_stats[key]}")
    print("\nEvaluacion:")
    for key, value in eval_stats.items():
        print(f"{key}: {value}")
    print("\nBaselines:")
    print(results.to_string(index=False))
    print(f"\nReporte escrito en {REPORT_MD}")
    print(f"Tiempo total: {time.time() - start:.2f} segundos")


if __name__ == "__main__":
    main()
