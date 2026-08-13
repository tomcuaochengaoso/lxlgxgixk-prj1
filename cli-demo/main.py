"""
PATRON demo pipeline - chạy end-to-end Module 1 -> Module 2 -> Module 3.
Không cần API key, chạy 100% local/offline, an toàn khi demo trực tiếp.

Usage:
    python main.py
"""

import json

from module1_extract import extract_ngo_profile
from module2_score import rank_prospects
from module3_compose import human_review_gate, draft_outreach_letter


def main():
    print("=" * 70)
    print("PATRON - Autopilot AI Agent for NGO Fundraising | Demo Pipeline")
    print("=" * 70)

    # ---- Module 1: tiếp nhận & trích xuất hồ sơ NGO ----
    with open("data/ngo_profile_raw.txt", encoding="utf-8") as f:
        raw_text = f.read()
    ngo = extract_ngo_profile(raw_text)

    print("\n[Module 1] Hồ sơ NGO đã trích xuất:")
    print(json.dumps(ngo, ensure_ascii=False, indent=2))

    # ---- Module 2: chấm điểm & xếp hạng prospect ----
    with open("data/prospects.json", encoding="utf-8") as f:
        prospects = json.load(f)
    ranked = rank_prospects(ngo, prospects)

    print("\n[Module 2] Bảng xếp hạng prospect (Match Score):")
    print(f"{'Hạng':<5}{'Điểm':<8}{'Eligibility':<18}{'Tên quỹ'}")
    for i, r in enumerate(ranked, start=1):
        print(f"{i:<5}{r['match_score']:<8}{r['eligibility']:<18}{r['prospect_name']}")

    # In giải thích chi tiết cho Top 1
    top = ranked[0]
    print(f"\n[Module 2] Giải thích chi tiết cho Top 1 - {top['prospect_name']}:")
    for f_ in sorted(top["factors"], key=lambda x: x["contribution"], reverse=True):
        print(f"  - {f_['factor']:<20} score={f_['score']:<5} weight={f_['weight']:<5} "
              f"đóng góp={f_['contribution']} điểm")

    # ---- Module 3: cổng duyệt + soạn thư cho Top 2 ----
    print("\n[Module 3] Human-in-the-loop + soạn thư tiếp cận cho Top 2:")
    for r in ranked[:2]:
        approved = human_review_gate(r["prospect_name"], r["match_score"])
        if approved:
            letter = draft_outreach_letter(ngo, r["prospect_name"], r)
            print(f"\n--- Bản nháp thư cho {r['prospect_name']} (chờ người duyệt lần cuối) ---")
            print(letter)
        else:
            print(f"  -> Bỏ qua soạn thư, chờ người xem lại prospect này thủ công.\n")

    print("=" * 70)
    print("Kết thúc pipeline demo. Toàn bộ output ở trên chạy thật từ code,")
    print("không phải dữ liệu chèn tay - dùng để quay video demo / chụp màn hình.")
    print("=" * 70)


if __name__ == "__main__":
    main()
