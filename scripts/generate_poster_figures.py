from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "poster_assets" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="talk")
PALETTE = {
    "Two-Stage Hybrid": "#0039A6",
    "Sequential Markov": "#C99700",
    "Collaborative ItemKNN": "#2E7D32",
    "Ablation sin cooc": "#C62828",
    "Ablation sin artist": "#6C757D",
    "Ablation sin name": "#7F8C8D",
    "Ablation sin pop": "#95A5A6",
    "Playlist Name Popular": "#B0B7C3",
    "Most Popular": "#D3D8E2",
    "Random": "#E5E9F2",
}


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_main_benchmark(df: pd.DataFrame) -> None:
    models = ["Sequential Markov", "Two-Stage Hybrid", "Collaborative ItemKNN", "Playlist Name Popular"]
    data = df[df["Modelo"].isin(models)].copy()
    melted = data.melt(
        id_vars=["Modelo"],
        value_vars=["HitRate@10", "MAP@10", "CatalogCoverage@10"],
        var_name="Metric",
        value_name="Score",
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=melted, x="Modelo", y="Score", hue="Metric", ax=ax, palette="Set2")
    ax.set_title("Main Benchmark (30% Full Run)")
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.tick_params(axis="x", rotation=15)
    save(fig, "fig_main_benchmark.png")


def fig_beyond_accuracy(df: pd.DataFrame) -> None:
    models = ["Sequential Markov", "Two-Stage Hybrid", "Collaborative ItemKNN"]
    data = df[df["Modelo"].isin(models)].copy()
    melted = data.melt(
        id_vars=["Modelo"],
        value_vars=["ILD@10", "Novelty@10", "nDCG@10"],
        var_name="Metric",
        value_name="Score",
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=melted, x="Modelo", y="Score", hue="Metric", ax=ax, palette="viridis")
    ax.set_title("Beyond-Accuracy Trade-off")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=15)
    save(fig, "fig_beyond_accuracy.png")


def fig_ablation(df: pd.DataFrame) -> None:
    hybrid_map = float(df.loc[df["Modelo"] == "Two-Stage Hybrid", "MAP@10"].iloc[0])
    ab_models = ["Ablation sin cooc", "Ablation sin artist", "Ablation sin name", "Ablation sin pop"]
    ab = df[df["Modelo"].isin(ab_models)].copy()
    ab["MAP_drop_pp"] = (hybrid_map - ab["MAP@10"]) * 100
    ab = ab.sort_values("MAP_drop_pp", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=ab, y="Modelo", x="MAP_drop_pp", ax=ax, palette="Reds_r")
    ax.set_title("Ablation Impact: MAP@10 Drop vs Two-Stage")
    ax.set_xlabel("Drop (percentage points)")
    ax.set_ylabel("")
    for i, v in enumerate(ab["MAP_drop_pp"]):
        ax.text(v + 0.03, i, f"{v:.2f} pp", va="center", fontsize=10)
    save(fig, "fig_ablation_map_drop.png")


def fig_segment_heatmap(df_seg: pd.DataFrame) -> None:
    pivot = df_seg.pivot(index="playlist_size_bucket", columns="target_pop_bucket", values="HitRate@10")
    order_rows = [r for r in ["short", "medium", "long"] if r in pivot.index]
    order_cols = [c for c in ["head", "mid", "tail"] if c in pivot.columns]
    pivot = pivot.loc[order_rows, order_cols]
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".3f",
        cmap="YlGnBu",
        cbar_kws={"label": "HitRate@10"},
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Segment Analysis (Two-Stage): HitRate@10")
    ax.set_xlabel("Target popularity bucket")
    ax.set_ylabel("Playlist size bucket")
    save(fig, "fig_segment_heatmap.png")


def fig_sensitivity(df30: pd.DataFrame, df20: pd.DataFrame) -> None:
    models = ["Sequential Markov", "Two-Stage Hybrid", "Collaborative ItemKNN"]
    d30 = df30[df30["Modelo"].isin(models)][["Modelo", "HitRate@10", "MAP@10"]].copy()
    d30["Run"] = "30% full"
    d20 = df20[df20["Modelo"].isin(models)][["Modelo", "HitRate@10", "MAP@10"]].copy()
    d20["Run"] = "20% sensitivity"
    data = pd.concat([d30, d20], ignore_index=True)
    melted = data.melt(id_vars=["Modelo", "Run"], value_vars=["HitRate@10", "MAP@10"], var_name="Metric", value_name="Score")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=melted, x="Modelo", y="Score", hue="Run", ax=ax)
    ax.set_title("Robustness Across Runs")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=15)
    save(fig, "fig_sensitivity_comparison.png")


def main() -> None:
    df30 = pd.read_csv(ROOT / "resultados_hito2_final_30_full.csv")
    df20 = pd.read_csv(ROOT / "resultados_hito2_final_20_sens.csv")
    seg = pd.read_csv(ROOT / "resultados_hito2_final_30_full_segmentos.csv")

    fig_main_benchmark(df30)
    fig_beyond_accuracy(df30)
    fig_ablation(df30)
    fig_segment_heatmap(seg)
    fig_sensitivity(df30, df20)

    print(f"Generated figures in {OUT}")


if __name__ == "__main__":
    main()
