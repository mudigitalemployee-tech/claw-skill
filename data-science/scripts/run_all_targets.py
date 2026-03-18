#!/usr/bin/env python3
"""
run_all_targets.py — Multi-target forecasting wrapper
Runs phase2 + phase3 for each numeric target column when target=all,
then assembles a combined report.

RC7/CR2/CR6: Auto-detects ALL numeric target columns from the dataset
instead of using a hardcoded list.
"""

import subprocess
import sys
import os
import json
import shutil
import argparse
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE = Path(__file__).resolve().parent.parent  # data-science root
SCRIPTS = BASE / "scripts"
PHASE1_DIR = BASE / "artifacts" / "phase1"
PHASE2_BASE = BASE / "artifacts" / "phase2"
PHASE3_BASE = BASE / "artifacts" / "phase3"


def auto_detect_targets(phase1_dir: Path) -> list:
    """
    Auto-detect all numeric target columns from the phase1 results.
    Uses schema from phase1_results.json to find all numeric columns,
    excluding the date column and date-derived features.
    """
    from utils import DATE_DERIVED_SUFFIXES

    p1_results_path = phase1_dir / "phase1_results.json"
    if not p1_results_path.exists():
        raise FileNotFoundError(
            f"Phase 1 results not found at {p1_results_path}. Run Phase 1 first."
        )

    with open(p1_results_path) as f:
        p1 = json.load(f)

    schema = p1.get("schema", {})
    date_cols = p1.get("date_cols_detected", [])
    target_col = p1.get("target", "")

    targets = []
    for col, info in schema.items():
        col_type = info.get("col_type", "")
        # Include only numeric columns
        if col_type != "numeric":
            continue
        # Exclude the primary date column
        if col in date_cols:
            continue
        # Exclude date-derived features
        if any(col.endswith(suffix) for suffix in DATE_DERIVED_SUFFIXES):
            continue
        targets.append(col)

    if not targets:
        # Fallback: try loading the clean_train.csv and using numeric cols
        train_path = phase1_dir / "clean_train.csv"
        if train_path.exists():
            df = pd.read_csv(train_path)
            targets = [
                c for c in df.select_dtypes(include="number").columns
                if not any(c.endswith(s) for s in DATE_DERIVED_SUFFIXES)
            ]

    return targets


def main():
    parser = argparse.ArgumentParser(
        description="Multi-target pipeline wrapper: Phase 2 + Phase 3 for all numeric targets"
    )
    parser.add_argument("--project_name", required=True,
                        help="Project name for report (e.g., Macrovar, Customer_Churn)")
    parser.add_argument("--task_type", required=True,
                        help="Task type (forecasting, regression, classification, segmentation)")
    parser.add_argument("--input", default=None,
                        help="Path to input CSV (for auto-detection fallback)")
    parser.add_argument("--phase1_dir", default=None,
                        help="Phase 1 artifacts dir")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Keep artifacts after report")
    parser.add_argument("--cleanup", action="store_true",
                        default=True, help="Clean artifacts after report")
    parser.add_argument("--cleanup-delay", type=int,
                        default=0, help="Seconds before cleanup")
    args = parser.parse_args()

    project_name = args.project_name
    task_type = args.task_type
    p1_dir = Path(args.phase1_dir) if args.phase1_dir else PHASE1_DIR

    # ── Auto-detect targets (RC7, CR2, CR6) ──
    try:
        TARGETS = auto_detect_targets(p1_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not TARGETS:
        print("Error: No numeric target columns detected. Check your dataset.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  AUTO-DETECTED {len(TARGETS)} TARGET COLUMNS")
    print(f"{'='*70}")
    for i, t in enumerate(TARGETS, 1):
        print(f"  {i}. {t}")

    all_phase2_results = {}
    all_phase3_results = {}
    best_models_summary = []

    for i, target in enumerate(TARGETS):
        print(f"\n{'='*70}")
        print(f"  TARGET {i+1}/{len(TARGETS)}: {target}")
        print(f"{'='*70}")

        p2_dir = PHASE2_BASE / target
        p3_dir = PHASE3_BASE / target
        p2_dir.mkdir(parents=True, exist_ok=True)
        p3_dir.mkdir(parents=True, exist_ok=True)

        # ── Phase 2 ──
        print(f"\n  -> Phase 2: Model Selection for {target}")
        cmd2 = [
            sys.executable, str(SCRIPTS / "phase2_modeling.py"),
            "--task_type", task_type,
            "--target", target,
            "--phase1_dir", str(p1_dir),
            "--output_dir", str(p2_dir),
        ]
        try:
            r2 = subprocess.run(cmd2, capture_output=True,
                                text=True, timeout=600)
            print(r2.stdout[-500:] if len(r2.stdout) > 500 else r2.stdout)
            if r2.returncode != 0:
                print(
                    f"  Warning: Phase 2 failed for {target}: {r2.stderr[-300:]}")
                continue
        except subprocess.TimeoutExpired:
            print(f"  Warning: Phase 2 timed out for {target}")
            continue
        except Exception as e:
            print(f"  Warning: Phase 2 error for {target}: {e}")
            continue

        # Load phase2 results
        try:
            with open(p2_dir / "phase2_results.json") as f:
                p2r = json.load(f)
            all_phase2_results[target] = p2r
            best_models_summary.append({
                "target": target,
                "best_model": p2r["best_model"],
                "metrics": p2r["fine_tuned_metrics"],
            })
        except Exception as e:
            print(
                f"  Warning: Could not load phase2 results for {target}: {e}")
            continue

        # ── Phase 3 ──
        print(f"\n  -> Phase 3: Execution for {target}")
        cmd3 = [
            sys.executable, str(SCRIPTS / "phase3_execution.py"),
            "--task_type", task_type,
            "--target", target,
            "--phase1_dir", str(p1_dir),
            "--phase2_dir", str(p2_dir),
            "--output_dir", str(p3_dir),
        ]
        try:
            r3 = subprocess.run(cmd3, capture_output=True,
                                text=True, timeout=600)
            print(r3.stdout[-500:] if len(r3.stdout) > 500 else r3.stdout)
            if r3.returncode != 0:
                print(
                    f"  Warning: Phase 3 failed for {target}: {r3.stderr[-300:]}")
                continue
        except subprocess.TimeoutExpired:
            print(f"  Warning: Phase 3 timed out for {target}")
            continue
        except Exception as e:
            print(f"  Warning: Phase 3 error for {target}: {e}")
            continue

        # Load phase3 results
        try:
            with open(p3_dir / "phase3_results.json") as f:
                p3r = json.load(f)
            all_phase3_results[target] = p3r
        except Exception as e:
            print(
                f"  Warning: Could not load phase3 results for {target}: {e}")

    # ── Consolidate results into the standard artifact dirs ──
    print(f"\n{'='*70}")
    print("  CONSOLIDATION - Merging per-target results")
    print(f"{'='*70}")

    # Merge all phase2 results
    combined_p2 = {
        "task_type": task_type,
        "target": "all",
        "per_target_results": all_phase2_results,
        "best_models_summary": best_models_summary,
    }
    with open(PHASE2_BASE / "phase2_results.json", "w") as f:
        json.dump(combined_p2, f, indent=2)

    # Build combined model comparison chart
    from utils import CHART_PALETTE
    chart_traces = []
    for entry in best_models_summary:
        t = entry["target"]
        m = entry["metrics"]
        chart_traces.append({
            "target": t.replace("_", " "),
            "model": entry["best_model"],
            "rmse": m.get("rmse", 0),
            "mape": m.get("mape", 0),
            "r2": m.get("r2", 0),
        })

    comparison_chart = {
        "chart_id": "model_comparison",
        "title": "Best Model per Variable - Forecasting",
        "data": [
            {
                "type": "bar",
                "name": "RMSE",
                "x": [t["target"] for t in chart_traces],
                "y": [t["rmse"] for t in chart_traces],
                "text": [t["model"] for t in chart_traces],
                "marker": {"color": CHART_PALETTE[0]},
            },
            {
                "type": "bar",
                "name": "MAPE (%)",
                "x": [t["target"] for t in chart_traces],
                "y": [t["mape"] for t in chart_traces],
                "marker": {"color": CHART_PALETTE[2]},
            },
        ],
        "layout": {
            "barmode": "group",
            "title": {"text": "Best Model per Variable - RMSE & MAPE"},
            "xaxis": {"title": "Variable", "tickangle": -30},
            "yaxis": {"title": "Score"},
        },
    }
    with open(PHASE2_BASE / "model_comparison_chart.json", "w") as f:
        json.dump(comparison_chart, f, indent=2)

    # Merge all phase3 results
    combined_p3 = {
        "task_type": task_type,
        "target": "all",
        "per_target_results": all_phase3_results,
    }
    with open(PHASE3_BASE / "phase3_results.json", "w") as f:
        json.dump(combined_p3, f, indent=2)

    # Merge execution charts from all targets
    all_charts = []
    for target, p3r in all_phase3_results.items():
        p3_chart_path = PHASE3_BASE / target / "execution_charts.json"
        if p3_chart_path.exists():
            with open(p3_chart_path) as f:
                charts = json.load(f)
            for c in charts:
                c["chart_id"] = f"{target}_{c.get('chart_id', 'chart')}"
                c["title"] = f"{target.replace('_', ' ')}: {c.get('title', '')}"
            all_charts.extend(charts)
    with open(PHASE3_BASE / "execution_charts.json", "w") as f:
        json.dump(all_charts, f, indent=2)

    # Merge business insights
    all_insights = []
    for target, p3r in all_phase3_results.items():
        bi_path = PHASE3_BASE / target / "business_insights.json"
        if bi_path.exists():
            with open(bi_path) as f:
                bi = json.load(f)
            if isinstance(bi, list):
                for b in bi:
                    b["target_variable"] = target
                all_insights.extend(bi)
            elif isinstance(bi, dict):
                bi["target_variable"] = target
                all_insights.append(bi)
    with open(PHASE3_BASE / "business_insights.json", "w") as f:
        json.dump(all_insights, f, indent=2)

    # Copy best_model.pkl from first successful target (for compatibility)
    for target in TARGETS:
        pkl = PHASE2_BASE / target / "best_model.pkl"
        if pkl.exists():
            shutil.copy(pkl, PHASE2_BASE / "best_model.pkl")
            break

    # Copy per_model_iteration_tables from all targets
    all_iterations = {}
    for target in TARGETS:
        itr_path = PHASE2_BASE / target / "per_model_iteration_tables.json"
        if itr_path.exists():
            with open(itr_path) as f:
                itr = json.load(f)
            all_iterations[target] = itr
    with open(PHASE2_BASE / "per_model_iteration_tables.json", "w") as f:
        json.dump(all_iterations, f, indent=2)

    # Merge per_model_predictions from all targets
    all_predictions = {}
    for target in TARGETS:
        pred_path = PHASE2_BASE / target / "per_model_predictions.json"
        if pred_path.exists():
            with open(pred_path) as f:
                pred = json.load(f)
            all_predictions[target] = pred
    if all_predictions:
        with open(PHASE2_BASE / "per_model_predictions.json", "w") as f:
            json.dump(all_predictions, f, indent=2)

    # Merge feature_selection_rationale from all targets
    all_rationale = {}
    for target in TARGETS:
        rat_path = PHASE2_BASE / target / "feature_selection_rationale.json"
        if rat_path.exists():
            with open(rat_path) as f:
                rat = json.load(f)
            all_rationale[target] = rat
    if all_rationale:
        with open(PHASE2_BASE / "feature_selection_rationale.json", "w") as f:
            json.dump(all_rationale, f, indent=2)

    # Merge drift matrices from all targets (CR16)
    all_drift = {}
    for target in TARGETS:
        drift_path = PHASE3_BASE / target / "drift_matrix.json"
        if drift_path.exists():
            with open(drift_path) as f:
                drift_data = json.load(f)
            all_drift.update(drift_data)  # target-keyed format
    if all_drift:
        with open(PHASE3_BASE / "drift_matrix.json", "w") as f:
            json.dump(all_drift, f, indent=2)

    # Merge chart conclusions from all targets (CR5/CR6)
    all_chart_conclusions = {}
    for target in TARGETS:
        cc_path = PHASE3_BASE / target / "chart_conclusions.json"
        if cc_path.exists():
            with open(cc_path) as f:
                cc = json.load(f)
            if isinstance(cc, dict):
                for k, v in cc.items():
                    all_chart_conclusions[f"{target}_{k}"] = v
    if all_chart_conclusions:
        with open(PHASE3_BASE / "chart_conclusions.json", "w") as f:
            json.dump(all_chart_conclusions, f, indent=2)

    print(f"\n{len(best_models_summary)}/{len(TARGETS)} targets complete.")
    print(f"\nBest models summary:")
    for entry in best_models_summary:
        t = entry["target"]
        m = entry["best_model"]
        rmse = entry["metrics"].get("rmse", "N/A")
        mape = entry["metrics"].get("mape", "N/A")
        print(f"  {t:45s} -> {m:25s} RMSE={rmse}, MAPE={mape}%")

    # ── Aggregate Self-Check Results (Step 7b, CR22) — before report so artifacts exist ──
    print(f"\n{'='*70}")
    print("  SELF-CHECK AGGREGATION")
    print(f"{'='*70}")

    self_check_summary = {"phase1": None, "phase2": {}, "phase3": {}}

    # Phase 1 self-check (global)
    p1_sc_path = p1_dir / "self_check_results.json"
    if p1_sc_path.exists():
        with open(p1_sc_path) as f:
            self_check_summary["phase1"] = json.load(f)
        print(
            f"  Phase 1 self-check: {'PASS' if self_check_summary['phase1'].get('passed') else 'WARN'}")

    # Phase 2 & 3 self-checks (per-target)
    total_warnings = 0
    total_errors = 0
    total_major_warnings = 0
    total_minor_warnings = 0
    for target in TARGETS:
        for phase, base_dir in [("phase2", PHASE2_BASE), ("phase3", PHASE3_BASE)]:
            sc_path = base_dir / target / "self_check_results.json"
            if sc_path.exists():
                with open(sc_path) as f:
                    sc = json.load(f)
                self_check_summary[phase][target] = sc
                # v5 Step 12: Classify warnings by severity
                warnings = sc.get("warnings", [])
                n_warn = len(warnings)
                n_major = sum(1 for w in warnings
                              if (isinstance(w, dict) and w.get("severity") == "major") or
                                 (isinstance(w, str) and any(kw in w.lower() for kw in ["nan", "empty", "schema"])))
                n_minor = n_warn - n_major
                n_err = len(sc.get("errors", []))
                total_warnings += n_warn
                total_major_warnings += n_major
                total_minor_warnings += n_minor
                total_errors += n_err
                if n_warn > 0 or n_err > 0:
                    status = "ERROR" if n_err > 0 else "MAJOR-WARN" if n_major > 0 else "WARN"
                    print(
                        f"  {phase}/{target}: {status} ({n_major} major, {n_minor} minor warnings, {n_err} errors)")

    # Save aggregate
    self_check_summary["total_warnings"] = total_warnings
    self_check_summary["total_major_warnings"] = total_major_warnings
    self_check_summary["total_minor_warnings"] = total_minor_warnings
    self_check_summary["total_errors"] = total_errors
    self_check_summary["all_passed"] = total_errors == 0 and total_major_warnings == 0

    sc_out = PHASE3_BASE / "self_check_summary.json"
    sc_out.parent.mkdir(parents=True, exist_ok=True)
    with open(sc_out, "w") as f:
        json.dump(self_check_summary, f, indent=2)

    if total_errors > 0:
        print(
            f"\n  ⚠️  SELF-CHECK: {total_errors} errors, {total_major_warnings} major + {total_minor_warnings} minor warnings")
        print(f"  Pipeline continues (lenient mode) — review self_check_summary.json")
    elif total_major_warnings > 0:
        print(
            f"\n  ⚠  {total_major_warnings} MAJOR + {total_minor_warnings} minor warnings (no errors)")
        if total_major_warnings > 5:
            print(f"  ⚠️  Major warnings exceed threshold (5). Review recommended before production use.")
    elif total_minor_warnings > 0:
        print(
            f"\n  ℹ  {total_minor_warnings} minor warnings (no major warnings, no errors)")
    else:
        print(f"\n  ✅ All self-checks passed across all targets")

    # ── Assemble Report ──
    print(f"\n{'='*70}")
    print("  REPORT ASSEMBLY")
    print(f"{'='*70}")

    cleanup_flag = "--cleanup"
    cleanup_delay_val = str(args.cleanup_delay)
    if args.no_cleanup:
        cleanup_flag = "--no-cleanup"

    cmd_report = [
        sys.executable, str(SCRIPTS / "build_musigma_report.py"),
        "--project_name", project_name,
        "--task_type", task_type,
        "--phase1_dir", str(p1_dir),
        "--phase2_dir", str(PHASE2_BASE),
        "--phase3_dir", str(PHASE3_BASE),
        cleanup_flag,
        "--cleanup-delay", cleanup_delay_val,
    ]
    try:
        r_report = subprocess.run(
            cmd_report, capture_output=True, text=True, timeout=300)
        print(r_report.stdout)
        if r_report.returncode != 0:
            print(f"Warning: Report assembly error: {r_report.stderr[-500:]}")
    except Exception as e:
        print(f"Warning: Report assembly failed: {e}")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
