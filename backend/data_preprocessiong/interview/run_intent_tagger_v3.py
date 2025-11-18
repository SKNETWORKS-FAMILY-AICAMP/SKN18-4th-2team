#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intent tagger (v3) with updated priority:
1) motivation_fit  (목표/지원동기/선호/희망부서 등)
2) self_reflection (후회/장단점/자기소개/자신있는 등)
3) criteria_evaluation (중요하게 생각/기준/평가척도 등)
4) stakeholder_comm (협업/갈등/커뮤니케이션/조율 등)
5) behavioral_star  (경험/사례/극복/성과/결과/어떻게 해결 등)
6) procedure_method (어떻게/방법/절차/프로세스/how to 등)
7) mechanism_reason (왜/이유/원인/소감/원리/how.*work 등)
8) compare_tradeoff (비교/장단점/중~더/vs/trade-off 등)
9) evidence_metric  (지표/수치/실험/검증/AUC/F1 등)
10) leadership_ownership (리더십/오너십/주도/책임/권한 등)
11) creativity_ideation  (창의/개선/아이디어/개선 방안/정책 제안 등)
12) root_cause (원인 분석/재발 방지/디버그/트러블슈팅 등)
13) ethics_compliance (윤리/준법/IRB/GDPR/HIPAA/개인정보/보안정책 등)
14) application_transfer (적용/현장/전이/실무 적용/use case 등)
15) estimation_planning (대략/예상/일정/계획/스케줄/리소스 계획/목표 기간 등)
16) cost_resource (비용/ROI/예산/원가/인력/장비/효율/가성비 등)

Usage:
  python run_intent_tagger_v3.py --input /path/to/merged_experienced_with_intent.csv --outdir /path/to/out
Creates:
  - intent_eval_report_v3.csv (full rows + pred)
  - intent_mismatches_v3.csv  (gold != pred)
"""

import argparse
import os
import re
import sys
import pandas as pd

# ------------------ Regex library ------------------
# Keep raw strings; compile with re.IGNORECASE
P_SELF   = re.compile(r"(후회|강점|약점|장점|단점|자기\s*소개|스스로|자신\s*있는|수준|숙련|레벨|대표적(인)?\s*프로젝트)")
P_MOTIV  = re.compile(r"(목표|지원\s*동기|왜\s*우리|가고\s*싶은\s*회사|적합|우선순위|중점적으로\s*보|선호|희망\s*부서|선호\s*부서)")
P_COMM   = re.compile(r"(협업|갈등|소통|설득|보고|피드백|커뮤니케이션|이해관계자|조율)")
P_BEHAV  = re.compile(r"(경험|사례|극복|성과|결과|\bstar\b|어떻게\s*(해결|대응))")
P_COMPARE= re.compile(r"(장단점|대안|비교|\\bvs\\b|trade[\\s-]?off|(.+)\\s*와\\s*(.+)\\s*중(에)?\\s*(어느|더))")
P_EVID   = re.compile(r"(지표|수치|근거|증거|성능|정확도|정밀도|재현율|f1|auc|실험|검증|validation|통계|p[- ]?value|신뢰\\s*구간)")
P_HOW    = re.compile(r"(어떻게|방법(론)?|절차|프로세스|순서|how\\s*to)")
P_WHY    = re.compile(r"(왜|이유|원인|배경|원리|how.*work|인과|causal|생각|소감)")
P_CRIT   = re.compile(r"(기준|평가\\s*척도|판단\\s*기준|선정\\s*기준|품질\\s*기준|중요하게\\s*생각)")
P_EDGE   = re.compile(r"(한계|예외|엣지|edge\\s*case|실패(\\s*모드)?|오류|리스크|안전)")
P_APP    = re.compile(r"(적용|현장|전이|다른\\s*(상황|산업)|use\\s*case|실무.*적용)")
P_EST    = re.compile(r"(대략|얼마나|예상|추정|일정|계획|납기|스케줄|리소스\\s*계획|목표\\s*기간)")
P_COST   = re.compile(r"(비용|roi|예산|원가|인력|장비|효율|투입\\s*대비|가성비)")
P_LEAD   = re.compile(r"(리더십|오너십|주도|책임|권한|위임|결정|주도적)")
P_CREAT  = re.compile(r"(새로운|혁신|개선|아이디어|창의(성)?|브레인스토밍|개선\\s*방안|정책\\s*제안)")
P_ROOT   = re.compile(r"(원인\\s*분석|근본\\s*원인|재발\\s*방지|트러블슈팅|디버그|문제\\s*해결)")
P_ETH    = re.compile(r"(윤리|준법|컴플라이언스|irb|gdpr|hipaa|개인정보|보안\\s*정책)")

# Ordered intent rules (label, regex)
INTENT_RULES = [
    ("motivation_fit",    P_MOTIV),
    ("self_reflection",   P_SELF),
    ("criteria_evaluation", P_CRIT),
    ("stakeholder_comm",  P_COMM),
    ("behavioral_star",   P_BEHAV),
    ("procedure_method",  P_HOW),
    ("mechanism_reason",  P_WHY),
    ("compare_tradeoff",  P_COMPARE),
    ("evidence_metric",   P_EVID),
    ("leadership_ownership", P_LEAD),
    ("creativity_ideation",  P_CREAT),
    ("root_cause",        P_ROOT),
    ("ethics_compliance", P_ETH),
    ("application_transfer", P_APP),
    ("estimation_planning",  P_EST),
    ("cost_resource",     P_COST),
]

FALLBACK = "mechanism_reason"

def tag_one(text: str) -> str:
    """Return first matching intent label, or FALLBACK if none."""
    if not isinstance(text, str):
        return FALLBACK
    q = text.strip().lower()
    for label, rx in INTENT_RULES:
        if rx.search(q):
            return label
    return FALLBACK

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV with at least 'question' column")
    ap.add_argument("--outdir", default=".", help="Directory to write reports")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.input, encoding="utf-8-sig")

    # Column normalization
    # Prefer 'question' if present; otherwise try fallbacks
    if "question" not in df.columns:
        # try question_norm
        if "question_norm" in df.columns:
            df["question"] = df["question_norm"]
        else:
            raise ValueError("No 'question' or 'question_norm' column found.")

    # Tag question intents
    df["question_intent"] = df["question"].apply(tag_one)

    # Save output
    output_path = os.path.join(args.outdir, "merged_experienced_with_question_intent.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Total rows processed: {len(df)}")
    print(f"Output saved to: {output_path}")
    
    # Display intent distribution
    print("\nQuestion Intent Distribution:")
    intent_counts = df["question_intent"].value_counts()
    for intent, count in intent_counts.items():
        print(f"  {intent}: {count} ({count/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()
