#!/usr/bin/env python3
"""
MONTE CARLO PATTERNS HTML REPORT GENERATOR
Generates beautiful, interactive HTML reports from MC pattern analysis
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class MCPatternsReportGenerator:
    """Generate comprehensive HTML reports from Monte Carlo pattern analysis"""
    
    def __init__(self, output_dir: str = "monte_carlo_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def generate_html_report(self, mc_report: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """Generate a comprehensive HTML report from MC analysis"""
        if output_filename is None:
            output_filename = f"mc_report_{mc_report.get('run_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
        output_path = self.output_dir / output_filename
        
        html_content = self._generate_html_content(mc_report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"HTML report generated: {output_path}")
        return str(output_path)
        
    def _generate_html_content(self, mc_report: Dict[str, Any]) -> str:
        """Generate the actual HTML content"""
        base = mc_report.get("base_metrics", {})
        mc = mc_report.get("mc", {})
        patterns = mc_report.get("patterns", {})
        lev = mc_report.get("leverageability", {})
        
        # Extract pattern data
        hod = patterns.get("hour_of_day", {})
        runs_test = patterns.get("runs_test", {})
        motifs = patterns.get("motifs", {})
        dd_clusters = patterns.get("drawdown_clusters", {})
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monte Carlo Pattern Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 12px;
            padding: 30px;
            border-left: 5px solid #667eea;
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .metric-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-card .value {{
            color: #333;
            font-size: 2em;
            font-weight: 700;
        }}
        
        .metric-card .subvalue {{
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .good {{
            color: #10b981;
        }}
        
        .bad {{
            color: #ef4444;
        }}
        
        .neutral {{
            color: #f59e0b;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .interpretation {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }}
        
        .interpretation strong {{
            color: #b45309;
        }}
        
        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin-top: 15px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }}
        
        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge-warning {{
            background: #fef3c7;
            color: #b45309;
        }}
        
        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e5e7eb;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎲 Monte Carlo Pattern Analysis Report</h1>
            <div class="subtitle">
                Run ID: {mc_report.get('run_id', 'N/A')} | 
                Generated: {mc_report.get('timestamp', datetime.now().isoformat())}
            </div>
        </div>
        
        <div class="content">
            <!-- Base Performance Metrics -->
            <div class="section">
                <h2>📊 Base Performance Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="label">Sharpe Ratio</div>
                        <div class="value {self._classify_sharpe(base.get('sharpe', 0))}">{base.get('sharpe', 0):.3f}</div>
                        <div class="subvalue">Annualized</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Max Drawdown</div>
                        <div class="value {self._classify_drawdown(base.get('max_dd', 0))}">{base.get('max_dd', 0):.2%}</div>
                        <div class="subvalue">Peak to Trough</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Ulcer Index</div>
                        <div class="value">{base.get('ulcer', 0):.3f}</div>
                        <div class="subvalue">Drawdown Volatility</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Number of Trades</div>
                        <div class="value">{base.get('trades', 0)}</div>
                        <div class="subvalue">Sample Size</div>
                    </div>
                </div>
            </div>
            
            <!-- Monte Carlo Distribution -->
            <div class="section">
                <h2>🎯 Monte Carlo Distribution ({mc.get('runs', 0)} simulations)</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="label">MC Sharpe Mean</div>
                        <div class="value">{mc.get('sharpe_mean', 0):.3f}</div>
                        <div class="subvalue">P5: {mc.get('sharpe_p05', 0):.3f} | P95: {mc.get('sharpe_p95', 0):.3f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">MC MaxDD Mean</div>
                        <div class="value">{mc.get('maxdd_mean', 0):.2%}</div>
                        <div class="subvalue">P95: {mc.get('maxdd_p95', 0):.2%}</div>
                    </div>
                </div>
                <div class="interpretation">
                    <strong>Interpretation:</strong> 
                    {self._interpret_mc_results(base.get('sharpe', 0), mc.get('sharpe_mean', 0), mc.get('sharpe_p05', 0))}
                </div>
            </div>
            
            <!-- Hour of Day Effect -->
            <div class="section">
                <h2>🕐 Hour-of-Day Effect Analysis</h2>
                <p><strong>Kruskal-Wallis Test:</strong> H = {hod.get('kruskal_H', 0):.3f}, p-value = {hod.get('p_value', 1):.4f}</p>
                
                <div style="margin: 20px 0;">
                    <span class="badge badge-success">Best Hours: {', '.join(map(str, hod.get('best_hours', [])))}</span>
                    <span class="badge badge-danger">Worst Hours: {', '.join(map(str, hod.get('worst_hours', [])))}</span>
                </div>
                
                {self._generate_hour_table(hod.get('table', []))}
                
                <div class="interpretation">
                    <strong>Interpretation:</strong> 
                    {self._interpret_hour_effect(hod.get('p_value', 1))}
                </div>
            </div>
            
            <!-- Leverageability Test -->
            <div class="section">
                <h2>⚡ Leverageability Analysis</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="label">Mean Sharpe Uplift</div>
                        <div class="value {self._classify_uplift(lev.get('uplift_mean', 0))}">{lev.get('uplift_mean', 0):.3f}</div>
                        <div class="subvalue">P95: {lev.get('uplift_p95', 0):.3f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Positive Uplift Rate</div>
                        <div class="value">{lev.get('uplift_frac_positive', 0):.1%}</div>
                        <div class="subvalue">{lev.get('n_paths', 0)} paths tested</div>
                    </div>
                </div>
                <div class="interpretation">
                    <strong>Strategy:</strong> 
                    Filter worst hours (zero allocation), leverage best hours (1.25x).
                    {self._interpret_leverageability(lev.get('uplift_mean', 0), lev.get('uplift_frac_positive', 0))}
                </div>
            </div>
            
            <!-- Runs Test -->
            <div class="section">
                <h2>🔄 Runs Test (Randomness Check)</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="label">Z-Score</div>
                        <div class="value">{runs_test.get('z', 0):.3f}</div>
                        <div class="subvalue">p-value: {runs_test.get('p', 1):.4f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Runs / Expected</div>
                        <div class="value">{runs_test.get('runs', 0)}</div>
                        <div class="subvalue">Pos: {runs_test.get('n_pos', 0)} | Neg: {runs_test.get('n_neg', 0)}</div>
                    </div>
                </div>
                <div class="interpretation">
                    <strong>Interpretation:</strong> 
                    {self._interpret_runs_test(runs_test.get('z', 0), runs_test.get('p', 1))}
                </div>
            </div>
            
            <!-- Motifs and Discords -->
            <div class="section">
                <h2>🔍 Pattern Discovery (Motifs & Discords)</h2>
                <p><strong>Recurring Patterns (Motifs):</strong></p>
                {self._generate_motifs_list(motifs.get('motifs', []))}
                
                <p style="margin-top: 20px;"><strong>Anomalous Pattern (Discord):</strong></p>
                {self._generate_discord_info(motifs.get('discord'))}
                
                <div class="interpretation">
                    <strong>Interpretation:</strong> 
                    Motifs represent recurring equity curve patterns. Discords are unusual patterns that may indicate regime changes or rare events.
                </div>
            </div>
            
            <!-- Drawdown Clustering -->
            <div class="section">
                <h2>📉 Drawdown Shape Clustering</h2>
                {self._generate_drawdown_clustering_info(dd_clusters)}
                <div class="interpretation">
                    <strong>Interpretation:</strong> 
                    Similar drawdown shapes are clustered together. Understanding drawdown patterns helps with risk management and position sizing.
                </div>
            </div>
            
            <!-- Raw JSON Data -->
            <div class="section">
                <h2>📄 Raw Data (JSON)</h2>
                <details>
                    <summary style="cursor: pointer; font-weight: 600; padding: 10px; background: white; border-radius: 5px;">
                        Click to expand full JSON report
                    </summary>
                    <div class="code-block">
                        <pre>{json.dumps(mc_report, indent=2)}</pre>
                    </div>
                </details>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Deep Backtesting Monte Carlo Pattern Analysis System</p>
            <p>Powered by world-class trading analytics and data science</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
        
    def _classify_sharpe(self, sharpe: float) -> str:
        """Classify Sharpe ratio"""
        if sharpe >= 2.0:
            return "good"
        elif sharpe >= 1.0:
            return "neutral"
        else:
            return "bad"
            
    def _classify_drawdown(self, dd: float) -> str:
        """Classify drawdown"""
        if dd <= 0.10:
            return "good"
        elif dd <= 0.20:
            return "neutral"
        else:
            return "bad"
            
    def _classify_uplift(self, uplift: float) -> str:
        """Classify leverageability uplift"""
        if uplift >= 0.2:
            return "good"
        elif uplift >= 0.0:
            return "neutral"
        else:
            return "bad"
            
    def _interpret_mc_results(self, base_sharpe: float, mc_mean: float, mc_p05: float) -> str:
        """Interpret MC results"""
        if base_sharpe > mc_mean:
            return "Base strategy outperforms MC mean, suggesting skill beyond luck."
        elif base_sharpe > mc_p05:
            return "Base strategy is within normal MC range (above 5th percentile)."
        else:
            return "⚠️ Base strategy underperforms MC simulations - possible overfitting or unfavorable sample."
            
    def _interpret_hour_effect(self, p_value: float) -> str:
        """Interpret hour-of-day effect"""
        if p_value < 0.01:
            return "Strong evidence of hour-of-day effect (p < 0.01). Time-based filtering recommended."
        elif p_value < 0.05:
            return "Moderate evidence of hour-of-day effect (p < 0.05). Consider time filtering."
        else:
            return "No significant hour-of-day effect detected. Time-based filtering may not improve performance."
            
    def _interpret_leverageability(self, uplift: float, frac_positive: float) -> str:
        """Interpret leverageability"""
        if uplift > 0.2 and frac_positive > 0.7:
            return "✅ Strong leverageability - hour filtering and leverage adjustment likely beneficial."
        elif uplift > 0.0 and frac_positive > 0.5:
            return "Moderate leverageability - hour filtering may provide some benefit."
        else:
            return "⚠️ Low leverageability - hour filtering unlikely to improve performance."
            
    def _interpret_runs_test(self, z: float, p_value: float) -> str:
        """Interpret runs test"""
        if p_value < 0.05:
            if z > 0:
                return "⚠️ Significantly more runs than expected - possible mean reversion or choppy behavior."
            else:
                return "⚠️ Significantly fewer runs than expected - possible trend following or clustering of wins/losses."
        else:
            return "Trade outcomes appear random (no significant pattern in win/loss sequences)."
            
    def _generate_hour_table(self, table: List[Dict]) -> str:
        """Generate HTML table for hour-of-day data"""
        if not table:
            return "<p>No hour data available.</p>"
            
        html = "<table><thead><tr><th>Hour</th><th>Mean Return</th><th>Std Dev</th><th>Count</th></tr></thead><tbody>"
        
        for row in sorted(table, key=lambda x: x.get('hour', 0)):
            hour = row.get('hour', 0)
            mean = row.get('mean', 0)
            std = row.get('std', 0)
            count = row.get('count', 0)
            
            color_class = "good" if mean > 0 else "bad" if mean < 0 else "neutral"
            
            html += f"""
            <tr>
                <td>{hour:02d}:00</td>
                <td class="{color_class}">{mean:.6f}</td>
                <td>{std:.6f}</td>
                <td>{count}</td>
            </tr>
            """
            
        html += "</tbody></table>"
        return html
        
    def _generate_motifs_list(self, motifs: List[Dict]) -> str:
        """Generate HTML for motifs list"""
        if not motifs:
            return "<p>No recurring motifs detected.</p>"
            
        html = "<ul>"
        for i, motif in enumerate(motifs, 1):
            html += f"""
            <li>
                <strong>Motif {i}:</strong> 
                Starts at position {motif.get('start', 0)}, 
                length {motif.get('len', 0)}, 
                similarity score {motif.get('score', 0):.1f}
            </li>
            """
        html += "</ul>"
        return html
        
    def _generate_discord_info(self, discord: Optional[Dict]) -> str:
        """Generate HTML for discord info"""
        if discord is None:
            return "<p>No discord detected.</p>"
            
        return f"""
        <div class="badge badge-warning">
            Anomalous pattern at position {discord.get('start', 0)}, length {discord.get('len', 0)}
        </div>
        """
        
    def _generate_drawdown_clustering_info(self, dd_clusters: Dict) -> str:
        """Generate HTML for drawdown clustering"""
        if not dd_clusters or not dd_clusters.get('counts'):
            return "<p>Insufficient drawdown episodes for clustering.</p>"
            
        counts = dd_clusters.get('counts', {})
        k = dd_clusters.get('k', 0)
        
        html = f"<p><strong>Number of clusters:</strong> {k}</p>"
        html += "<p><strong>Cluster distribution:</strong></p><ul>"
        
        for cluster_id, count in sorted(counts.items()):
            html += f"<li>Cluster {cluster_id}: {count} episodes</li>"
            
        html += "</ul>"
        return html


def main():
    """Command-line interface for HTML report generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate HTML reports from MC pattern analysis JSON")
    parser.add_argument("json_file", type=str, help="MC pattern analysis JSON file")
    parser.add_argument("--output", type=str, help="Output HTML filename")
    parser.add_argument("--output-dir", type=str, default="monte_carlo_reports", help="Output directory")
    
    args = parser.parse_args()
    
    # Load JSON report
    with open(args.json_file, 'r') as f:
        mc_report = json.load(f)
        
    # Generate HTML
    generator = MCPatternsReportGenerator(output_dir=args.output_dir)
    output_path = generator.generate_html_report(mc_report, output_filename=args.output)
    
    print(f"HTML report generated: {output_path}")


if __name__ == "__main__":
    main()




