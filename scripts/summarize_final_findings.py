from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FULL = ROOT / "resultados_hito2_final_30_full.csv"
SENS = ROOT / "resultados_hito2_final_20_sens.csv"
SEG = ROOT / "resultados_hito2_final_30_full_segmentos.csv"
EX = ROOT / "resultados_hito2_final_30_full_ejemplos.csv"
OUT = ROOT / "HALLAZGOS_FINALES_POSTER_PAPER.md"


def read_table(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_model(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {r["Modelo"]: r for r in rows}


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def delta(a: float, b: float) -> str:
    sign = "+" if a - b >= 0 else ""
    return f"{sign}{(a - b) * 100:.2f} pp"


def main() -> None:
    full_rows = read_table(FULL)
    sens_rows = read_table(SENS)
    seg_rows = read_table(SEG)
    ex_rows = read_table(EX)

    full_m = by_model(full_rows)
    sens_m = by_model(sens_rows)

    hybrid = full_m["Two-Stage Hybrid"]
    markov = full_m["Sequential Markov"]
    iknn = full_m["Collaborative ItemKNN"]

    abl_pop = full_m["Ablation sin pop"]
    abl_name = full_m["Ablation sin name"]
    abl_artist = full_m["Ablation sin artist"]
    abl_cooc = full_m["Ablation sin cooc"]

    # Segment summaries.
    def seg_lookup(size: str, pop: str) -> dict[str, str]:
        for r in seg_rows:
            if r["playlist_size_bucket"] == size and r["target_pop_bucket"] == pop:
                return r
        raise KeyError((size, pop))

    short_head = seg_lookup("short", "head")
    medium_head = seg_lookup("medium", "head")
    long_tail = seg_lookup("long", "tail")

    # Qualitative examples.
    hit_example = next((r for r in ex_rows if r.get("hit@10") == "1"), None)
    miss_example = next((r for r in ex_rows if r.get("hit@10") == "0"), None)

    lines: list[str] = []
    lines.append("# Hallazgos Finales para Poster y Paper")
    lines.append("")
    lines.append("## 1) Mensaje principal")
    lines.append(
        "El sistema Two-Stage Hybrid logra rendimiento competitivo en HitRate@10 y mejora fuerte en cobertura y novedad frente a comparadores simples, mientras que Sequential Markov lidera en MAP@10 y nDCG@10."
    )
    lines.append("")
    lines.append("## 2) Resultados principales (corrida 30 full)")
    lines.append("")
    lines.append("- Two-Stage Hybrid: "
                 f"HitRate@10={pct(f(hybrid, 'HitRate@10'))}, "
                 f"MAP@10={pct(f(hybrid, 'MAP@10'))}, "
                 f"nDCG@10={pct(f(hybrid, 'nDCG@10'))}, "
                 f"ILD@10={f(hybrid, 'ILD@10'):.3f}, "
                 f"Novelty@10={f(hybrid, 'Novelty@10'):.3f}, "
                 f"CatalogCoverage@10={pct(f(hybrid, 'CatalogCoverage@10'))}.")
    lines.append("- Sequential Markov: "
                 f"HitRate@10={pct(f(markov, 'HitRate@10'))}, "
                 f"MAP@10={pct(f(markov, 'MAP@10'))}, "
                 f"nDCG@10={pct(f(markov, 'nDCG@10'))}, "
                 f"CatalogCoverage@10={pct(f(markov, 'CatalogCoverage@10'))}.")
    lines.append("- Collaborative ItemKNN: "
                 f"HitRate@10={pct(f(iknn, 'HitRate@10'))}, "
                 f"MAP@10={pct(f(iknn, 'MAP@10'))}, "
                 f"CatalogCoverage@10={pct(f(iknn, 'CatalogCoverage@10'))}.")
    lines.append("")
    lines.append("Comparaciones directas relevantes:")
    lines.append("- Hybrid vs ItemKNN: "
                 f"HitRate@10 {delta(f(hybrid, 'HitRate@10'), f(iknn, 'HitRate@10'))}, "
                 f"MAP@10 {delta(f(hybrid, 'MAP@10'), f(iknn, 'MAP@10'))}, "
                 f"Cobertura {delta(f(hybrid, 'CatalogCoverage@10'), f(iknn, 'CatalogCoverage@10'))}.")
    lines.append("- Hybrid vs Markov: "
                 f"HitRate@10 {delta(f(hybrid, 'HitRate@10'), f(markov, 'HitRate@10'))}, "
                 f"MAP@10 {delta(f(hybrid, 'MAP@10'), f(markov, 'MAP@10'))}, "
                 f"nDCG@10 {delta(f(hybrid, 'nDCG@10'), f(markov, 'nDCG@10'))}, "
                 f"Cobertura {delta(f(hybrid, 'CatalogCoverage@10'), f(markov, 'CatalogCoverage@10'))}.")
    lines.append("")
    lines.append("## 3) Ablations (aporte de senales)")
    lines.append("")
    lines.append("Caida de MAP@10 respecto de Two-Stage Hybrid:")
    lines.append(f"- Sin cooc: {delta(f(abl_cooc, 'MAP@10'), f(hybrid, 'MAP@10'))}")
    lines.append(f"- Sin artist: {delta(f(abl_artist, 'MAP@10'), f(hybrid, 'MAP@10'))}")
    lines.append(f"- Sin name: {delta(f(abl_name, 'MAP@10'), f(hybrid, 'MAP@10'))}")
    lines.append(f"- Sin pop: {delta(f(abl_pop, 'MAP@10'), f(hybrid, 'MAP@10'))}")
    lines.append("")
    lines.append("Interpretacion corta:")
    lines.append("- Cooc es la senal estructural mas critica (mayor caida al removerla).")
    lines.append("- Artist y name aportan mejora incremental importante en ranking.")
    lines.append("- Popularidad tiene efecto menor en MAP@10, pero ayuda en estabilidad de cobertura.")
    lines.append("")
    lines.append("## 4) Analisis por segmentos")
    lines.append("")
    lines.append("- Head + short playlists: "
                 f"HitRate@10={pct(float(short_head['HitRate@10']))}, MAP@10={pct(float(short_head['MAP@10']))}.")
    lines.append("- Head + medium playlists: "
                 f"HitRate@10={pct(float(medium_head['HitRate@10']))}, MAP@10={pct(float(medium_head['MAP@10']))}.")
    lines.append("- Tail + long playlists: "
                 f"HitRate@10={pct(float(long_tail['HitRate@10']))}, MAP@10={pct(float(long_tail['MAP@10']))}.")
    lines.append("- Hallazgo: el modelo rinde muy bien en head/mid y cae fuerte en tail, lo que abre espacio para mejoras de long-tail en trabajo futuro.")
    lines.append("")
    lines.append("## 5) Robustez (20 sens)")
    lines.append("")
    lines.append("- Two-Stage Hybrid mantiene desempeno competitivo en sensibilidad: "
                 f"HitRate@10={pct(f(sens_m['Two-Stage Hybrid'], 'HitRate@10'))}, "
                 f"MAP@10={pct(f(sens_m['Two-Stage Hybrid'], 'MAP@10'))}. ")
    lines.append("- El orden relativo principal se mantiene: Markov fuerte en precision/ranking y Hybrid fuerte en cobertura/novedad.")
    lines.append("")
    lines.append("## 6) Ejemplos cualitativos para poster")
    lines.append("")
    if hit_example:
        lines.append("Ejemplo con acierto (hit@10=1):")
        lines.append(f"- Playlist: {hit_example['playlist_name']}")
        lines.append(f"- Perfil: {hit_example['profile']}")
        lines.append(f"- Target: {hit_example['target']}")
        lines.append(f"- Top-10: {hit_example['recs_top10']}")
        lines.append("")
    if miss_example:
        lines.append("Ejemplo con error (hit@10=0):")
        lines.append(f"- Playlist: {miss_example['playlist_name']}")
        lines.append(f"- Perfil: {miss_example['profile']}")
        lines.append(f"- Target: {miss_example['target']}")
        lines.append(f"- Top-10: {miss_example['recs_top10']}")
        lines.append("")

    lines.append("## 7) Texto sugerido para conclusiones del paper")
    lines.append("")
    lines.append(
        "Nuestros resultados muestran que una arquitectura de dos etapas basada en co-ocurrencia y reranking logra un balance competitivo entre exactitud y cobertura del catalogo. En particular, el sistema propuesto iguala o supera a comparadores colaborativos simples en HitRate@10 y mejora de forma consistente la novedad y cobertura, mientras que un baseline secuencial tipo Markov conserva ventaja en MAP@10 y nDCG@10. Las ablaciones confirman que la co-ocurrencia es la senal mas determinante del pipeline, seguida por las senales de artista y nombre de playlist. Finalmente, el analisis por segmentos evidencia que el metodo funciona mejor en objetivos de popularidad alta/media y playlists cortas/medias, manteniendo como desafio abierto el desempeno sobre cola larga."
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
