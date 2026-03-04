"""Dashboard module — web UI to visualize before/after pipeline processing."""

import logging

import pandas as pd
from flask import Flask, render_template_string

from pipeline.config import load_config
from pipeline.extract import extract
from pipeline.transform import (
    add_computed_columns,
    clean_amounts,
    deduplicate,
    normalize_categories,
    parse_dates,
)

logger = logging.getLogger(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Pipeline Dashboard</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #334155;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-light: #60a5fa;
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #eab308;
            --orange: #f97316;
            --row-dropped-bg: #1c0a0a;
            --row-dropped-text: #fca5a5;
            --row-modified-bg: #0c1a2e;
            --legend-dropped-bg: #450a0a;
            --legend-modified-bg: #0c1a2e;
            --badge-blue-bg: #1e3a5f;
            --badge-green-bg: #14532d;
            --badge-red-bg: #450a0a;
            --badge-yellow-bg: #422006;
            --badge-orange-bg: #431407;
            --icon-drop-bg: #450a0a;
            --icon-fix-bg: #14532d;
            --icon-dedup-bg: #422006;
            --icon-add-bg: #1e3a5f;
            --icon-warn-bg: #431407;
        }
        [data-theme="light"] {
            --bg: #f8fafc;
            --surface: #ffffff;
            --surface-hover: #f1f5f9;
            --border: #e2e8f0;
            --text: #1e293b;
            --text-muted: #64748b;
            --accent: #2563eb;
            --accent-light: #3b82f6;
            --green: #16a34a;
            --red: #dc2626;
            --yellow: #ca8a04;
            --orange: #ea580c;
            --row-dropped-bg: #fef2f2;
            --row-dropped-text: #991b1b;
            --row-modified-bg: #eff6ff;
            --legend-dropped-bg: #fecaca;
            --legend-modified-bg: #bfdbfe;
            --badge-blue-bg: #dbeafe;
            --badge-green-bg: #dcfce7;
            --badge-red-bg: #fee2e2;
            --badge-yellow-bg: #fef9c3;
            --badge-orange-bg: #ffedd5;
            --icon-drop-bg: #fee2e2;
            --icon-fix-bg: #dcfce7;
            --icon-dedup-bg: #fef9c3;
            --icon-add-bg: #dbeafe;
            --icon-warn-bg: #ffedd5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }
        .header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
        }
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        .header p {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
        }
        .stat-card .label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .stat-card .value {
            font-size: 1.75rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }
        .stat-card .detail {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }
        .stat-card .value.green { color: var(--green); }
        .stat-card .value.red { color: var(--red); }
        .stat-card .value.yellow { color: var(--yellow); }
        .stat-card .value.blue { color: var(--accent-light); }

        .section {
            margin-bottom: 2.5rem;
        }
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .section-header h2 {
            font-size: 1.25rem;
            font-weight: 600;
        }
        .badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .badge-blue { background: var(--badge-blue-bg); color: var(--accent-light); }
        .badge-green { background: var(--badge-green-bg); color: var(--green); }
        .badge-red { background: var(--badge-red-bg); color: var(--red); }
        .badge-yellow { background: var(--badge-yellow-bg); color: var(--yellow); }
        .badge-orange { background: var(--badge-orange-bg); color: var(--orange); }

        .changelog {
            display: grid;
            gap: 0.75rem;
        }
        .change-item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1rem 1.25rem;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }
        .change-icon {
            width: 2rem;
            height: 2rem;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
            margin-top: 0.1rem;
        }
        .change-icon.drop { background: var(--icon-drop-bg); color: var(--red); }
        .change-icon.fix { background: var(--icon-fix-bg); color: var(--green); }
        .change-icon.dedup { background: var(--icon-dedup-bg); color: var(--yellow); }
        .change-icon.add { background: var(--icon-add-bg); color: var(--accent-light); }
        .change-icon.warn { background: var(--icon-warn-bg); color: var(--orange); }
        .change-body h4 {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }
        .change-body p {
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .change-body .affected {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.4rem;
            font-style: italic;
        }

        .tabs {
            display: flex;
            gap: 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1rem;
        }
        .tab {
            padding: 0.75rem 1.25rem;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            color: var(--text-muted);
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.15s;
            background: none;
            border-top: none;
            border-left: none;
            border-right: none;
        }
        .tab:hover { color: var(--text); }
        .tab.active {
            color: var(--accent-light);
            border-bottom-color: var(--accent-light);
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .table-wrapper {
            overflow-x: auto;
            border: 1px solid var(--border);
            border-radius: 0.75rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        thead {
            background: var(--surface);
            position: sticky;
            top: 0;
        }
        th {
            text-align: left;
            padding: 0.75rem 1rem;
            font-weight: 600;
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
        }
        td {
            padding: 0.6rem 1rem;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: var(--surface-hover); }
        tr.row-dropped td {
            background: var(--row-dropped-bg);
            color: var(--row-dropped-text);
            text-decoration: line-through;
            opacity: 0.7;
        }
        tr.row-modified td { background: var(--row-modified-bg); }
        tr.row-modified td.cell-changed {
            color: var(--accent-light);
            font-weight: 600;
        }

        .legend {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
        .legend-dot.dropped { background: var(--legend-dropped-bg); border: 1px solid var(--red); }
        .legend-dot.modified {
            background: var(--legend-modified-bg);
            border: 1px solid var(--accent);
        }
        .legend-dot.unchanged { background: var(--surface); border: 1px solid var(--border); }

        .category-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
        }
        .cat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1rem;
        }
        .cat-card .cat-name {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: capitalize;
            margin-bottom: 0.5rem;
        }
        .cat-card .cat-stat {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .cat-card .cat-stat span {
            color: var(--text);
            font-weight: 600;
        }
        .theme-toggle {
            background: var(--surface-hover);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s;
        }
        .theme-toggle:hover {
            background: var(--border);
        }
        .header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-row">
            <div>
                <h1>ETL Pipeline Dashboard</h1>
                <p>Before &amp; after view of data processing &mdash;
                showing what changed and why</p>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()" id="theme-btn">
                <span id="theme-icon">&#9788;</span>
                <span id="theme-label">Light Mode</span>
            </button>
        </div>
    </div>

    <div class="container">
        <!-- Stats Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Input Rows</div>
                <div class="value blue">{{ stats.input_rows }}</div>
                <div class="detail">Raw records loaded</div>
            </div>
            <div class="stat-card">
                <div class="label">Output Rows</div>
                <div class="value green">{{ stats.output_rows }}</div>
                <div class="detail">After all transformations</div>
            </div>
            <div class="stat-card">
                <div class="label">Rows Dropped</div>
                <div class="value red">{{ stats.rows_dropped }}</div>
                <div class="detail">{{ stats.drop_pct }}% of input</div>
            </div>
            <div class="stat-card">
                <div class="label">Duplicates Removed</div>
                <div class="value yellow">{{ stats.duplicates }}</div>
                <div class="detail">Based on ID column</div>
            </div>
            <div class="stat-card">
                <div class="label">Dates Fixed</div>
                <div class="value blue">{{ stats.dates_fixed }}</div>
                <div class="detail">Non-standard formats parsed</div>
            </div>
            <div class="stat-card">
                <div class="label">Categories Normalized</div>
                <div class="value green">{{ stats.categories_normalized }}</div>
                <div class="detail">Case/whitespace cleaned</div>
            </div>
        </div>

        <!-- Transformation Changelog -->
        <div class="section">
            <div class="section-header">
                <h2>Transformation Changelog</h2>
            </div>
            <div class="changelog">
                {% for change in changelog %}
                <div class="change-item">
                    <div class="change-icon {{ change.icon_class }}">{{ change.icon }}</div>
                    <div class="change-body">
                        <h4>{{ change.title }}</h4>
                        <p>{{ change.description }}</p>
                        {% if change.affected_rows %}
                        <p class="affected">Affected rows: {{ change.affected_rows }}</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Data Tables -->
        <div class="section">
            <div class="section-header">
                <h2>Data Comparison</h2>
            </div>
            <div class="tabs">
                <button class="tab active" onclick="switchTab('before')">
                    Raw Input <span class="badge badge-blue">{{ stats.input_rows }} rows</span>
                </button>
                <button class="tab" onclick="switchTab('after')">
                    Processed Output <span class="badge badge-green">{{ stats.output_rows }}</span>
                </button>
                <button class="tab" onclick="switchTab('diff')">
                    Row-Level Diff <span class="badge badge-orange">{{ stats.total_changes }}</span>
                </button>
            </div>

            <div id="tab-before" class="tab-content active">
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                {% for col in before_columns %}
                                <th>{{ col }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in before_data %}
                            <tr>
                                {% for col in before_columns %}
                                <td>{{ row[col] }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="tab-after" class="tab-content">
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                {% for col in after_columns %}
                                <th>{{ col }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in after_data %}
                            <tr>
                                {% for col in after_columns %}
                                <td>{{ row[col] }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="tab-diff" class="tab-content">
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-dot dropped"></div> Dropped
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot modified"></div> Modified
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot unchanged"></div> Unchanged
                    </div>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>ID</th>
                                {% for col in diff_columns %}
                                <th>{{ col }}</th>
                                {% endfor %}
                                <th>Changes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in diff_data %}
                            <tr class="{{ row.row_class }}">
                                <td><span class="badge {{ row.status_badge }}">
                                    {{ row.status }}</span></td>
                                <td>{{ row.id }}</td>
                                {% for col in diff_columns %}
                                <td class="{{ 'cell-changed' if col in row.changed_cols else '' }}">
                                    {{ row.values[col] }}
                                </td>
                                {% endfor %}
                                <td>{{ row.change_summary }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Category Breakdown -->
        <div class="section">
            <div class="section-header">
                <h2>Category Breakdown (After Processing)</h2>
            </div>
            <div class="category-grid">
                {% for cat in categories %}
                <div class="cat-card">
                    <div class="cat-name">{{ cat.name }}</div>
                    <div class="cat-stat">Rows: <span>{{ cat.count }}</span></div>
                    <div class="cat-stat">Total: <span>${{ cat.total }}</span></div>
                    <div class="cat-stat">Avg: <span>${{ cat.avg }}</span></div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function switchTab(name) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + name).classList.add('active');
            event.target.closest('.tab').classList.add('active');
        }

        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', next);
            localStorage.setItem('etl-dashboard-theme', next);
            updateToggleButton(next);
        }

        function updateToggleButton(theme) {
            const icon = document.getElementById('theme-icon');
            const label = document.getElementById('theme-label');
            if (theme === 'light') {
                icon.innerHTML = '&#9789;';
                label.textContent = 'Dark Mode';
            } else {
                icon.innerHTML = '&#9788;';
                label.textContent = 'Light Mode';
            }
        }

        (function() {
            const saved = localStorage.getItem('etl-dashboard-theme');
            if (saved) {
                document.documentElement.setAttribute('data-theme', saved);
                updateToggleButton(saved);
            }
        })();
    </script>
</body>
</html>
"""


def _compute_diff(raw_df, processed_df):
    """Compute row-level diff between raw input and processed output."""
    raw_ids = set(raw_df["id"].tolist())
    processed_ids = set(processed_df["id"].tolist())

    dropped_ids = raw_ids - processed_ids
    kept_ids = raw_ids & processed_ids

    diff_rows = []
    shared_cols = ["date", "amount", "category", "description"]
    diff_columns = [c for c in shared_cols if c in raw_df.columns]
    seen_ids = set()

    for _, raw_row in raw_df.iterrows():
        row_id = raw_row["id"]

        # Handle duplicate raw rows (second+ occurrence of same ID)
        if row_id in seen_ids:
            values = {}
            for col in diff_columns:
                val = raw_row.get(col, "")
                values[col] = str(val) if pd.notna(val) else ""
            diff_rows.append(
                {
                    "id": row_id,
                    "status": "Dropped",
                    "status_badge": "badge-red",
                    "row_class": "row-dropped",
                    "values": values,
                    "changed_cols": [],
                    "change_summary": "Removed as duplicate",
                }
            )
            continue
        seen_ids.add(row_id)

        if row_id in dropped_ids:
            values = {}
            for col in diff_columns:
                val = raw_row.get(col, "")
                values[col] = str(val) if pd.notna(val) else ""
            diff_rows.append(
                {
                    "id": row_id,
                    "status": "Dropped",
                    "status_badge": "badge-red",
                    "row_class": "row-dropped",
                    "values": values,
                    "changed_cols": [],
                    "change_summary": "Removed during transform",
                }
            )
        elif row_id in kept_ids:
            proc_matches = processed_df[processed_df["id"] == row_id]
            if proc_matches.empty:
                continue
            proc_row = proc_matches.iloc[0]

            changed_cols = []
            changes = []
            values = {}

            for col in diff_columns:
                raw_val = raw_row.get(col, "")
                proc_val = proc_row.get(col, "")

                raw_str = str(raw_val) if pd.notna(raw_val) else ""
                proc_str = str(proc_val) if pd.notna(proc_val) else ""

                if raw_str.strip() != proc_str.strip():
                    changed_cols.append(col)
                    changes.append(f"{col}: {raw_str!r} -> {proc_str!r}")
                    values[col] = f"{raw_str} -> {proc_str}"
                else:
                    values[col] = proc_str

            if changed_cols:
                diff_rows.append(
                    {
                        "id": row_id,
                        "status": "Modified",
                        "status_badge": "badge-yellow",
                        "row_class": "row-modified",
                        "values": values,
                        "changed_cols": changed_cols,
                        "change_summary": "; ".join(changes),
                    }
                )
            else:
                diff_rows.append(
                    {
                        "id": row_id,
                        "status": "Unchanged",
                        "status_badge": "badge-green",
                        "row_class": "",
                        "values": values,
                        "changed_cols": [],
                        "change_summary": "",
                    }
                )

    return diff_rows, diff_columns


def _build_changelog(raw_df, processed_df, dedup_columns=None):
    """Build a list of human-readable transformation changes."""
    changelog = []

    # 1. Rows dropped for missing amounts
    nan_amount_ids = raw_df[raw_df["amount"].isna()]["id"].tolist()
    if nan_amount_ids:
        changelog.append(
            {
                "icon": "\u2716",
                "icon_class": "drop",
                "title": f"Dropped {len(nan_amount_ids)} rows with missing amounts",
                "description": "Rows where the amount column was blank/NaN were removed during"
                " the clean_amounts step.",
                "affected_rows": ", ".join(f"ID {i}" for i in nan_amount_ids),
            }
        )

    # 2. Duplicates removed
    dedup_cols = dedup_columns if dedup_columns else ["id"]
    dup_mask = raw_df.duplicated(subset=dedup_cols, keep="first")
    dup_ids = raw_df[dup_mask]["id"].tolist()
    if dup_ids:
        changelog.append(
            {
                "icon": "\u2716",
                "icon_class": "dedup",
                "title": f"Removed {len(dup_ids)} duplicate rows",
                "description": "Duplicate entries (same ID) were removed, keeping the first"
                " occurrence.",
                "affected_rows": ", ".join(f"ID {i}" for i in dup_ids),
            }
        )

    # 3. Categories normalized
    if "category" in raw_df.columns:
        changed_cats = raw_df[
            raw_df["category"].str.strip() != raw_df["category"].str.lower().str.strip()
        ]
        if len(changed_cats) > 0:
            changelog.append(
                {
                    "icon": "\u2714",
                    "icon_class": "fix",
                    "title": f"Normalized {len(changed_cats)} category values",
                    "description": "Categories were converted to lowercase and whitespace was"
                    " stripped (e.g. ' Food ' -> 'food', 'TRANSPORT' -> 'transport').",
                    "affected_rows": ", ".join(
                        f"ID {i}" for i in changed_cats["id"].tolist()[:10]
                    ),
                }
            )

    # 4. Dates parsed from non-standard formats
    if "date" in raw_df.columns:
        std_format = r"^\d{4}-\d{2}-\d{2}$"
        non_standard = raw_df[~raw_df["date"].astype(str).str.match(std_format)]
        if len(non_standard) > 0:
            changelog.append(
                {
                    "icon": "\u2714",
                    "icon_class": "fix",
                    "title": f"Parsed {len(non_standard)} dates from non-standard formats",
                    "description": "Dates in formats like MM/DD/YYYY, YYYY/MM/DD, or"
                    " unparseable strings were converted to standard datetime format.",
                    "affected_rows": ", ".join(
                        f"ID {i}" for i in non_standard["id"].tolist()[:10]
                    ),
                }
            )

    # 5. Computed columns added
    new_cols = [c for c in processed_df.columns if c not in raw_df.columns]
    if new_cols:
        changelog.append(
            {
                "icon": "+",
                "icon_class": "add",
                "title": f"Added {len(new_cols)} computed columns",
                "description": f"New columns added: {', '.join(new_cols)}.",
                "affected_rows": None,
            }
        )

    return changelog


def run_dashboard(config=None, host="127.0.0.1", port=5050):
    """Launch the Flask dashboard showing before/after pipeline data."""
    if config is None:
        config = load_config()

    # Run extract
    raw_df = extract(config)
    raw_display = raw_df.copy()

    # Run transform step-by-step to capture intermediate states
    df = raw_df.copy()
    df_after_clean = clean_amounts(df.copy())
    df_after_norm = normalize_categories(df_after_clean.copy())
    date_format = config.get("date_format", "%Y-%m-%d")
    df_after_dates = parse_dates(df_after_norm.copy(), date_format)
    df_after_dedup = deduplicate(
        df_after_dates.copy(), subset=config.get("dedup_columns", ["id"])
    )

    # add_computed_columns may fail due to intentional bug (string vs float comparison)
    try:
        processed_df = add_computed_columns(df_after_dedup.copy())
    except TypeError as e:
        logger.warning(f"add_computed_columns partially failed: {e}")
        processed_df = df_after_dedup.copy()
        # Add the columns we can safely compute
        processed_df["amount_usd"] = processed_df["amount"]
        if "date" in processed_df.columns:
            processed_df["quarter"] = processed_df["date"].dt.quarter
        # Mark is_high_value as failed
        processed_df["is_high_value"] = None

    # Compute stats
    dedup_cols = config.get("dedup_columns", ["id"])
    dup_count = int(raw_df.duplicated(subset=dedup_cols, keep="first").sum())

    cat_changed = 0
    if "category" in raw_df.columns:
        cat_changed = int(
            (
                raw_df["category"].str.strip() != raw_df["category"].str.lower().str.strip()
            ).sum()
        )

    dates_fixed = 0
    if "date" in raw_df.columns:
        std_format = r"^\d{4}-\d{2}-\d{2}$"
        dates_fixed = int((~raw_df["date"].astype(str).str.match(std_format)).sum())

    rows_dropped = len(raw_df) - len(processed_df)
    drop_pct = round(rows_dropped / len(raw_df) * 100, 1) if len(raw_df) > 0 else 0

    # Normalize dates to strings before diff comparison so that
    # "2024-01-02" vs Timestamp("2024-01-02 00:00:00") aren't flagged
    diff_processed = processed_df.copy()
    if "date" in diff_processed.columns:
        diff_processed["date"] = (
            diff_processed["date"].dt.strftime("%Y-%m-%d").fillna("")
        )
    diff_data, diff_columns = _compute_diff(raw_df, diff_processed)
    total_changes = sum(1 for d in diff_data if d["status"] != "Unchanged")

    stats = {
        "input_rows": len(raw_df),
        "output_rows": len(processed_df),
        "rows_dropped": rows_dropped,
        "drop_pct": drop_pct,
        "duplicates": dup_count,
        "dates_fixed": dates_fixed,
        "categories_normalized": cat_changed,
        "total_changes": total_changes,
    }

    changelog = _build_changelog(raw_df, processed_df, dedup_columns=dedup_cols)

    # Category breakdown
    categories = []
    if "category" in processed_df.columns and "amount" in processed_df.columns:
        for cat, group in processed_df.groupby("category"):
            categories.append(
                {
                    "name": cat,
                    "count": len(group),
                    "total": f"{group['amount'].sum():,.2f}",
                    "avg": f"{group['amount'].mean():,.2f}",
                }
            )
        categories.sort(key=lambda x: x["name"])

    # Prepare display DataFrames
    before_data = raw_display.fillna("").to_dict("records")
    before_columns = list(raw_display.columns)

    # Format processed for display
    proc_display = processed_df.copy()
    if "date" in proc_display.columns:
        proc_display["date"] = proc_display["date"].dt.strftime("%Y-%m-%d").fillna("NaT")
    after_data = proc_display.fillna("").to_dict("records")
    after_columns = list(proc_display.columns)

    # Build Flask app
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(
            DASHBOARD_HTML,
            stats=stats,
            changelog=changelog,
            before_data=before_data,
            before_columns=before_columns,
            after_data=after_data,
            after_columns=after_columns,
            diff_data=diff_data,
            diff_columns=diff_columns,
            categories=categories,
        )

    logger.info(f"Starting dashboard at http://{host}:{port}")
    print(f"\n  Dashboard running at http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False)
