# PATRON — Trợ lý AI tìm & kết nối nguồn tài trợ cho tổ chức xã hội

Bài dự thi **AI Challenge 2026 "GENERATION AI: NEW MINDSET for ECON & BIZ"** — Trường Đại học Ngoại thương (FTU), trong khuôn khổ Hội thảo Khoa học Quốc gia AI4Econ&Biz 2026.

PATRON tự động hoá quy trình nghiên cứu gây quỹ cho NGO: tiếp nhận hồ sơ tổ chức, tìm & chấm điểm mức độ phù hợp với các quỹ/nhà tài trợ, và soạn sẵn thư tiếp cận — con người luôn duyệt trước khi gửi bất cứ thư nào.

## Repo có 2 bản demo

## Chạy AI bằng API của bạn (không cần mở Claude)

Web app bây giờ đi qua `server.py`, một proxy local rất nhỏ. API key chỉ nằm trong `.env`, nên không bị lộ trong `index.html`.

```powershell
cd C:\Users\Admin\OneDrive\Desktop\meo
Copy-Item .env.example .env
# Mở .env, điền AI_BASE_URL, AI_API_KEY và AI_MODEL của bạn
python server.py
```

Sau đó mở **http://127.0.0.1:8000**. Đừng double-click `index.html`, vì khi đó browser không kết nối được với server local.

Mặc định dùng chuẩn **OpenAI-compatible Chat Completions**: OpenAI, OpenRouter, Groq, DeepSeek và nhiều dịch vụ khác. Nếu dùng Claude API native, đặt `AI_PROVIDER=anthropic` và `AI_BASE_URL=https://api.anthropic.com` trong `.env`.

Hai tính năng trích xuất hồ sơ và soạn thư chạy với mọi API tương thích. Nút tìm quỹ trên web còn cần nhà cung cấp có công cụ web search: dùng OpenAI thì đặt `AI_SEARCH_MODE=openai_responses`; dùng Claude thì đặt `AI_PROVIDER=anthropic`. Các API chỉ sinh văn bản không thể tự tìm web thật chỉ với một API key.

### 1. `index.html` — Web app (bản chính, dùng để demo/trình bày)

Single-file HTML/CSS/JS, **không cần cài đặt gì** — mở trực tiếp bằng trình duyệt là chạy được.

- **Hồ sơ NGO** (mục 01): điền tay hoặc dán mô tả tự do để AI trích xuất.
- **Trọng số chấm điểm** (mục 02): 7 yếu tố kéo-thả điều chỉnh được, mặc định khớp đúng bảng 3.2 trong proposal (Khớp lĩnh vực 30% · Khớp quy mô 15% · Khớp địa bàn 15% · Điều kiện & tư cách pháp lý 15% · Thời điểm & hạn nộp 10% · Đà quyên góp & CSR 10% · Độ hào phóng lịch sử 5%).
- **Danh sách quỹ tài trợ** (mục 03): 8 quỹ mẫu có sẵn, có thể xoá/sửa/thêm tay, hoặc bấm **"Tìm quỹ mới trên web"** để AI tự search + đọc nguồn thật.
- **Kết quả xếp hạng** (mục 04): điểm phù hợp 0–100 kèm giải thích theo từng yếu tố, và nút soạn thư tiếp cận (bản mẫu hoặc AI soạn lại).

**Chạy thử:** chạy `python server.py` và mở `http://127.0.0.1:8000`. Không mở `index.html` bằng double-click hoặc `python -m http.server`, vì các cách đó không chạy proxy giữ API key.

**Lưu ý bảo mật:** 3 nút AI gọi tới proxy trong `server.py`, không gọi thẳng từ trình duyệt. Đừng commit file `.env` và đừng dán API key vào `index.html`.

Toàn bộ phần còn lại (form hồ sơ, chấm điểm rule-based, bảng quỹ, thêm/xoá tay, thư mẫu) chạy 100% bằng JavaScript thuần, hoạt động bình thường ở mọi nơi kể cả khi host public.

Khi host public, cần deploy proxy tương đương `server.py` (Cloudflare Worker/Vercel Function/FastAPI) cùng domain hoặc đổi URL API trong `index.html` sang URL proxy đó. GitHub Pages chỉ host file tĩnh nên không thể tự giữ API key.

### 2. `cli-demo/` — Pipeline Python 3-module (bản kỹ thuật, tách module theo người)

Không cần API key, chạy 100% local/offline.

```bash
cd cli-demo
python3 main.py
```

- `module1_extract.py` — trích xuất hồ sơ NGO từ text tự do (rule-based, regex).
- `module2_score.py` — chấm điểm & xếp hạng 7 yếu tố có trọng số, breakdown giải thích rõ.
- `module3_compose.py` — cổng duyệt human-in-the-loop + soạn thư tiếp cận.
- `main.py` — chạy end-to-end cả 3 module, in kết quả ra terminal.
- `data/` — hồ sơ NGO mẫu + 8 quỹ tài trợ mẫu, đồng bộ với dữ liệu trong `index.html`.

Bản này dùng để minh hoạ kiến trúc "tách module theo người phụ trách" và chạy được không cần trình duyệt/internet — hợp cho phần chấm "chiều sâu kỹ thuật".

## Chạy web app qua GitHub Pages

1. Push repo này lên GitHub.
2. Vào **Settings → Pages**, chọn branch `main`, thư mục `/ (root)`.
3. GitHub sẽ serve `index.html` tại `https://<username>.github.io/<repo>/`.
4. Bản GitHub Pages chỉ chạy phần giao diện/rule-based. Muốn bật AI, deploy thêm proxy backend và cấu hình URL API phù hợp.

## Hướng nâng cấp lên bản production

- Deploy `server.py` hoặc chuyển nó thành Cloudflare Worker / Vercel Function / FastAPI để dùng cho nhiều người; giữ API key ở biến môi trường của nền tảng deploy.
- Thay dữ liệu quỹ tài trợ mẫu bằng nguồn thật (đã có sẵn nút "Tìm quỹ mới trên web" làm nền, chỉ cần chạy qua backend ổn định hơn thay vì gọi trực tiếp).
- `module1_extract.py` có sẵn hàm `extract_with_llm()` (hiện raise `NotImplementedError`) — chỗ cắm LLM extraction thật cho bản CLI nếu cần.
- Thêm bước lưu trạng thái duyệt/loại prospect (hiện tại `human_review_gate()` chỉ mô phỏng trong bộ nhớ) để vòng phản hồi thật sự tinh chỉnh được trọng số theo thời gian, đúng như mô tả trong proposal.

## Lưu ý liêm chính học thuật

Toàn bộ dữ liệu quỹ tài trợ trong `index.html` và `cli-demo/data/prospects.json` là **dữ liệu minh hoạ** (một số dựa lỏng lẻo trên tổ chức có thật như VinIF, USAID, UNDP, ActionAid — có ghi chú rõ "minh hoạ"/"giả lập"), không phải kết quả scraping/web search thật, trừ các quỹ được gắn nhãn **"AI"** trong bảng — những quỹ đó do tính năng "Tìm quỹ mới trên web" tìm thật qua Anthropic web search tool, có link nguồn kèm theo để tự kiểm chứng.

## License

MIT — xem file [LICENSE](./LICENSE).
