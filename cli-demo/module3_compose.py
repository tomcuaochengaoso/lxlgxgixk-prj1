"""
Module 3 - Soạn thư tiếp cận & Human-in-the-loop
--------------------------------------------------
Input : hồ sơ NGO + kết quả chấm điểm 1 prospect (từ Module 2).
Output: bản nháp thư tiếp cận (tiếng Việt, formal vừa phải), CHỈ được coi
        là "sẵn sàng gửi" sau khi có approve từ người dùng (cổng duyệt).

Không tự động gửi bất cứ thư nào - đây là điểm bắt buộc theo đề bài
(con người quyết định ở mọi bước quan trọng).
"""

REASON_TEXT = {
    "field_match": "lĩnh vực hoạt động của quỹ khớp cao với lĩnh vực của tổ chức",
    "amount_fit": "mức tài trợ điển hình của quỹ phù hợp với ngân sách đang cần",
    "geo_fit": "địa bàn tài trợ của quỹ bao phủ khu vực tổ chức đang hoạt động",
    "eligibility": "tổ chức đủ điều kiện & tư cách pháp lý theo tiêu chí của quỹ",
    "deadline_readiness": "còn đủ thời gian chuẩn bị hồ sơ trước hạn nộp",
    "signal": "quỹ vừa có tín hiệu quan tâm/hoạt động CSR gần đây liên quan",
    "generosity": "quỹ có lịch sử giải ngân đều đặn và hào phóng",
}


def build_explanation_summary(score_result: dict, top_n: int = 3) -> str:
    """Chuyển factor scores thành 2-3 lý do bằng ngôn ngữ tự nhiên."""
    top_factors = sorted(score_result["factors"], key=lambda f: f["contribution"], reverse=True)[:top_n]
    reasons = [REASON_TEXT.get(f["factor"], f["factor"]) for f in top_factors if f["score"] > 0]
    return "; ".join(reasons) if reasons else "một số yếu tố phù hợp cơ bản"


def draft_outreach_letter(ngo: dict, prospect_name: str, score_result: dict) -> str:
    reasons = build_explanation_summary(score_result)
    letter = f"""Kính gửi Ban Quản lý {prospect_name},

Tôi là đại diện {ngo['name']}. Chúng tôi đang triển khai các chương trình
vận hành nhà tạm lánh, tư vấn tâm lý và hỗ trợ pháp lý cho phụ nữ và trẻ em
là nạn nhân bạo lực gia đình tại địa bàn hoạt động của tổ chức.

Qua rà soát, chúng tôi nhận thấy {reasons}, nên mạnh dạn kết nối để tìm
hiểu khả năng hợp tác. Ngân sách dự kiến cho hạng mục liên quan nằm trong
khoảng {ngo.get('budget_min', 0):,} - {ngo.get('budget_max', 0):,} USD.

Rất mong được trao đổi thêm cùng quý quỹ trong thời gian tới, qua email
hoặc một buổi gặp trực tuyến ngắn.

Trân trọng,
{ngo['name']}
(Điểm phù hợp tham khảo nội bộ: {score_result['match_score']}/100 -
đây KHÔNG phải xác suất được duyệt, chỉ là chỉ số ưu tiên nội bộ.)
"""
    return letter


def human_review_gate(prospect_name: str, match_score: float, auto_approve_threshold: float = 70.0) -> bool:
    """
    Cổng duyệt bắt buộc trước khi coi thư là 'sẵn sàng gửi'.
    Trong demo: mô phỏng người dùng duyệt các prospect có điểm >= ngưỡng.
    Trong hệ thống thật: đây phải là một hành động duyệt thủ công thực sự,
    không bao giờ tự động gửi thư mà không có người xác nhận.
    """
    decision = match_score >= auto_approve_threshold
    status = "DUYỆT (mô phỏng)" if decision else "CHỜ NGƯỜI XEM LẠI"
    print(f"  [Human-in-the-loop] {prospect_name}: {status} (score={match_score})")
    return decision


if __name__ == "__main__":
    import json
    from module1_extract import extract_ngo_profile
    from module2_score import rank_prospects

    with open("data/ngo_profile_raw.txt", encoding="utf-8") as f:
        ngo = extract_ngo_profile(f.read())
    with open("data/prospects.json", encoding="utf-8") as f:
        prospects = json.load(f)

    ranked = rank_prospects(ngo, prospects)
    top = ranked[0]
    approved = human_review_gate(top["prospect_name"], top["match_score"])
    if approved:
        print("\n--- BẢN NHÁP THƯ TIẾP CẬN (chờ người duyệt lần cuối trước khi gửi) ---\n")
        print(draft_outreach_letter(ngo, top["prospect_name"], top))
