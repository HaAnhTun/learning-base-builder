# Personal Learning Base Builder

Biến transcript khóa học Udemy thành kho kiến thức cá nhân (SQLite). Đặc tả: [docs/SPEC.md](docs/SPEC.md).

Hai hướng sử dụng: xuất Markdown sạch cho NotebookLM/LLM, và đóng gói khóa học (transcript, quiz, bài kiểm tra, tài liệu) thành Claude skill. Phần trích xuất từ vựng/kiến thức bằng AI đã chuyển vào [archive/](archive/README.md).

Trạng thái: đăng nhập Udemy, tải transcript + quiz + bài kiểm tra + tài liệu đính kèm, Clean Dataset, xuất Markdown cho NotebookLM, đóng gói skill. Toàn bộ chạy bằng Python, không cần AI.

## Cài đặt

Yêu cầu Python 3.10–3.14.

```bash
pip install -r requirements.txt
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
python -m engine fetch <url|slug|id>           # tải caption tiếng Anh + quiz + bài kiểm tra + tài liệu đính kèm, rồi import
python -m engine fetch <url> --lang en,vi      # nhiều ngôn ngữ; --lang all = tất cả
python -m engine import data/input/<khóa>      # import file .vtt/.txt/.md tự đặt (tự làm sạch)
python -m engine clean <slug> [--force]        # làm sạch lại
python -m engine export notebooklm <slug>      # Markdown cho NotebookLM (--by chapter|course|lesson)
python -m engine export skill <slug>           # Claude skill: data/export/skills/<slug>/ (chép vào .claude/skills/ hoặc ~/.claude/skills/)
python -m engine stats
```

Trong Claude Code: `/learning-base-builder fetch <url>` …

File tải về nằm ở `data/input/<slug>/<locale>/NNN-<tên-bài>.vtt`, mỗi thư mục ngôn ngữ có `_manifest.json` riêng. Quiz và bài kiểm tra ở `data/input/<slug>/quizzes/NN-<tên>.json` (câu hỏi gốc, đáp án, giải thích; chỉ mục `_quizzes.json`); tài liệu đính kèm ở `data/input/<slug>/materials/` (link ngoài chỉ được ghi lại, không mở).
Chỉ ngôn ngữ trong `--lang` (mặc định `en`) được tải; thư mục ngôn ngữ khác không bị đụng tới.

File tự đặt: `data/input/<khóa>/<lang>/bai-01.vtt` (hoặc đặt phẳng trong `data/input/<khóa>/`).
Chạy lại `fetch`/`import` không tạo bản ghi trùng.

Dữ liệu: `data/input` (raw, không bao giờ sửa) → `data/clean` (Clean Dataset JSON) → `data/export` (Markdown/JSON/CSV).
Upload các file trong `data/export/notebooklm/<slug>/<lang>/` lên NotebookLM (Gemini Notebook).

Chỉ dùng cho khóa học bạn đã đăng ký, phục vụ học tập cá nhân.

## Skill của khóa học

`python -m engine export skill <slug>` tạo thư mục skill gồm `SKILL.md` (mục lục chương, quiz và cách dùng) và `references/`:
`course/` (transcript từng chương), `quizzes/` (mọi quiz và bài kiểm tra kèm đáp án, giải thích), `materials/` (file đính kèm).
Chép thư mục đó vào `.claude/skills/` (một dự án) hoặc `~/.claude/skills/` (mọi dự án), rồi hỏi Claude về khóa học, nhờ ra quiz hoặc làm bài kiểm tra thử.

## Archive

Trích xuất từ vựng/kiến thức bằng AI, app flashcard và báo cáo chất lượng nằm ở [archive/](archive/README.md) (có hướng dẫn khôi phục).

## Test

```bash
python -m pytest
```
