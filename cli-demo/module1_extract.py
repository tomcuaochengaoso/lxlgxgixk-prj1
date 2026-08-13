"""
Module 1 - Tiếp nhận & Trích xuất hồ sơ NGO
--------------------------------------------
Input : đoạn mô tả tổ chức dạng text tự do, lộn xộn.
Output: dict hồ sơ NGO đã chuẩn hoá, dùng làm input cho Module 2.

Đây là bản MOCK rule-based (regex + keyword mapping), không gọi API thật,
để demo chạy ổn định 100% khi trình bày. Kiến trúc để sẵn chỗ thay bằng
LLM extraction thật (xem hàm extract_with_llm ở cuối file, hiện chưa dùng).
Ví dụ NGO dùng trong data/ngo_profile_raw.txt khớp đúng ví dụ minh hoạ
trong proposal: nhà tạm lánh hỗ trợ nạn nhân bạo lực gia đình tại Hà Nội.
"""

import re

# Từ điển ánh xạ cụm từ tự do -> field taxonomy chuẩn hoá
# (khớp với field taxonomy đang dùng trong data/prospects.json)
FIELD_KEYWORDS = {
    "bạo lực gia đình": "bảo vệ phụ nữ và trẻ em",
    "nhà tạm lánh": "nhà tạm lánh",
    "tư vấn tâm lý": "tư vấn tâm lý",
    "hỗ trợ pháp lý": "hỗ trợ pháp lý",
}

# Từ điển chuẩn hoá tên tỉnh/vùng -> region taxonomy
REGION_KEYWORDS = {
    "hà nội": "hà nội",
    "đống đa": "hà nội",
}


def _extract_name(text: str) -> str:
    m = re.search(r"Tổ chức ([^,]+)", text)
    return m.group(1).strip() if m else "Không xác định"


def _extract_mission(text: str) -> str:
    m = re.search(r"Sứ mệnh của (?:tụi mình|chúng tôi) là ([^.]+)\.", text)
    return m.group(1).strip() if m else ""


def _extract_fields(text: str) -> list:
    low = text.lower()
    found = []
    for kw, field in FIELD_KEYWORDS.items():
        if kw in low and field not in found:
            found.append(field)
    return found


def _extract_regions(text: str) -> list:
    low = text.lower()
    found = []
    for kw, region in REGION_KEYWORDS.items():
        if kw in low and region not in found:
            found.append(region)
    return found


def _extract_budget(text: str):
    # bắt các mẫu dạng "100.000-150.000 USD" hoặc "100.000 - 150.000 USD"
    m = re.search(r"([\d.]+)\s*-\s*([\d.]+)\s*USD", text)
    if not m:
        return None, None
    lo = int(m.group(1).replace(".", ""))
    hi = int(m.group(2).replace(".", ""))
    return lo, hi


def extract_ngo_profile(raw_text: str) -> dict:
    """Trích xuất hồ sơ NGO có cấu trúc từ đoạn text tự do."""
    budget_min, budget_max = _extract_budget(raw_text)
    profile = {
        "name": _extract_name(raw_text),
        "mission": _extract_mission(raw_text),
        "fields": _extract_fields(raw_text),
        "regions": _extract_regions(raw_text),
        "budget_min": budget_min,
        "budget_max": budget_max,
        "source": "rule_based_extraction_v1",
    }
    return profile


def extract_with_llm(raw_text: str) -> dict:
    """
    CHỖ DÀNH SẴN cho bản nâng cấp thật: gọi LLM (Claude/GPT/Qwen...) để
    trích xuất hồ sơ NGO chính xác hơn rule-based, đặc biệt với các đoạn
    mô tả không theo mẫu câu cố định như bản demo này.
    Hiện chưa triển khai (out of scope cho bản CLI demo này — bản web
    trong index.html đã có tính năng này chạy thật qua Anthropic API).
    """
    raise NotImplementedError("Chưa cấu hình API key cho bản demo CLI này.")


if __name__ == "__main__":
    with open("data/ngo_profile_raw.txt", encoding="utf-8") as f:
        raw = f.read()
    profile = extract_ngo_profile(raw)
    import json
    print(json.dumps(profile, ensure_ascii=False, indent=2))
