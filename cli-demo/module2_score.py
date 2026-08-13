"""
Module 2 - Chấm điểm & Xếp hạng (Match Score)
-----------------------------------------------
Input : hồ sơ NGO (từ Module 1) + danh sách prospect (data/prospects.json).
Output: danh sách prospect đã chấm điểm, xếp hạng, kèm giải thích từng
        yếu tố (factor-level explanation) -> input cho Module 3.

Trọng số đúng bảng 3.2 trong proposal AI Challenge 2026 (7 yếu tố, tổng 100%):
  - Khớp lĩnh vực                30%
  - Khớp quy mô ngân sách         15%
  - Khớp địa bàn                  15%
  - Điều kiện & tư cách pháp lý   15%
  - Thời điểm & hạn nộp           10%
  - Đà quyên góp & CSR            10%
  - Độ hào phóng lịch sử           5%
"""

from datetime import date

WEIGHTS = {
    "field_match": 0.30,
    "amount_fit": 0.15,
    "geo_fit": 0.15,
    "eligibility": 0.15,
    "deadline_readiness": 0.10,
    "signal": 0.10,
    "generosity": 0.05,
}

ELIGIBILITY_SCORE = {"eligible": 1.0, "review": 0.5, "ineligible": 0.0}

TODAY = date(2026, 8, 12)  # ngày tham chiếu cho demo, khớp ngày hiện tại của team
MIN_PREP_DAYS = 14         # thời gian chuẩn bị tối thiểu để nộp hồ sơ


def _field_match(ngo_fields, prospect_fields) -> float:
    if not ngo_fields or not prospect_fields:
        return 0.0
    overlap = set(f.lower() for f in ngo_fields) & set(f.lower() for f in prospect_fields)
    return round(len(overlap) / len(set(prospect_fields)), 2)


def _amount_fit(ngo_min, ngo_max, p_min, p_max) -> float:
    if ngo_min is None or p_min is None:
        return 0.5  # thiếu dữ liệu -> giá trị trung tính, không phạt là 0
    # điểm 1.0 nếu hai khoảng giao nhau đáng kể, giảm dần nếu lệch xa
    overlap = min(ngo_max, p_max) - max(ngo_min, p_min)
    if overlap >= 0:
        return 1.0
    gap = abs(overlap)
    span = max(ngo_max - ngo_min, p_max - p_min, 1)
    return round(max(0.0, 1 - gap / span), 2)


def _geo_fit(ngo_regions, prospect_regions) -> float:
    if not ngo_regions or not prospect_regions:
        return 0.5
    p_regions = set(r.lower() for r in prospect_regions)
    if "toàn quốc" in p_regions:
        return 1.0
    overlap = set(r.lower() for r in ngo_regions) & p_regions
    return 1.0 if overlap else 0.0


def _deadline_readiness(deadline_str) -> float:
    if not deadline_str:
        return 0.5  # không có hạn cố định -> trung tính
    y, m, d = map(int, deadline_str.split("-"))
    days_left = (date(y, m, d) - TODAY).days
    if days_left < MIN_PREP_DAYS:
        return 0.0
    if days_left >= 60:
        return 1.0
    return round((days_left - MIN_PREP_DAYS) / (60 - MIN_PREP_DAYS), 2)


def _signal(days_ago: int) -> float:
    if days_ago <= 30:
        return 1.0
    if days_ago >= 120:
        return 0.0
    return round(1 - (days_ago - 30) / 90, 2)


def score_prospect(ngo: dict, prospect: dict) -> dict:
    factors = {
        "field_match": _field_match(ngo.get("fields"), prospect["fields"]),
        "amount_fit": _amount_fit(
            ngo.get("budget_min"), ngo.get("budget_max"),
            prospect["amount_min"], prospect["amount_max"],
        ),
        "geo_fit": _geo_fit(ngo.get("regions"), prospect["regions"]),
        "eligibility": ELIGIBILITY_SCORE.get(prospect.get("eligibility"), 0.5),
        "deadline_readiness": _deadline_readiness(prospect.get("deadline")),
        "signal": _signal(prospect.get("signal_days", 999)),
        "generosity": (prospect.get("generosity", 50)) / 100,
    }

    total = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    total_100 = round(total * 100, 1)

    explanation = []
    for k, v in factors.items():
        contribution = round(v * WEIGHTS[k] * 100, 1)
        explanation.append({
            "factor": k,
            "score": v,
            "weight": WEIGHTS[k],
            "contribution": contribution,
        })

    raw_eligibility = prospect.get("eligibility", "review")
    if raw_eligibility == "ineligible":
        eligibility_label = "INELIGIBLE"
    elif raw_eligibility == "review" or factors["geo_fit"] == 0 or factors["field_match"] == 0:
        eligibility_label = "REVIEW_REQUIRED"
    else:
        eligibility_label = "ELIGIBLE"

    return {
        "prospect_id": prospect["id"],
        "prospect_name": prospect["name"],
        "match_score": total_100,
        "factors": explanation,
        "eligibility": eligibility_label,
    }


def rank_prospects(ngo: dict, prospects: list) -> list:
    scored = [score_prospect(ngo, p) for p in prospects]
    return sorted(scored, key=lambda x: x["match_score"], reverse=True)


if __name__ == "__main__":
    import json
    from module1_extract import extract_ngo_profile

    with open("data/ngo_profile_raw.txt", encoding="utf-8") as f:
        ngo = extract_ngo_profile(f.read())
    with open("data/prospects.json", encoding="utf-8") as f:
        prospects = json.load(f)

    ranked = rank_prospects(ngo, prospects)
    for r in ranked:
        print(f"{r['match_score']:>5} | {r['eligibility']:<15} | {r['prospect_name']}")
