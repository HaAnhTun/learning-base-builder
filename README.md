# Personal Learning Base Builder

Biến transcript khóa học Udemy thành kho kiến thức cá nhân (SQLite). Đặc tả: [docs/SPEC.md](docs/SPEC.md).

Ba hướng sử dụng (SPEC 2.0): xuất dữ liệu sạch cho NotebookLM, trích xuất từ vựng, trích xuất kiến thức.

Trạng thái: đăng nhập Udemy, tải transcript, Clean Dataset, xuất Markdown cho NotebookLM, trích xuất từ vựng và kiến thức bằng AI (Claude Code, subagent Haiku), duyệt kết quả, app flashcard `study/`.

## Cài đặt

Yêu cầu Python 3.10–3.14.

```bash
pip install -r requirements.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

Playwright chỉ cần cho lệnh `login` và dùng Chrome hoặc Edge đã cài sẵn trên máy — không cần `playwright install`.

## Lấy token Udemy

**Dùng Udemy Business** (`<công-ty>.udemy.com`): trước khi login, tạo `config.local.yaml` với

```yaml
udemy:
  base_url: https://<công-ty>.udemy.com
```

Token của portal Business khác token của www.udemy.com.

### Cách 1 — tự động (khuyên dùng)

```bash
python -m engine login
```

Một cửa sổ Chrome/Edge mở ra trang Udemy. Đăng nhập như bình thường (đăng nhập bằng mã gửi qua email hoạt động tốt; đăng nhập Google có thể bị chặn trong trình duyệt tự động). Khi đăng nhập xong, token được lưu vào `config.local.yaml` và cửa sổ tự đóng.

Profile trình duyệt được giữ ở `data/.auth/`, nên khi token hết hạn (quan sát được khoảng 28 ngày) thường chỉ cần chạy lại `login` mà không phải nhập lại.

### Cách 2 — thủ công

1. Đăng nhập Udemy trên Chrome.
2. Mở DevTools (F12) → tab **Application** → **Cookies** → `https://www.udemy.com`.
3. Copy giá trị của cookie `access_token`.
4. Sao chép `config.local.example.yaml` thành `config.local.yaml` và dán vào `access_token`.

Hoặc đặt biến môi trường `UDEMY_ACCESS_TOKEN` (ghi đè giá trị trong file).

> `access_token` có toàn quyền với tài khoản Udemy của bạn. Không commit `config.local.yaml`, không chia sẻ token.

## Sử dụng

```bash
python -m engine fetch                         # liệt kê khóa học đã đăng ký
python -m engine fetch <url|slug|id>           # tải caption tiếng Anh rồi import
python -m engine fetch <url> --lang en,vi      # nhiều ngôn ngữ; --lang all = tất cả
python -m engine import data/input/<khóa>      # import file .vtt/.txt/.md tự đặt (tự làm sạch)
python -m engine clean <slug> [--force]        # làm sạch lại
python -m engine export notebooklm <slug>      # Markdown cho NotebookLM (--by chapter|course|lesson)
python -m engine stats
```

Trong Claude Code: `/learning-base-builder fetch <url>` …

File tải về nằm ở `data/input/<slug>/<locale>/NNN-<tên-bài>.vtt`, mỗi thư mục ngôn ngữ có `_manifest.json` riêng.
Chỉ ngôn ngữ trong `--lang` (mặc định `en`) được tải; thư mục ngôn ngữ khác không bị đụng tới.

File tự đặt: `data/input/<khóa>/<lang>/bai-01.vtt` (hoặc đặt phẳng trong `data/input/<khóa>/`).
Chạy lại `fetch`/`import` không tạo bản ghi trùng.

Dữ liệu: `data/input` (raw, không bao giờ sửa) → `data/clean` (Clean Dataset JSON) → `data/export` (Markdown/JSON/CSV).
Upload các file trong `data/export/notebooklm/<slug>/<lang>/` lên NotebookLM (Gemini Notebook).

Chỉ dùng cho khóa học bạn đã đăng ký, phục vụ học tập cá nhân.

## Trích xuất từ vựng và kiến thức (AI, trong Claude Code)

Trong Claude Code: `/learning-base-builder vocab evaluate <slug>`, `/learning-base-builder vocab enrich <slug>` (dịch định nghĩa, câu ví dụ, từ loại cho danh sách học), `/learning-base-builder knowledge extract <slug>` và `/learning-base-builder knowledge enrich <slug>` (mức quan trọng, câu hỏi gợi nhớ, dịch lại tự nhiên) — skill tạo task, giao cho subagent Haiku, rồi kiểm tra và lưu kết quả. Xuất file:

```bash
python -m engine vocab candidates <slug>       # trích ứng viên (không AI)
python -m engine vocab export <slug>           # data/export/vocabulary/<slug>/: .csv (đầy đủ), .json/.md (danh sách học: quan trọng ≥ 70)
python -m engine knowledge export <slug>       # data/export/knowledge/<slug>/knowledge.json, .md
python -m engine review list <slug> --mode vocab   # các mục cần duyệt
```

## Học bằng flashcard

Mở `study/index.html` bằng trình duyệt, chọn `vocabulary.json` và/hoặc `knowledge.json`. Space để lật thẻ, → đã nhớ, ← chưa nhớ. Tiến độ lưu trong trình duyệt.

## Test

```bash
python -m pytest
```
