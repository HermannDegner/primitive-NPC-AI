#!/usr/bin/env python3
"""
SSD Theory Compliance Checker - SSD理論準拠チェッカー

🔗 基礎理論リポジトリ: https://github.com/HermannDegner/Structural-Subjectivity-Dynamics

プロジェクト全体のSSD理論準拠状況を検証し、レポートを生成します。
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from dataclasses import dataclass

from ssd_theory_reference import get_ssd_reference, validate_against_ssd_theory

@dataclass
class ComplianceReport:
    """SSD理論準拠レポート"""
    file_path: str
    compliance_score: float
    found_concepts: List[str] 
    missing_concepts: List[str]
    theoretical_gaps: List[str]
    recommendations: List[str]
    kappa_memory_implementation: Dict[str, Any]

class SSDComplianceChecker:
    """SSD理論準拠チェッカー"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ssd_ref = get_ssd_reference()
        
        # SSD理論必須概念
        self.required_concepts = {
            "coherence_inertia_kappa": r"(κ|kappa|coherence[_\s]*inertia)",
            "memory_system": r"(記憶|memory|experience|learning)",
            "meaning_pressure": r"(意味圧|meaning[_\s]*pressure|p\(t\))",
            "alignment": r"(整合|alignment)",
            "leap": r"(跳躍|leap|jump)",
            "four_layer": r"(四層|four[_\s]*layer|物理層|基層|中核層|上層)",
            "structure": r"(構造|structure)",
            "subjective": r"(主観|subjective)",
            "ssd_theory": r"(SSD|Structure[_\s]*Subjective[_\s]*Dynamics|構造主観力学)"
        }
        
        # 重要ファイルパターン
        self.important_files = [
            "**/*.py",
            "**/*.md", 
            "**/*.txt"
        ]
        
        # 除外パターン
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            "*.pyc",
            "*.log"
        ]
    
    def scan_file_for_concepts(self, file_path: Path) -> Dict[str, Any]:
        """ファイル内のSSD概念をスキャン"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e), "concepts": {}}
        
        found_concepts = {}
        for concept_name, pattern in self.required_concepts.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_concepts[concept_name] = len(matches) > 0
        
        # 特別チェック: κ=記憶システム
        kappa_memory_check = self.ssd_ref.check_kappa_memory_implementation(content)
        
        return {
            "concepts": found_concepts,
            "content_length": len(content),
            "kappa_memory": kappa_memory_check,
            "ssd_references": self._count_ssd_references(content)
        }
    
    def _count_ssd_references(self, content: str) -> Dict[str, int]:
        """SSD理論参照の数をカウント"""
        references = {
            "github_repo_mentions": len(re.findall(r"HermannDegner/Structural-Subjectivity-Dynamics", content)),
            "theory_mentions": len(re.findall(r"SSD|Structure\s*Subjective\s*Dynamics|構造主観力学", content, re.IGNORECASE)),
            "kappa_memory_mentions": len(re.findall(r"κ.*記憶|kappa.*memory|整合慣性.*記憶", content, re.IGNORECASE))
        }
        return references
    
    def generate_file_report(self, file_path: Path, scan_results: Dict[str, Any]) -> ComplianceReport:
        """ファイル別コンプライアンスレポートを生成"""
        
        concepts = scan_results.get("concepts", {})
        found_concepts = [name for name, found in concepts.items() if found]
        missing_concepts = [name for name, found in concepts.items() if not found]
        
        # コンプライアンススコア計算
        compliance_score = len(found_concepts) / len(self.required_concepts) if self.required_concepts else 0.0
        
        # 推奨事項生成
        recommendations = []
        if compliance_score < 0.5:
            recommendations.append(f"基礎理論リポジトリを参照してください: {self.ssd_ref.repo_url}")
            
        if "coherence_inertia_kappa" not in found_concepts:
            recommendations.append("整合慣性κの概念を実装してください")
            
        if "memory_system" not in found_concepts:
            recommendations.append("κ=記憶システムの理論的洞察を実装してください")
        
        # 理論的ギャップの特定
        gaps = []
        kappa_memory = scan_results.get("kappa_memory", {})
        if kappa_memory.get("theoretical_compliance", "LOW") == "LOW":
            gaps.append("整合慣性κ=記憶システムの実装が不十分")
        
        return ComplianceReport(
            file_path=str(file_path),
            compliance_score=compliance_score,
            found_concepts=found_concepts,
            missing_concepts=missing_concepts,
            theoretical_gaps=gaps,
            recommendations=recommendations,
            kappa_memory_implementation=kappa_memory
        )
    
    def scan_project(self) -> List[ComplianceReport]:
        """プロジェクト全体をスキャン"""
        
        reports = []
        
        # 重要ファイルを特定
        important_files = []
        for pattern in self.important_files:
            important_files.extend(self.project_root.glob(pattern))
        
        # 除外ファイルをフィルタ
        filtered_files = []
        for file_path in important_files:
            if file_path.is_file() and not any(exclude in str(file_path) for exclude in self.exclude_patterns):
                filtered_files.append(file_path)
        
        print(f"📁 スキャン対象ファイル数: {len(filtered_files)}")
        
        # 各ファイルをスキャン
        for file_path in filtered_files:
            print(f"🔍 スキャン中: {file_path.name}")
            
            scan_results = self.scan_file_for_concepts(file_path)
            if "error" not in scan_results:
                report = self.generate_file_report(file_path, scan_results)
                reports.append(report)
        
        return reports
    
    def generate_summary_report(self, reports: List[ComplianceReport]) -> Dict[str, Any]:
        """総合レポートを生成"""
        
        if not reports:
            return {"error": "レポートデータがありません"}
        
        # 統計計算
        total_files = len(reports)
        avg_compliance = sum(r.compliance_score for r in reports) / total_files
        
        high_compliance = [r for r in reports if r.compliance_score >= 0.8]
        medium_compliance = [r for r in reports if 0.5 <= r.compliance_score < 0.8]
        low_compliance = [r for r in reports if r.compliance_score < 0.5]
        
        # 最も重要な概念の普及率
        concept_coverage = {}
        for concept in self.required_concepts.keys():
            coverage = sum(1 for r in reports if concept in r.found_concepts) / total_files
            concept_coverage[concept] = coverage
        
        # 重要な発見
        key_findings = []
        
        # κ=記憶システムの実装状況
        kappa_implementations = [r.kappa_memory_implementation for r in reports if r.kappa_memory_implementation]
        high_kappa_impl = [k for k in kappa_implementations if k.get("theoretical_compliance") == "HIGH"]
        
        if len(high_kappa_impl) / total_files > 0.7:
            key_findings.append("✅ 整合慣性κ=記憶システムが適切に実装されています")
        else:
            key_findings.append("⚠️ 整合慣性κ=記憶システムの実装を改善する必要があります")
        
        # 基礎理論参照状況
        theory_refs = sum(1 for r in reports if "ssd_theory" in r.found_concepts)
        if theory_refs / total_files > 0.8:
            key_findings.append("✅ SSD基礎理論への参照が充実しています")
        else:
            key_findings.append("⚠️ SSD基礎理論への参照を増やしてください")
        
        return {
            "総ファイル数": total_files,
            "平均コンプライアンススコア": avg_compliance,
            "高コンプライアンス": len(high_compliance),
            "中コンプライアンス": len(medium_compliance), 
            "低コンプライアンス": len(low_compliance),
            "概念カバレッジ": concept_coverage,
            "主要発見": key_findings,
            "基礎理論リポジトリ": self.ssd_ref.repo_url,
            "推奨事項": [
                "定期的にSSD基礎理論リポジトリを確認してください",
                "整合慣性κ=記憶システムの概念を全ファイルで統一してください",
                "構造観照（テオーリア）の姿勢を保持してください"
            ]
        }
    
    def export_report(self, reports: List[ComplianceReport], summary: Dict[str, Any], 
                     output_file: str = "ssd_compliance_report.md") -> None:
        """レポートをMarkdown形式でエクスポート"""
        
        output_path = self.project_root / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# SSD理論準拠レポート\n\n")
            f.write(f"🔗 **基礎理論リポジトリ**: {self.ssd_ref.repo_url}\n\n")
            f.write(f"📅 **生成日時**: {self._get_current_datetime()}\n\n")
            
            # 総合統計
            f.write("## 📊 総合統計\n\n")
            f.write(f"- **総ファイル数**: {summary['総ファイル数']}\n")
            f.write(f"- **平均コンプライアンススコア**: {summary['平均コンプライアンススコア']:.2f}\n")
            f.write(f"- **高コンプライアンス** (≥80%): {summary['高コンプライアンス']}ファイル\n")
            f.write(f"- **中コンプライアンス** (50-80%): {summary['中コンプライアンス']}ファイル\n")
            f.write(f"- **低コンプライアンス** (<50%): {summary['低コンプライアンス']}ファイル\n\n")
            
            # 主要発見
            f.write("## 🔍 主要発見\n\n")
            for finding in summary["主要発見"]:
                f.write(f"- {finding}\n")
            f.write("\n")
            
            # 概念カバレッジ
            f.write("## 📈 SSD概念カバレッジ\n\n")
            for concept, coverage in summary["概念カバレッジ"].items():
                percentage = coverage * 100
                status = "✅" if coverage >= 0.7 else "⚠️" if coverage >= 0.4 else "❌"
                f.write(f"- **{concept}**: {percentage:.1f}% {status}\n")
            f.write("\n")
            
            # ファイル別詳細
            f.write("## 📋 ファイル別詳細\n\n")
            
            # 高コンプライアンスファイル
            high_files = [r for r in reports if r.compliance_score >= 0.8]
            if high_files:
                f.write("### ✅ 高コンプライアンスファイル (≥80%)\n\n")
                for report in sorted(high_files, key=lambda x: x.compliance_score, reverse=True):
                    f.write(f"- **{Path(report.file_path).name}**: {report.compliance_score:.1%}\n")
                f.write("\n")
            
            # 改善が必要なファイル
            low_files = [r for r in reports if r.compliance_score < 0.5]
            if low_files:
                f.write("### ⚠️ 改善が必要なファイル (<50%)\n\n")
                for report in sorted(low_files, key=lambda x: x.compliance_score):
                    f.write(f"- **{Path(report.file_path).name}**: {report.compliance_score:.1%}\n")
                    if report.recommendations:
                        for rec in report.recommendations[:2]:  # 主要な推奨事項のみ
                            f.write(f"  - 💡 {rec}\n")
                f.write("\n")
            
            # 推奨事項
            f.write("## 💡 推奨事項\n\n")
            for rec in summary["推奨事項"]:
                f.write(f"1. {rec}\n")
            f.write("\n")
            
            f.write("---\n")
            f.write("**このレポートは自動生成されました。定期的に実行してSSD理論準拠を維持してください。**\n")
        
        print(f"📄 レポートを出力しました: {output_path}")
    
    def _get_current_datetime(self) -> str:
        """現在日時を取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

def main():
    """メイン実行関数"""
    print("🔍 SSD理論準拠チェッカーを開始します...")
    
    # プロジェクトルートを取得
    project_root = Path(__file__).parent
    print(f"📁 プロジェクトルート: {project_root}")
    
    # チェッカーを初期化
    checker = SSDComplianceChecker(str(project_root))
    
    # プロジェクトをスキャン
    print("\n🔍 プロジェクトをスキャンしています...")
    reports = checker.scan_project()
    
    # 総合レポートを生成
    print("\n📊 総合レポートを生成しています...")
    summary = checker.generate_summary_report(reports)
    
    # レポートを表示
    print(f"\n📋 SSD理論準拠状況:")
    print(f"平均コンプライアンススコア: {summary['平均コンプライアンススコア']:.1%}")
    print(f"高コンプライアンスファイル: {summary['高コンプライアンス']}")
    print(f"改善が必要: {summary['低コンプライアンス']}")
    
    # レポートをエクスポート
    checker.export_report(reports, summary)
    
    print(f"\n🔗 基礎理論リポジトリ: {checker.ssd_ref.repo_url}")
    print("✅ SSD理論準拠チェック完了!")

if __name__ == "__main__":
    main()