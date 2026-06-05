from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_ORDER = [
    "Random",
    "Most Popular",
    "Playlist Name Popular",
    "Two-Stage Cooc+Rerank",
    "Two-Stage + LastFM",
]


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    if not rows:
        raise ValueError(f"CSV sin filas: {csv_path}")
    return rows


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def by_order(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    index = {name: i for i, name in enumerate(DEFAULT_ORDER)}
    return sorted(rows, key=lambda r: index.get(r.get("Modelo", ""), 999))


def find_row(rows: list[dict[str, str]], model: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("Modelo") == model:
            return row
    return None


def safe_ratio(a: float, b: float) -> float:
    if b <= 0:
        return 0.0
    return a / b


def build_tex(
    rows: list[dict[str, str]],
    sample_percent: str,
    eval_playlists: str,
    source_csv: str,
) -> str:
    rows = by_order(rows)

    two_stage = find_row(rows, "Two-Stage Cooc+Rerank")
    two_stage_lastfm = find_row(rows, "Two-Stage + LastFM")
    playlist_name = find_row(rows, "Playlist Name Popular")
    most_popular = find_row(rows, "Most Popular")

    if two_stage is None or playlist_name is None or most_popular is None:
        raise ValueError(
            "CSV debe contener al menos: Two-Stage Cooc+Rerank, Playlist Name Popular, Most Popular"
        )

    ts_hr = to_float(two_stage["HitRate@10"])
    ts_ndcg = to_float(two_stage["nDCG@10"])

    pnp_hr = to_float(playlist_name["HitRate@10"])
    pnp_ndcg = to_float(playlist_name["nDCG@10"])

    mp_hr = to_float(most_popular["HitRate@10"])
    mp_ndcg = to_float(most_popular["nDCG@10"])

    ratio_hr_vs_pnp = safe_ratio(ts_hr, pnp_hr)
    ratio_ndcg_vs_pnp = safe_ratio(ts_ndcg, pnp_ndcg)
    ratio_hr_vs_mp = safe_ratio(ts_hr, mp_hr)
    ratio_ndcg_vs_mp = safe_ratio(ts_ndcg, mp_ndcg)

    lastfm_line = "No disponible en esta corrida."
    if two_stage_lastfm is not None:
        lfm_map = to_float(two_stage_lastfm["MAP@10"])
        lfm_ndcg = to_float(two_stage_lastfm["nDCG@10"])
        ts_map = to_float(two_stage["MAP@10"])
        delta_map = lfm_map - ts_map
        delta_ndcg = lfm_ndcg - ts_ndcg
        lastfm_line = (
            "En esta corrida, Two-Stage + LastFM "
            f"presenta $\\Delta$MAP@10={delta_map:.4f} y $\\Delta$nDCG@10={delta_ndcg:.4f} "
            "respecto a Two-Stage Cooc+Rerank."
        )

    table_lines = []
    for r in rows:
        table_lines.append(
            f"{r['Modelo']} & {to_float(r['HitRate@10']):.4f} & {to_float(r['Precision@10']):.4f} & {to_float(r['MAP@10']):.4f} & {to_float(r['nDCG@10']):.4f}\\\\"
        )

    tex = f"""% Archivo generado automaticamente desde {source_csv}
% Inserta con: \\input{{seccion_resultados_midterm_auto.tex}}

\\section{{Resultados finales Midterm}}

Esta seccion resume la corrida seleccionada como principal para entrega, con muestra del {sample_percent}\\% y {eval_playlists} playlists evaluadas en protocolo \\textit{{leave-last-out}}.

\\begin{{table}}[H]
\\centering
\\small
\\begin{{tabular}}{{lrrrr}}
\\toprule
\\textbf{{Modelo}} & \\textbf{{HitRate@10}} & \\textbf{{Precision@10}} & \\textbf{{MAP@10}} & \\textbf{{nDCG@10}}\\\\
\\midrule
{chr(10).join(table_lines)}
\\bottomrule
\\end{{tabular}}
\\caption{{Resultados finales del Midterm en evaluacion top-10 (fuente: {source_csv}).}}
\\label{{tab:midterm_results_final}}
\\end{{table}}

\\section{{Conclusiones finales}}

\\textbf{{Conclusion 1}}: Two-Stage Cooc+Rerank supera a Playlist Name Popular por un factor aproximado de {ratio_hr_vs_pnp:.2f}x en HitRate@10 y {ratio_ndcg_vs_pnp:.2f}x en nDCG@10.

\\textbf{{Conclusion 2}}: frente a Most Popular, la mejora alcanza aproximadamente {ratio_hr_vs_mp:.2f}x en HitRate@10 y {ratio_ndcg_vs_mp:.2f}x en nDCG@10.

\\textbf{{Conclusion 3}}: {lastfm_line}

\\textbf{{Conclusion 4}}: el enfoque principal definido para Midterm (retrieval por co-ocurrencia + reranking) queda respaldado empiricamente sobre los baselines exigidos por el curso.
"""
    return tex


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera una seccion LaTeX de resultados y conclusiones desde CSV Midterm")
    parser.add_argument("--csv", required=True, help="Ruta al CSV de resultados")
    parser.add_argument(
        "--output",
        default="seccion_resultados_midterm_auto.tex",
        help="Ruta del archivo .tex de salida",
    )
    parser.add_argument(
        "--sample-percent",
        default="30",
        help="Porcentaje de muestra usado en la corrida principal",
    )
    parser.add_argument(
        "--eval-playlists",
        default="(completar)",
        help="Cantidad de playlists evaluadas en la corrida principal",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.output)

    rows = load_rows(csv_path)
    tex = build_tex(
        rows=rows,
        sample_percent=args.sample_percent,
        eval_playlists=args.eval_playlists,
        source_csv=csv_path.name,
    )
    out_path.write_text(tex, encoding="utf-8")
    print(f"Seccion generada en: {out_path}")


if __name__ == "__main__":
    main()
