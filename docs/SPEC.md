# ĐẶC TẢ DỰ ÁN: PERSONAL LEARNING BASE BUILDER

> Phiên bản spec: 2.0 (2026-11-04). Thay thế spec 1.x (định hướng flashcard/Anki).
> Giai đoạn 1 (Ingestion) đã triển khai xong và được giữ nguyên trong spec này.

## 1. Tổng quan sản phẩm

Personal Learning Base Builder là một **nền tảng dữ liệu học tập cá nhân dùng chung**: nhận tài liệu học tập — trọng tâm là transcript khóa học Udemy định dạng VTT — rồi tạo ra một bộ dữ liệu sạch, có cấu trúc, truy được nguồn, và tái sử dụng được.

Trên nền dữ liệu đó, hệ thống hỗ trợ **ba hướng sử dụng độc lập**:

| Hướng | Mục đích | Có dùng AI? |
|---|---|---|
| 1. NotebookLM | Xuất Markdown sạch để người dùng tự đưa lên NotebookLM (nay là *Gemini Notebook*) | Không |
| 2. Vocabulary Extraction | Chọn và xếp hạng từ vựng, thuật ngữ có giá trị trong khóa học | Có (đánh giá ứng viên) |
| 3. Knowledge Extraction | Biến transcript thành hệ thống kiến thức phân cấp | Có |

Ba hướng chỉ dùng chung **Clean Dataset** và các thành phần hạ tầng; mỗi hướng có workflow, output schema và lệnh riêng, chạy độc lập với nhau. NotebookLM không phụ thuộc vào pipeline AI.

Clean Dataset (JSON) và bản Markdown xuất ra được thiết kế để tái sử dụng cho: NotebookLM; Claude và các AI assistant khác (đưa trực tiếp Markdown hoặc JSON); hai chế độ trích xuất của hệ thống; và các hệ thống flashcard/Anki trong tương lai.

Hệ thống phục vụ học tập cá nhân, không thương mại. Chỉ xử lý khóa học người dùng đã đăng ký.

### 1.1. Mục tiêu

1. Lấy transcript từ Udemy nhanh, lặp lại được, không tạo dữ liệu trùng.
2. Tạo Clean Dataset xác định (deterministic, không AI), giữ ranh giới bài học, metadata, thứ tự câu và timestamp.
3. Xuất tài liệu Markdown dễ đọc, vừa giới hạn nguồn của NotebookLM.
4. Trích xuất từ vựng quan trọng: lọc nhiễu bằng xử lý xác định, AI chỉ đánh giá và xếp hạng ứng viên.
5. Trích xuất kiến thức có cấu trúc phân cấp theo ranh giới ngữ nghĩa.
6. Mọi kết quả trích xuất truy ngược được về bài học, khoảng câu và thời điểm trong video.
7. Thiết kế AI mở: V1 chạy bằng Claude Code (subscription), sau này thay bằng Claude API mà không đổi pipeline.

## 2. Ba hướng sử dụng và luồng dữ liệu

```text
                         ┌──────────────────────────── Nền tảng dùng chung ───────────────────────────┐
 Udemy (login/fetch)     │                                                                            │
 hoặc file tự đặt  ───►  │  Raw (data/input, không sửa) ──► Transcript Cleaner ──► Clean Dataset      │
                         │                                   (Python, không AI)     (data/clean, JSON)│
                         └───────────────────────────────────────────────┬────────────────────────────┘
                                                                         │
            ┌────────────────────────────────────┬───────────────────────┴───────────────────────┐
            ▼                                    ▼                                               ▼
  Hướng 1: NotebookLM Export          Hướng 2: Vocabulary Mode                      Hướng 3: Knowledge Mode
  (không AI)                          Candidate Extraction (spaCy)                   Task theo bài học
  Markdown theo chapter + index       → Chuẩn hóa & gộp toàn khóa                    → AI: semantic segmentation
            │                         → Lọc từ phổ thông                               + topic + mục kiến thức
            ▼                         → AI đánh giá ứng viên                         → Validate → lưu phân cấp
  NotebookLM (công cụ ngoài)          → Validate → xếp hạng → lưu                    → Export JSON/Markdown
                                      → Export JSON/CSV/Markdown
                                                 │                                               │
                                                 └──────────── AI Orchestrator dùng chung ───────┘
                                                   (task packet, runner, cache, validate, review)
```

## 3. Dữ liệu đầu vào và Ingestion *(Giai đoạn 1 — đã triển khai)*

Hỗ trợ các định dạng:
- `.vtt` (chính)
- `.md`, `.txt`
- `.pdf`, `.docx`: Future.

Cấu trúc thư mục đầu vào: mỗi khóa học một thư mục, mỗi ngôn ngữ một thư mục con.

```text
data/input/
  <course-slug>/
    en_US/
      _manifest.json                    # chỉ có khi tải bằng lệnh fetch
      001-introduction.vtt
      002-setup-environment.vtt
    vi_VN/
      _manifest.json
      002-setup-environment.vtt
```

Quy ước khi tải từ Udemy: `<course-slug>/<locale>/NNN-<lecture-slug>.vtt`
- `<locale>`: `locale_id` của caption (`en_US`, `vi_VN`, ...).
- `NNN`: thứ tự bài giảng trong toàn khóa (3 chữ số, 4 nếu > 999 bài).
- `<lecture-slug>`: tiêu đề bỏ dấu, chữ thường, ký tự khác `[a-z0-9]` thành `-`, tối đa 60 ký tự; rỗng thì `lecture-<id>`.
- Tiêu đề gốc (Unicode) được giữ trong `_manifest.json` của thư mục ngôn ngữ.

Khi import file tự đặt (thư mục không có `_manifest.json`):
- Tên khóa học = tên thư mục; tên bài = tên file bỏ phần mở rộng (và bỏ hậu tố locale nếu có).
- File đặt trong thư mục con `<course>/<lang>/` có ngôn ngữ = tên thư mục con; file đặt phẳng trong `<course>/` dùng hậu tố locale trong tên file (`lesson.vi.txt`) nếu có, ngược lại `default_lang`.
- Cùng tên bài ở các thư mục ngôn ngữ khác nhau là cùng một bài học.
- Thứ tự bài = thứ tự sắp xếp tên bài.
- **Không trộn:** một thư mục khóa học đã có thư mục ngôn ngữ do `fetch` tạo (có `_manifest.json`) thì các file/thư mục tự đặt khác trong đó bị bỏ qua kèm cảnh báo; file tự đặt không bao giờ ghi đè metadata khóa học Udemy.

Mỗi tài liệu lưu: tên khóa học, tên bài (và chương nếu có), tên file gốc, ngôn ngữ, nguồn caption (`manual` / `auto` / `file`), thời điểm nhập.

### 3.1. Lấy transcript từ Udemy

Tham khảo cơ chế của `InvictusNavarchus/udemy-transcript-downloader`: gọi API nội bộ `api-2.0` của Udemy (không cào giao diện panel Transcript), lấy curriculum, đọc `asset.captions[]` và tải file VTT.

**Xác thực:**
- Dùng cookie `access_token` của tài khoản Udemy (thời hạn quan sát được khoảng 28 ngày, chưa có tài liệu chính thức).
- Lệnh `login` mở Chrome/Edge có sẵn trên máy bằng Playwright (profile riêng ở `data/.auth/`), người dùng tự đăng nhập, script chờ cookie `access_token` xuất hiện rồi lưu vào `config.local.yaml`.
- Có thể dán token thủ công vào `config.local.yaml` hoặc đặt biến môi trường `UDEMY_ACCESS_TOKEN` (ghi đè file).
- `config.local.yaml` và `data/.auth/` không được commit. Token không bao giờ được in ra log hoặc output.
- Một tài khoản; `base_url` cấu hình được (`https://www.udemy.com` hoặc portal Udemy Business `https://<company>.udemy.com`).

**Truy cập mạng:**
- Dùng `curl_cffi` (giả lập TLS của Chrome) để tránh bị Cloudflare chặn.
- Tối đa 4 request đồng thời; retry với backoff khi gặp 429/5xx hoặc lỗi mạng.
- Request mang token không theo redirect (tránh lộ token sang host khác); file caption tải từ CDN không kèm token.
- 401/403 dạng JSON: token hết hạn → dừng, yêu cầu chạy lại `login`. 401/403 dạng HTML: bị Cloudflare chặn → báo lỗi, không yêu cầu login.
- Lần gọi curriculum đầu tiên của một khóa có thể mất 1–2 phút (Udemy dựng danh sách caption phía server); các lần sau vài giây. Lệnh in tiến độ.
- `fetch` không có tham số khóa học: liệt kê các khóa đã đăng ký (id, slug, tiêu đề).

**Chọn caption:**
- `--lang` mặc định `en`; nhận danh sách (`en,vi`) hoặc `all`.
- Mã ngắn (`en`) khớp mọi `en_*`; mã đầy đủ (`en_GB`) phải khớp chính xác.
- Mỗi bài × mỗi ngôn ngữ yêu cầu chỉ lấy một track, theo thứ tự ưu tiên: caption do giảng viên tải lên (manual) trước caption tự động (auto); cùng loại thì `en_US` (với `en`) trước, rồi theo alphabet locale.
- URL caption là link ký có thời hạn: tải ngay, không lưu URL.
- `fetch` chỉ tải và ghi các thư mục `<locale>/` khớp `--lang`; thư mục ngôn ngữ khác giữ nguyên.

**`_manifest.json`** (một file cho mỗi thư mục ngôn ngữ): `course_id`, `slug`, `title`, `url`, `host`, `locale_id`, `fetched_at`, `requested_langs`; mảng `lectures[]`: `lecture_id`, `position`, `chapter_title`, `chapter_index`, `title`, `filename`, `source`, `label`, `sha256`; mảng `skipped[]` (bài không có file trong ngôn ngữ này): `lecture_id`, `title`, `reason` ∈ {`non_video`, `no_caption_for_lang`, `http_<code>`, thông báo lỗi mạng}.

### 3.2. Đăng ký dữ liệu (import)

- `import` nhận thư mục khóa học (mọi ngôn ngữ) hoặc một thư mục ngôn ngữ có `_manifest.json`, ghi course/lesson/transcript vào SQLite rồi chạy Transcript Cleaner (mục 5) cho các file mới hoặc đã đổi.
- Thư mục ngôn ngữ có `_manifest.json`: chỉ import file được manifest liệt kê; file khác bị bỏ qua và được báo lại.
- Bài học được nhận diện theo `lecture_id` (Udemy) hoặc tên bài (file tự đặt), nên nhiều ngôn ngữ của cùng một bài không tạo bài học trùng.
- File có cùng SHA-256 với bản đã nhập: bỏ qua. Hash thay đổi: làm sạch lại và xử lý phụ thuộc theo mục 9.5.

## 4. Các lớp dữ liệu

Dữ liệu được tách thành bốn lớp; lớp sau chỉ được sinh ra từ lớp trước, không bao giờ sửa ngược.

| Lớp | Vị trí | Nội dung | Sinh bởi |
|---|---|---|---|
| Raw | `data/input/` | File VTT/TXT/MD gốc + manifest | `fetch` hoặc người dùng |
| Clean | `data/clean/` | Clean Dataset JSON — **nguồn sự thật** cho mọi hướng | Transcript Cleaner |
| Extracted | `data/learning.db` (+ `data/work/` cho task AI) | Ứng viên, từ vựng, kiến thức, trạng thái | Vocabulary / Knowledge Mode |
| Export | `data/export/` | Markdown, JSON, CSV cho người dùng/công cụ khác | Export Manager |

```text
data/                                            # toàn bộ gitignored
  input/<course>/<locale>/...                    # raw, không sửa
  clean/<course>/<language>/<NNN>-<lesson-slug>.json
  work/tasks/<mode>/<task_id>.json               # task packet gửi AI
  work/tasks/<mode>/<task_id>.result.json        # kết quả AI thô (trước validate)
  export/
    notebooklm/<course>/<lang>/index.md, *.md
    vocabulary/<course>/vocabulary.json|.csv|.md
    knowledge/<course>/knowledge.json, knowledge.md
  learning.db                                    # metadata, index, kết quả trích xuất
  .auth/                                         # profile trình duyệt login
```

- Tên file clean cho mọi nguồn: `<position:03d>-<slugify(title)>.json` (cùng quy tắc slug mục 3) trong thư mục `<language>` (locale của transcript, ví dụ `en_US`, hoặc mã từ file tự đặt, ví dụ `vi`).
- SQLite lưu metadata, hash, trạng thái xử lý và kết quả trích xuất. Văn bản transcript đã làm sạch **không** lưu trong SQLite (bỏ bảng `chunk` của Giai đoạn 1); mọi tham chiếu dùng `(transcript_id, sentence_id)`.

## 5. Clean Dataset và Transcript Cleaner

### 5.1. Quy tắc làm sạch (Python, không AI)

- Không sửa hoặc ghi đè file gốc; output là dữ liệu dẫn xuất.
- Parser VTT trả về danh sách cue `(start, end, lines[])`, không tự loại trùng; mọi quy tắc loại trùng nằm trong Cleaner.
- Loại bỏ header `WEBVTT`, khối `NOTE`/`STYLE`/`REGION`, cue id, dòng timing, thẻ định dạng (`<v>`, `<c>`, `<b>`, timestamp nội tuyến), decode HTML entity, chuẩn hóa khoảng trắng; UTF-8, đa ngôn ngữ.
- **Rolling captions** — chỉ áp dụng giữa hai cue *liền kề về thời gian* (`start ≤ end_trước + 0,05s`):
  - Nếu các dòng đầu của cue hiện tại trùng nguyên văn các dòng cuối của cue trước **và** cue hiện tại còn dòng mới phía sau → bỏ các dòng lặp (kiểu YouTube cuộn hai dòng).
  - Nếu cue hiện tại trùng hoàn toàn cue trước → chỉ bỏ khi hai cue **chồng thời gian** (`start < end_trước`) hoặc cue hiện tại kéo dài < 0,1s (cue "nháy" của caption cuộn).
  - Mọi trường hợp khác giữ nguyên, kể cả hai cue liên tiếp có cùng nội dung (lặp có chủ đích, ví dụ "No." / "No.").
- Bảo toàn thứ tự câu.
- Tách câu theo dấu kết câu (`.`, `!`, `?`, `…`, dấu câu CJK). Câu trải qua nhiều cue: `start` = start cue đầu, `end` = end cue cuối. Nhiều câu trong một cue dùng chung khoảng thời gian của cue (xấp xỉ).
- Caption không có dấu câu: xét theo từng transcript — nếu trung bình > 40 từ/câu sau khi tách theo dấu câu thì dùng mỗi cue làm một "câu".
- TXT/MD: không có timestamp (`start`/`end` = `null`); MD bỏ ký hiệu heading/blockquote/đường kẻ; parser giữ dòng trống để làm ranh giới đoạn.

### 5.2. Chia đoạn (paragraph)

Phục vụ Markdown dễ đọc và gợi ý ranh giới cho AI:
- VTT: ngắt đoạn khi khoảng lặng giữa hai câu ≥ `clean.paragraph_pause_seconds` (mặc định 1,5s) hoặc đoạn đã đủ `clean.max_sentences_per_paragraph` câu (mặc định 6).
- TXT/MD: đoạn theo dòng trống.

### 5.3. Định dạng file Clean

```json
{
  "schema_version": 1,
  "cleaner_version": "1",
  "course": {"slug": "aws-certified-solutions-architect-associate-saa-c03", "title": "Ultimate AWS Certified Solutions Architect Associate 2026", "source": "udemy", "external_id": "2196488"},
  "lesson": {"external_id": "13528154", "position": 12, "chapter_index": 3, "chapter_title": "Amazon S3", "title": "S3 Lifecycle Rules"},
  "language": "en_US",
  "caption_source": "manual",
  "source_file": "input/aws-certified-solutions-architect-associate-saa-c03/en_US/012-s3-lifecycle-rules.vtt",
  "source_sha256": "…",
  "word_count": 812,
  "sentences": [
    {"id": 0, "start": 0.0, "end": 3.44, "text": "So now let's talk about lifecycle rules."}
  ],
  "paragraphs": [[0, 5], [6, 11]]
}
```

- **Mọi khoảng câu trong hệ thống là khoảng đóng `[start_id, end_id]`** (bao gồm cả hai đầu).
- `sentences[].id` bắt đầu từ 0, liên tục, ổn định trong một `cleaner_version`; là đơn vị tham chiếu nguồn của mọi kết quả.
- Làm sạch lại khi `source_sha256` hoặc `cleaner_version` thay đổi (mục 9.5).

## 6. Hướng 1 — Xuất dữ liệu cho NotebookLM

**Luồng:** `Raw VTT → Transcript Cleaner → Clean Dataset → Markdown Export → (người dùng upload lên NotebookLM)`

Không dùng AI. NotebookLM là công cụ bên ngoài, không phải thành phần của hệ thống.

**Giới hạn tham chiếu (NotebookLM/Gemini Notebook, 11/2026):** tối đa 500.000 từ hoặc 200 MB mỗi nguồn; số nguồn mỗi notebook: Free 50, Plus 100, Pro 300, Ultra 500–600; hỗ trợ `.md` và `.txt`.

**Đơn vị xuất** (`--by`):

| `--by` | File | Ghi chú |
|---|---|---|
| `chapter` (mặc định) | `NN - <Chapter title>.md` | Nếu số chapter > `notebooklm.max_sources` (mặc định 45): gộp các chapter liền kề thành `Vol NN (Chapters a–b).md` |
| `course` | `<Course title>.md` | Khóa lớn nhất hiện có ~300k từ, dưới 500k |
| `lesson` | `NNN - <Lesson title>.md` | In cảnh báo khi số file vượt 50/100/300 (giới hạn Free/Plus/Pro) |

- Mọi file vượt `notebooklm.max_words_per_file` (mặc định 200.000 từ) được tách thành `<tên> (part N).md`, cắt tại ranh giới bài.
- File tự đặt không có chapter: coi cả khóa là một chapter.
- `--lang` chọn ngôn ngữ (mặc định `default_lang`; nhận danh sách và `all` như `fetch`, không phân biệt hoa/thường); mỗi bài lấy một transcript theo thứ tự ưu tiên mục 3.1; mỗi giá trị `--lang` được xuất vào thư mục riêng `notebooklm/<course>/<lang>/`.
- Tên file bỏ ký tự không hợp lệ trên Windows/macOS/Linux.

**Nội dung:** file chapter/course dùng H1 cho chapter, H2 cho bài; file theo bài dùng H1 cho bài.

```markdown
# Chapter 3: Amazon S3

## 12. S3 Lifecycle Rules

> Course: Ultimate AWS Certified Solutions Architect Associate 2026 · Lesson 12/384 · en_US · manual caption

So now let's talk about lifecycle rules. You can transition objects…

Expiration actions can be configured to delete…
```

- Mỗi đoạn (mục 5.2) là một đoạn văn thuần, không có mốc thời gian (yêu cầu người dùng 2026-11-05); timestamp vẫn ở Clean Dataset.
- `index.md`: tên khóa, nguồn, ngôn ngữ, đơn vị xuất, danh sách file → chapter → các bài (số thứ tự, tiêu đề). Không ghi ngày xuất để giữ tính xác định.
- Dòng transcript bắt đầu bằng `#` hoặc `>` được escape để không thành heading/quote. `Lesson N/T` dùng `T` = vị trí bài lớn nhất của khóa.
- Xuất lại ghi đè thư mục export của khóa/locale đó; nội dung xác định (cùng input → cùng output).

## 7. Hướng 2 — Vocabulary Extraction Mode

**Luồng:** `Clean Dataset → Candidate Extraction → Normalization & Deduplication → Common-word Filtering → AI Evaluation → Validate → Ranking → Important Vocabulary → Export`

Chế độ độc lập với Knowledge Mode. V1 chỉ xử lý transcript tiếng Anh: mỗi bài dùng đúng một transcript `en_*`, chọn theo thứ tự ưu tiên mục 3.1.

### 7.1. Trích ứng viên (Python, không AI)

Dùng spaCy + `en_core_web_sm` trên từng câu của Clean Dataset:
- **Acronym / chữ viết tắt / ký hiệu kỹ thuật:** regex cho token viết hoa hoặc chữ-số (`S3`, `EC2`, `IAM`, `API`, `DNS`, `SQL`) và token kỹ thuật có chữ số (`k8s`). Không lọc theo độ dài ký tự.
- **Cụm danh từ / thuật ngữ nhiều từ:** từ noun chunk, bỏ mạo từ/đại từ/từ định lượng đầu cụm và phần sở hữu (`an S3 bucket` → `S3 bucket`, `the model's output` → `output`); giữ các từ nội dung mà spaCy coi là stopword (`least privilege`, `front end`).
- **Từ ghép có gạch nối:** dò trực tiếp trên token (`sub-agent`, `multi-agent`, `few-shot`, `state-of-the-art`); các mảnh của từ ghép không thành ứng viên riêng.
- **Phrasal verb:** động từ + tiểu từ (`dep = prt`), ví dụ `spin up`, `scale out`, `set up`.
- **Từ đơn:** danh từ, động từ, tính từ, trạng từ có nội dung.
- Ghi lại mọi lần xuất hiện: `(transcript_id, sentence_id)`.

### 7.2. Chuẩn hóa và gộp (Normalizer dùng chung)

- Dạng chuẩn: chữ thường (giữ nguyên dạng viết hoa của acronym), chuẩn hóa khoảng trắng và gạch nối; với cụm nhiều từ chỉ lemma từ chính (từ cuối). Token bị gắn nhãn tên riêng (PROPN) được lemma như danh từ (`Tokens` → `token`). Từ đơn chỉ khác hoa/thường gộp về dạng acronym (`json` → `JSON`). Cùng hàm chuẩn hóa này được Knowledge Mode dùng cho tên khái niệm.
- Gộp các biến thể cùng dạng chuẩn trên **toàn khóa**; giữ dạng hiển thị phổ biến nhất.
- Không gộp các từ chỉ vì viết gần giống nhau.
- Mỗi ứng viên có: tần suất, số bài xuất hiện, các lần xuất hiện, và `vocabulary.contexts_per_candidate` (mặc định 3) câu ngữ cảnh tiêu biểu, chọn xác định (ưu tiên các bài khác nhau, theo thứ tự bài).

### 7.3. Lọc từ phổ thông

- Danh sách tần suất tiếng Anh tổng quát (điểm Zipf) xuất một lần từ `wordfreq`, lưu trong repo kèm ghi công giấy phép CC BY-SA 4.0. `wordfreq` không phải phụ thuộc lúc chạy.
- **Ngưỡng phổ thông** theo trình độ `learner.cefr_level` (cấu hình, tham số `--level`, hoặc skill hỏi người dùng khi chưa đặt): `vocabulary.zipf_threshold_by_level`.
- **Keyness** của từ trong khóa: `keyness = log2((f_khóa + 1) / (f_chung + 1))`, với `f_khóa` = số lần xuất hiện trên một triệu từ của khóa và `f_chung = 10^(Zipf − 3)` (tần suất trên một triệu từ tiếng Anh chung).
- Một ứng viên **bị loại** (`filter_reason`) khi:
  - `common_word`: là từ đơn, Zipf ≥ ngưỡng **và** keyness < `vocabulary.keyness_min` (mặc định 4,0 sau benchmark khóa CCAR — 2,0 giữ cả `use`, `run`, `actually`). Nhờ vậy từ phổ thông mang nghĩa chuyên ngành trong khóa (`region`, `instance`, `bucket`) vẫn được giữ.
  - `stopword`: thuộc danh sách stopword của spaCy.
  - `noise`: chỉ gồm số/ký hiệu, từ đệm khi nói (`um`, `uh`, `okay`, `alright`), hoặc nhãn caption (`[music]`, `[laughter]`). Không bao giờ dùng độ dài ký tự làm tiêu chí.
  - `low_frequency`: cụm nhiều từ hoặc phrasal verb xuất hiện ít hơn `vocabulary.phrase_min_frequency` lần (mặc định 3; benchmark: 5.981/7.547 cụm danh từ chỉ xuất hiện 1 lần, phần lớn là nhiễu).
- Acronym và cụm nhiều từ không bị lọc bởi tần suất tổng quát (chỉ bởi `low_frequency`).
- Ứng viên bị loại vẫn được lưu kèm lý do để kiểm tra lại.

### 7.4. AI đánh giá

- **Gom lô:** chỉ các ứng viên `kept` **chưa có đánh giá hợp lệ** cho `prompt_version` hiện tại, hoặc có tập câu ngữ cảnh đã thay đổi; sắp xếp xác định (tần suất giảm dần, rồi theo `normalized_term`) và chia lô `vocabulary.batch_size` (mặc định 100). Nhờ vậy thêm bài mới chỉ tạo task cho ứng viên mới/thay đổi.
- Input mỗi ứng viên: dạng hiển thị, loại sơ bộ, tần suất, số bài, câu ngữ cảnh (kèm id câu); input của lô còn có tên khóa, trình độ người học.
- AI quyết định chọn/loại (`selected`) và chấm `importance` 0–100 theo: mức liên quan đến nội dung khóa, tầm quan trọng trong lĩnh vực, tần suất và ý nghĩa trong ngữ cảnh, giá trị ứng dụng thực tế; đồng thời bổ sung thông tin học tập (mục 7.5). Hướng dẫn `vocab-eval.md` có thang điểm mốc (rubric kèm ví dụ) để điểm giữa các lô so sánh được.
- **Xếp hạng cuối (Python, xác định) = thứ tự học:** trong các mục `selected = true` của khóa: `importance` giảm dần → từ/cụm dài hơn trước (số từ, rồi số ký tự, giảm dần) → `lesson_count` giảm dần → `frequency` giảm dần → `normalized_term`. Tính lại sau mỗi lần ingest.

### 7.4b. Bổ sung chi tiết học (task `vocab_enrich`)

- Chỉ chạy cho các từ trong danh sách học (mục 7.5 Export), không cho toàn bộ ứng viên — giữ chi phí AI thấp.
- Mỗi từ thêm: `part_of_speech`, `definition_vi` (bản dịch đầy đủ của định nghĩa tiếng Anh), `example_vi` (bản dịch câu ví dụ gốc), `usage_note` (tùy chọn, ≤ 25 từ: collocation, từ dễ nhầm, mẫu câu).
- Cache theo hash của input từng từ (term, nghĩa, định nghĩa, câu ví dụ, prompt_version): đổi định nghĩa hoặc câu ví dụ thì bổ sung lại. Mục thiếu trường bắt buộc bị bỏ riêng và vào lô sau.
- Lệnh: `vocab enrich-prepare` → runner → `vocab enrich-ingest` (cùng giao thức mục 9.2); hướng dẫn `references/vocab-enrich.md`.

### 7.5. Output mỗi mục từ vựng

| Trường | Mô tả |
|---|---|
| `term`, `normalized_term` | Dạng hiển thị, dạng chuẩn |
| `term_type` | `acronym` / `abbreviation` / `technical_term` / `collocation` / `phrasal_verb` / `academic` / `general` (AI xác nhận/sửa loại sơ bộ) |
| `selected` | AI chọn hay loại |
| `importance` (0–100), `rank`, `reason` | Điểm, thứ hạng trong khóa, lý do ngắn |
| `frequency`, `lesson_count` | Thống kê trong khóa |
| `vietnamese_meaning` | Nghĩa tiếng Việt theo ngữ cảnh khóa |
| `english_definition` | Định nghĩa tiếng Anh theo ngữ cảnh khóa |
| `expansion` | Dạng đầy đủ của acronym/chữ viết tắt (nếu có) |
| `cefr_level` | Chỉ với từ phổ thông, khi xác định hợp lý |
| `examples` | Câu gốc trong transcript (id câu do AI chọn trong số câu ngữ cảnh) — không tự bịa |
| `sources` | Mọi lần xuất hiện: bài, id câu, timestamp — lưu trong SQLite (`vocab_occurrence`), không đưa vào file export |
| `status`, `confidence` | Mục 9.4 |

Một thuật ngữ là một bản ghi `vocab_term` duy nhất trên toàn hệ thống; mọi thông tin do AI đánh giá (loại, nghĩa, định nghĩa, expansion, CEFR, điểm) gắn theo **từng khóa** (`vocab_entry`) nên các nghĩa khác nhau theo ngữ cảnh khóa được giữ lại.

**Export** (chỉ mục `selected = true`, không `rejected`, đánh giá khớp ngữ cảnh hiện tại):
- `vocabulary.csv`: toàn bộ từ được chọn (tra cứu bằng Excel/Sheets).
- `vocabulary.json` và `vocabulary.md` = **danh sách học**: các từ có `importance` ≥ `vocabulary.export_min_importance` (mặc định 70 — mốc "thuật ngữ quan trọng lặp lại / cụm từ rất hữu ích" của rubric). Số lượng co giãn theo nội dung khóa (khóa CCAR: ~520 từ) thay vì cố định; vài nghìn từ là quá nhiều để học, kể cả với B1.
- Định dạng cho người và app học: mỗi từ gồm `rank, term, type, pos, importance, vi, en, definition_vi, expansion, cefr, note, frequency, lessons` và **một** câu ví dụ gốc `{text, vi, lesson}` (bản dịch từ `vocab_enrich`); JSON ghi mỗi mục một dòng. File export không ghi mốc thời gian (yêu cầu người dùng 2026-11-05); timestamp vẫn ở Clean Dataset/SQLite. Nguồn chi tiết (mọi lần xuất hiện, id câu) ở lại SQLite.

## 8. Hướng 3 — Knowledge Extraction Mode

**Luồng:** `Clean Dataset → (Pre-split nếu bài quá dài) → AI: Semantic Segmentation + Topic Identification + Concept Extraction → Validate → Structured Knowledge → Export`

Chế độ độc lập với Vocabulary Mode. V1 chỉ xử lý transcript tiếng Anh (một transcript `en_*` mỗi bài, theo thứ tự ưu tiên mục 3.1).

### 8.1. Phân đoạn ngữ nghĩa

- Đơn vị xử lý là **một bài học**. Bài học hiện có trung vị ~700–1.000 từ, dài nhất ~2.700 từ, vừa context model → một task AI mỗi bài.
- AI nhận danh sách câu có id (kèm ranh giới đoạn mục 5.2 làm gợi ý) và trả về ranh giới topic/subtopic dưới dạng khoảng id câu; không cắt theo số token cố định, không chia đôi một khái niệm.
- Vocabulary Mode và Knowledge Mode dùng chiến lược phân đoạn khác nhau: Vocabulary làm việc theo câu, Knowledge theo bài/topic.
- **Bài quá dài** (> `knowledge.max_lesson_words`, mặc định 8.000 từ): Python cắt thành các phần tại ranh giới đoạn; mỗi phần gửi kèm đoạn liền trước làm ngữ cảnh *chỉ đọc*. Mỗi phần chỉ được tạo topic/item trong phạm vi câu của chính nó. Khi ghép: topic cuối phần trước và topic đầu phần sau có cùng tiêu đề chuẩn hóa thì gộp thành một; nếu không, topic tại ranh giới được đánh dấu `needs_review`.

### 8.2. Phân cấp

```text
Course → Chapter (từ Udemy manifest) → Lesson → Topic → [Subtopic] → Knowledge Item
```

- Topic/subtopic do AI tự xác định từ nội dung, không theo danh mục định nghĩa cứng.
- Subtopic là tùy chọn, tối đa một cấp. Item gắn vào node sâu nhất chứa nó (topic hoặc subtopic).
- Các topic của một bài nên phủ phần lớn câu của bài; khoảng câu của topic không chồng nhau; subtopic nằm trong topic cha.

### 8.3. Knowledge Item

Loại item: `concept`, `definition`, `key_point`, `process` (các bước, cách hoạt động), `example`, `advantage`, `disadvantage`, `relation`, `warning` (cảnh báo/giới hạn).

| Trường | Mô tả |
|---|---|
| `item_type` | Một trong các loại trên |
| `title` | `{ "<lang>": "..." }` theo `knowledge.output_languages`; tên thuật ngữ/khái niệm giữ tiếng Anh trong mọi ngôn ngữ |
| `content` | `{ "<lang>": "..." }`; với `process`: `{ "<lang>": ["bước 1", "bước 2", …] }` |
| `concept_name` | Với `concept`/`definition`: tên khái niệm tiếng Anh (để gom) |
| `relation` | Với `relation`: `{ "from": "<concept>", "to": "<concept>", "type": "is_a \| part_of \| uses \| compared_with \| alternative_to \| related_to" }` |
| `source` | `transcript_id`, `[sentence_start, sentence_end]`, `start`/`end` (giây) |
| `status`, `confidence` | Mục 9.4 |

Topic/subtopic có `title` theo cùng cấu trúc đa ngôn ngữ và `source` riêng.

```json
{
  "course": {"slug": "…", "title": "…"},
  "chapters": [{"index": 3, "title": "Amazon S3", "lessons": [{
    "position": 12, "title": "S3 Lifecycle Rules", "transcript_id": 4521,
    "topics": [{
      "title": {"en": "Lifecycle transitions", "vi": "Chuyển lớp lưu trữ theo vòng đời"},
      "source": {"sentence_start": 0, "sentence_end": 14, "start": 0.0, "end": 61.2},
      "subtopics": [],
      "items": [{
        "item_type": "definition", "concept_name": "S3 Lifecycle Rule",
        "title": {"en": "S3 Lifecycle Rule", "vi": "S3 Lifecycle Rule"},
        "content": {"en": "A rule that moves or expires objects automatically…", "vi": "Quy tắc tự động chuyển lớp hoặc xóa object…"},
        "source": {"sentence_start": 2, "sentence_end": 4, "start": 6.1, "end": 15.8},
        "status": "auto_approved", "confidence": 0.86
      }]
    }]
  }]}]
}
```

### 8.4. Liên kết cơ bản (V1)

- Item có `concept_name` được gom theo tên chuẩn hóa (Normalizer mục 7.2) thành một khái niệm dùng chung; mỗi item là một mention có nguồn riêng.
- Item `relation` lưu quan hệ giữa hai khái niệm.
- Từ vựng và khái niệm cùng tên chuẩn hóa được liên kết khi export (`vocab_term.normalized_term = concept.normalized_name`), không cần bảng riêng. Lần xuất hiện của từ vựng có thể ánh xạ về topic qua khoảng id câu.
- Cây chủ đề cấp khóa (gom topic xuyên bài) và liên kết sâu: Future.

### 8.4b. Bổ sung chi tiết học (task `knowledge_enrich`)

Thêm theo yêu cầu người dùng (2026-11-05): JSON kiến thức phải giúp học được, có thứ tự quan trọng, đủ nhưng không thừa, và tiếng Việt không dịch từng chữ.
- Chạy trên item đã lưu (chỉ phần tiếng Anh), không đọc lại transcript, nên rẻ hơn nhiều so với trích lại. Task gom nguyên bài, khoảng `knowledge.enrich_batch_size` item (mặc định 60).
- Mỗi item thêm `importance` (0–100: 90+ cốt lõi/bẫy thi, 70+ ý hỗ trợ quan trọng, 50+ chi tiết/ví dụ hữu ích, < 50 thủ tục khóa học, giai thoại, lặp ý) và `question` (câu hỏi gợi nhớ, mỗi ngôn ngữ một câu, đáp án là nội dung item). Tiêu đề/nội dung ngôn ngữ khác tiếng Anh và tiêu đề topic được **dịch lại từ tiếng Anh** theo `references/translation-vi.md`; mục đã duyệt tay giữ nguyên tiêu đề/nội dung.
- Cache theo hash phần tiếng Anh của item (+ ngôn ngữ, prompt_version); trích lại bài thì item mới được bổ sung lại. Task chỉ chứa item còn thiếu (kèm topic chứa chúng); item thiếu/hỏng bị bỏ riêng và vào task của lần `enrich-prepare` sau (hash task có số vòng nên không bị cache chặn).
- Kiểm tra cứng khi ingest (cả `vocab_enrich`): đoạn tiếng Việt ≥ 6 từ không có dấu = chưa dịch (Haiku từng trả tiếng Anh cụt chữ cho ~200 item); tiêu đề ≥ 3 từ giống hệt tiếng Anh = chưa dịch (~8% item ở lượt đầu); `process` phải là danh sách bước.
- Lệnh: `knowledge enrich-prepare` → runner → `knowledge enrich-ingest`; hướng dẫn `references/knowledge-enrich.md`.

### 8.4c. Hướng dẫn dịch tiếng Việt

`references/translation-vi.md` là nguồn duy nhất cho mọi mode sinh tiếng Việt (vocab_eval, vocab_enrich, knowledge_extract, knowledge_enrich): dịch theo nghĩa rồi viết lại theo trật tự tiếng Việt, giữ thuật ngữ kỹ thuật bằng tiếng Anh, bảng từ có nghĩa chuyên ngành kèm bẫy nghĩa thường ("agent" ≠ "đại lý", "noise" ≠ "tiếng ồn", "business rules" = "quy tắc nghiệp vụ"), quy tắc câu (chủ động, bỏ "của nó", trật tự bổ ngữ) và ví dụ dịch từng chữ → tự nhiên. Prompt subagent luôn yêu cầu đọc file này (thêm 2026-11-05 vì bản dịch Haiku bị word-by-word).

**Export:** không xuất mục `rejected`, bài đang `stale` và item đã bổ sung có `importance` < `knowledge.export_min_importance` (mặc định 50); topic/bài không còn item bị bỏ.
- `knowledge.json` dạng gọn: `{kind, course, slug, languages, concepts[{name, lessons}], relations[{from, to, type}], min_importance, lessons[{n, title, chapter, topics[{title, items[{type, title, content, importance?, question?, subtopic?, concept?, relation?}]}]}]}` (không có mốc thời gian; bài theo thứ tự khóa, item theo thứ tự trong bài — app học sắp "quan trọng trước") — subtopic trở thành nhãn của item; id, khoảng câu, độ tin cậy, trạng thái ở lại SQLite. Ví dụ JSON đầy đủ ở mục 8.3 là mô hình lưu trữ, không phải file export.
- `knowledge.md`: ghi chú phân cấp chapter → lesson → topic → item, item cốt lõi (importance ≥ 80) đánh dấu ★; có thể đưa lên NotebookLM.

## 9. Thành phần dùng chung: AI Orchestrator

### 9.1. Task packet

Python tạo task, AI chỉ thực thi. `mode` ∈ {`vocab_eval`, `vocab_enrich`, `knowledge_extract`, `knowledge_enrich`}.

```json
{
  "task_id": "vocab_eval-3f9a2c1b7e04",
  "mode": "vocab_eval",
  "prompt_version": "vocab_eval-v1",
  "instructions": ".claude/skills/learning-base-builder/references/vocab-eval.md",
  "input_hash": "3f9a2c1b7e04…",
  "input": {"course": "…", "learner_level": "B1", "candidates": []},
  "output_schema": {},
  "result_path": "data/work/tasks/vocab_eval/vocab_eval-3f9a2c1b7e04.result.json"
}
```

- `task_id` = `<mode>-<12 ký tự đầu của input_hash>`.
- `input_hash` = SHA-256 của `input` **cùng mọi cấu hình ảnh hưởng tới kết quả** (`learner.cefr_level`, `knowledge.output_languages`, `vocabulary.contexts_per_candidate`, `prompt_version`).

### 9.2. Giao thức engine ↔ runner

Engine tách thành các bước để runner nào cũng cắm vào được:

1. `python -m engine <mode> prepare <course> [--limit N] [--lessons …]` — tạo task packet cho phần việc chưa có kết quả hợp lệ, ghi bảng `ai_task` trạng thái `pending`, in danh sách đường dẫn task.
2. **Runner** thực thi từng task `pending`: đọc task packet, ghi đúng `result_path`.
3. `python -m engine <mode> ingest <course>` — với mọi task `pending` đã có file result: validate (mục 9.4), lưu kết quả, chuyển trạng thái; tính lại xếp hạng (vocab) hoặc gom khái niệm (knowledge).
4. Lặp 1–3 đến khi không còn task `pending`.

Trạng thái `ai_task`: `pending` → `done` (hợp lệ) hoặc `invalid` (sai validate cứng). Ở lần `prepare` sau, task `invalid` còn lượt thử (`attempts` ≤ `ai.max_retries`) được đưa lại `pending` (xóa file result cũ); quá số lần thì `failed` và được báo lại; task vocab có toàn bộ ứng viên đã được lô khác đánh giá thì thành `superseded`. File kết quả JSON lệch ngoặc (lỗi hay gặp khi model tự viết JSON lồng nhiều tầng) được cân lại ngoặc trước khi parse; nội dung chuỗi không bị đụng tới.

- **V1 — Claude Code runner:** skill (`/learning-base-builder vocab evaluate` hoặc `knowledge extract`) chạy vòng lặp trên, phân phối task `pending` cho subagent Claude Code (dùng subscription), song song tối đa `ai.max_parallel_subagents`. Không gọi Anthropic API, không cần API key. Claude Code không chạy model local hay GPU local.
- **Tiết kiệm usage gói Claude** (chỉ bước 2 tốn usage; Clean, NotebookLM, Candidate Extraction chạy bằng Python):
  - Subagent trích xuất chạy model `ai.subagent_model` (mặc định **Haiku**) — dữ liệu đầu vào đã được làm sạch và chuẩn hóa nên tác vụ đủ đơn giản cho model nhỏ. Phiên chính chỉ điều phối.
  - Mỗi subagent nhận nhiều task (`ai.tasks_per_subagent`) để chia nhỏ chi phí khởi động subagent (system prompt, công cụ, hướng dẫn ~10–20 nghìn token): Knowledge 5 bài/subagent (benchmark: với 15 bài/subagent, Haiku giữ chất lượng ở ~5 bài đầu rồi giảm còn 1 topic/1 item mỗi bài; kết quả quá mỏng — bài ≥ 30 câu mà < 2 topic hoặc < 4 item — bị loại ở validate cứng); Vocabulary 2 lô/subagent (benchmark: một lô 100 ứng viên ≈ 70 nghìn token với Haiku; giữ tổng ngữ cảnh subagent dưới giới hạn của Haiku).
  - Subagent đọc hướng dẫn một lần, ghi kết quả ra `result_path` và chỉ trả về một dòng tóm tắt (ví dụ `done 15/15, invalid 0`); nội dung kết quả không đi qua ngữ cảnh phiên chính.
- **Future — Claude API runner:** thực thi bước 2 bằng Claude API (batch, concurrency, retry, theo dõi chi phí); bước 1 và 3 giữ nguyên.

### 9.3. Cache và checkpoint

- `ai_task` là cache: UNIQUE(`mode`, `prompt_version`, `input_hash`); task `done` không chạy lại.
- Checkpoint theo từng task; dừng giữa chừng thì chạy lại chỉ xử lý task còn `pending`.

### 9.4. Validate và kiểm duyệt

- **Sửa lỗi xác định trước khi validate** (rút ra từ benchmark Haiku — lỗi lệch biên nhỏ không đáng chạy lại cả task; mục được sửa luôn thành `needs_review`):
  - Knowledge: topic chồng nhau được cắt (topic bị phủ hoàn toàn gộp vào topic trước); khoảng câu của subtopic/item bị kẹp vào node cha; thiếu một đầu khoảng câu → lấy đầu còn lại; `item_type` lạ → `key_point`; `concept`/`definition` thiếu `concept_name` → dùng tiêu đề tiếng Anh; `process` viết thành chuỗi → một bước; nội dung dạng danh sách ở item khác `process` → nối thành chuỗi; khóa thừa trong item bị bỏ; item thiếu loại hoặc thiếu một ngôn ngữ ở tiêu đề/nội dung bị bỏ (phần còn lại của bài vẫn được lưu).
  - Vocabulary: `key` mà model chép nhầm dạng hiển thị được ánh xạ về key chuẩn; câu ví dụ ngoài các câu ngữ cảnh được giao bị bỏ; key lạ/trùng hoặc mục được chọn mà thiếu nghĩa bị bỏ riêng; ứng viên thiếu kết quả không làm hỏng lô — phần có được lưu, phần thiếu được `prepare` gom vào lô sau.
  - Runner: subagent tự kiểm tra file kết quả parse được bằng `json.load` trước khi trả về (giảm mạnh lỗi JSON lệch ngoặc).
- **Validate cứng** (sai → task `invalid`, không lưu gì): JSON đọc được; đúng JSON Schema (sau khi sửa); khoảng câu hợp lệ và nằm trong bài/phần được giao; topic không chồng nhau; enum đúng; tiêu đề topic/subtopic đủ các ngôn ngữ trong `output_languages`; Knowledge: phần có ≥ 30 câu phải có ≥ 2 topic và ≥ 4 item (chống kết quả quá mỏng).
- **Kiểm tra mềm** (sai → mục đó `needs_review`): term không thực sự xuất hiện (theo dạng chuẩn) trong câu ví dụ đã chọn; câu ví dụ nằm ngoài các câu ngữ cảnh được giao (bị bỏ, không làm hỏng cả lô); `confidence` < `ai.review_threshold` (mặc định 0,7); topic chồng nhau, hoặc các topic bỏ sót > 20% số câu của bài; topic tại ranh giới phần của bài quá dài không gộp được.
- **Trạng thái kết quả:**
  - `auto_approved`: qua cả validate cứng và mềm.
  - `needs_review`: không qua kiểm tra mềm.
  - `approved` / `rejected`: do người dùng quyết định qua lệnh `review` (ghi `reviewed_at`).
  - Với từ vựng, `selected = false` là quyết định của AI, độc lập với `status`.
- **Chạy lại với `prompt_version` mới:** kết quả mới (đã qua validate cứng) thay kết quả cũ, **trừ** các mục người dùng đã `approved`/`rejected` — các mục này giữ nguyên trừ khi chạy với `--override-reviewed`.
- Lệnh `review <course> --mode vocab|knowledge`: duyệt lần lượt các mục `needs_review` (hiển thị kết quả + câu nguồn), cho phép approve, reject, hoặc sửa nghĩa/nội dung rồi approve.

### 9.5. Theo dõi tiến trình và dữ liệu cũ

- `processing_state` theo từng transcript: `clean`, `vocab_occurrences`, `knowledge` (kèm hash input và version đã dùng).
- **Transcript được làm sạch lại** (raw đổi hoặc `cleaner_version` đổi): xóa `vocab_occurrence` và `knowledge_node`/`knowledge_item` của transcript đó (dữ liệu sinh lại được; id câu có thể đã đổi), đặt stage `vocab_occurrences` và `knowledge` = `stale`. Mục `approved`/`rejected` do người dùng duyệt được lưu vết (term/tiêu đề + quyết định) để áp lại khi kết quả mới khớp.
- **Tổng hợp từ vựng cấp khóa** (gộp, lọc, chọn ngữ cảnh) được tính lại toàn khóa khi có transcript thay đổi hoặc khi `learner.cefr_level` / ngưỡng lọc thay đổi; `vocab_entry` của term vẫn còn là ứng viên được giữ nếu tập câu ngữ cảnh không đổi, ngược lại được đánh giá lại ở lần `prepare` sau.
- Export và `review` bỏ qua dữ liệu của transcript đang `stale`.

## 10. Kiến trúc hệ thống

### 10.1. Claude Code Skill

- Giao diện người dùng: `/learning-base-builder <lệnh>`.
- Điều phối quy trình; hỏi người dùng các lựa chọn còn thiếu (ví dụ trình độ CEFR).
- Là runner AI V1 (mục 9.2): phân phối task cho subagent, hướng dẫn trích xuất nằm trong `references/`.
- Không đọc/in token Udemy.

### 10.2. Python Engine (`python -m engine <lệnh>`)

Xử lý mọi tác vụ xác định và điều phối dữ liệu. Phụ thuộc: stdlib, PyYAML, `curl_cffi`, spaCy + `en_core_web_sm`; Playwright (tùy chọn, chỉ cho `login`); pytest (dev).

| Module | Trách nhiệm | Trạng thái |
|---|---|---|
| `__main__.py` | CLI: thêm lệnh mới, cập nhật `stats`, bỏ phần chunk | Có, cần sửa |
| `config.py` | Đọc `config.yaml` + `config.local.yaml` + env | Có |
| `udemy_auth.py`, `udemy_client.py`, `fetcher.py` | Login, gọi api-2.0, tải VTT + manifest | Có |
| `importer.py` (Dataset Manager) | Đăng ký course/lesson/transcript, hash; gọi cleaner; quy tắc không trộn (mục 3) | Có, cần sửa |
| `vtt_parser.py`, `parser.py` (Document Parser) | VTT → cue `(start, end, lines)`, không loại trùng; TXT/MD giữ ranh giới đoạn | Có, cần sửa |
| `cleaner.py` (Transcript Cleaner) | Rolling caption, tách câu, chia đoạn, ghi Clean JSON | Mới (thay `segmenter.py`) |
| `normalizer.py` | Chuẩn hóa term/tên khái niệm dùng chung | Mới |
| `export_notebooklm.py` | Markdown theo chapter/course/lesson + index | Mới |
| `vocab/candidates.py` | spaCy, acronym, gộp, lọc phổ thông, chọn ngữ cảnh | Mới |
| `vocab/mode.py` | `prepare`/`ingest` cho vocab_eval, xếp hạng, dựng mô hình export | Mới |
| `knowledge/mode.py` | Pre-split, `prepare`/`ingest` cho knowledge_extract, gom khái niệm, dựng mô hình export | Mới |
| `ai/tasks.py` (AI Orchestrator) | Task packet, `input_hash`, cache, trạng thái, retry | Mới |
| `ai/validate.py` | Validate cứng/mềm, gán status | Mới |
| `database.py` (Result Storage) | Schema SQLite (`PRAGMA user_version`) | Có, cần sửa |
| `exporter.py` (Export Manager) | Chỉ tuần tự hóa mô hình export của từng mode ra JSON/CSV/Markdown | Mới |

### 10.3. Cấu trúc dự án

```text
learning-base-builder/
├── .claude/skills/learning-base-builder/
│   ├── SKILL.md
│   └── references/
│       ├── vocab-eval.md          # hướng dẫn, rubric, schema cho task vocab_eval
│       └── knowledge-extract.md   # hướng dẫn, schema cho task knowledge_extract
├── engine/                        # xem bảng 10.2
├── resources/
│   ├── word_frequency_en.tsv      # xuất từ wordfreq
│   └── ATTRIBUTION.md             # ghi công CC BY-SA 4.0
├── data/                          # xem mục 4 (gitignored)
├── study/                         # app flashcard tĩnh (HTML/CSS/JS) đọc vocabulary.json / knowledge.json
├── tests/
├── evaluations/test_cases/        # bộ bài benchmark + kết quả mong đợi
├── docs/SPEC.md
├── config.yaml
├── config.local.yaml              # token (gitignored)
├── config.local.example.yaml
├── requirements.txt
└── README.md
```

## 11. Data Model (SQLite)

Giữ từ Giai đoạn 1 (có chỉnh):
- **course** (id, title, source, external_id, slug UNIQUE, url, host, created_at)
- **lesson** (id, course_id, external_id, position, chapter, title; UNIQUE(course_id, external_id)) — thêm `chapter_index`.
- **transcript** (id, lesson_id, language, caption_source, filename, content_hash, imported_at; UNIQUE(lesson_id, language)) — thêm `clean_path`, `cleaner_version`, `sentence_count`, `word_count`; **bỏ** `status`, `processed_at` (thay bằng `processing_state`).

Mới:
- **processing_state** (transcript_id, stage `clean`/`vocab_occurrences`/`knowledge`, input_hash, version, status `done`/`stale`/`failed`, updated_at; PK(transcript_id, stage)).
- **ai_task** (id = task_id, mode, prompt_version, input_hash, course_id, task_path, result_path, status `pending`/`done`/`invalid`/`failed`, attempts, error, created_at, updated_at; UNIQUE(mode, prompt_version, input_hash)).
- **vocab_term** (id, normalized_term UNIQUE, display_term, preliminary_type, zipf).
- **vocab_candidate** (id, course_id, term_id, frequency, lesson_count, keyness, filter_status `kept`/`filtered`, filter_reason, context_sentence_refs (JSON danh sách `[transcript_id, sentence_id]`), context_hash; UNIQUE(course_id, term_id)).
- **vocab_occurrence** (candidate_id, transcript_id, sentence_id; PK(candidate_id, transcript_id, sentence_id)).
- **vocab_entry** (id, course_id, term_id, selected, term_type, importance, rank, reason, vietnamese_meaning, english_definition, expansion, cefr_level, example_sentence_refs (JSON), context_hash, status, confidence, reviewed_at, prompt_version, task_id; UNIQUE(course_id, term_id)).
- **knowledge_node** (id, transcript_id, parent_id, node_type `topic`/`subtopic`, title_json, position, sentence_start, sentence_end, status, confidence, reviewed_at, prompt_version, task_id).
- **knowledge_item** (id, node_id, item_type, concept_name, title_json, content_json, relation_json, sentence_start, sentence_end, status, confidence, reviewed_at).
- **concept** (id, normalized_name UNIQUE, name) và **concept_mention** (concept_id, knowledge_item_id; PK cả hai).
- **concept_relation** (concept_id, related_concept_id, relation_type, knowledge_item_id; PK(concept_id, related_concept_id, relation_type)).
- **review_log** (id, course_id, mode, key (normalized_term hoặc concept/tiêu đề chuẩn hóa), decision, edited_json, reviewed_at) — lưu vết quyết định duyệt để áp lại sau khi sinh lại kết quả (mục 9.5).

Bỏ khỏi V1: `chunk`, `vocabulary`, `vocabulary_meaning`, `knowledge_source`, `flashcard`, `extraction_cache`, và bảng `concept`/`concept_relation` phiên bản 1 (thay bằng phiên bản mới ở trên).

**Migration:** DB hiện chỉ chứa metadata tái tạo được từ `data/input/`. Giai đoạn 2 xóa `data/learning.db` và chạy lại `import` để tạo schema mới; từ đó dùng `PRAGMA user_version` để đánh số schema cho các thay đổi sau.

## 12. Yêu cầu chức năng và lệnh

### 12.1. Functional Requirements

| ID | Yêu cầu | Mục |
|---|---|---|
| FR-ING | Đăng nhập, tải transcript Udemy theo ngôn ngữ, đăng ký dữ liệu, chạy lại không trùng | 3 |
| FR-CLN | Làm sạch xác định ra Clean Dataset có câu, timestamp, đoạn; không sửa raw; không xóa lặp có chủ đích | 5 |
| FR-NLM | Xuất Markdown theo chapter/course/lesson + index, vừa giới hạn NotebookLM, không cần AI | 6 |
| FR-VOC | Trích ứng viên, chuẩn hóa, gộp, lọc phổ thông, AI đánh giá, xếp hạng, export; giữ acronym và cụm nhiều từ | 7 |
| FR-KNW | Phân đoạn ngữ nghĩa theo bài, topic phân cấp, item kiến thức, gom khái niệm, export | 8 |
| FR-AI | Task packet, runner thay thế được, cache, checkpoint, validate, review | 9 |
| FR-SRC | Mọi kết quả có nguồn bài + khoảng câu + timestamp | 5.3, 7.5, 8.3 |

### 12.2. Lệnh

`<course>` là slug khóa học (tên thư mục trong `data/input/`). Mỗi lệnh skill gọi lệnh engine tương ứng; riêng `vocab evaluate` và `knowledge extract` là vòng lặp skill theo mục 9.2.

| Lệnh skill | Lệnh engine | Mô tả | Trạng thái |
|---|---|---|---|
| `login` | `login` | Mở trình duyệt đăng nhập Udemy, lưu token | Có |
| `fetch [<url\|slug\|id>] [--lang]` | `fetch` | Tải transcript, rồi `import`; không tham số → liệt kê khóa | Có |
| `import <folder>` | `import` | Đăng ký dữ liệu + làm sạch | Có, cần thêm bước clean |
| `clean <course> [--force]` | `clean` | Làm sạch lại phần đổi; `--force` làm sạch lại toàn bộ dù hash/version không đổi | Mới |
| `export notebooklm <course> [--by chapter\|course\|lesson] [--lang]` | `export notebooklm` | Xuất Markdown cho NotebookLM | Mới |
| `vocab candidates <course> [--level]` | `vocab candidates` | Trích + lọc ứng viên (không AI) | Mới |
| `vocab evaluate <course> [--limit N]` | `vocab prepare` → runner → `vocab ingest` | Đánh giá ứng viên bằng AI; `--limit` = số task tối đa mỗi vòng | Mới |
| `vocab enrich <course> [--limit N]` | `vocab enrich-prepare` → runner → `vocab enrich-ingest` | Chi tiết học cho danh sách học (mục 7.4b) | Mới |
| `vocab export <course>` | `vocab export` | JSON/CSV/Markdown | Mới |
| `knowledge extract <course> [--lessons 1-10,15] [--limit N]` | `knowledge prepare` → runner → `knowledge ingest` | Trích kiến thức theo bài; `--lessons` = danh sách/khoảng `position` | Mới |
| `knowledge enrich <course> [--limit N]` | `knowledge enrich-prepare` → runner → `knowledge enrich-ingest` | Mức quan trọng, câu hỏi gợi nhớ, dịch lại tự nhiên (mục 8.4b) | Mới |
| `knowledge export <course>` | `knowledge export` | JSON/Markdown | Mới |
| `review <course> --mode vocab\|knowledge` | `review` | Duyệt mục `needs_review` | Mới |
| `stats` | `stats` | Thống kê dữ liệu và tiến trình từng hướng (clean, task AI theo trạng thái, số từ vựng/khái niệm) | Có, cần mở rộng |

### 12.3. App học flashcard (`study/`)

Thêm theo yêu cầu người dùng (2026-11-05). Thư mục `study/` gồm `index.html`, `style.css`, `app.js` thuần, không build, không server: mở `index.html`, chọn/kéo thả `vocabulary.json` hoặc `knowledge.json`.
- Từ vựng: mặt trước là từ (loại, từ loại, CEFR, dạng đầy đủ), mặt sau là nghĩa Việt, định nghĩa Anh + bản dịch, câu ví dụ gốc + bản dịch kèm số bài, ghi chú cách dùng. Lọc theo số từ đầu bảng và loại.
- Kiến thức: mỗi item là một thẻ; mặt trước là loại + mức quan trọng + câu hỏi gợi nhớ (hoặc tiêu đề nếu chưa bổ sung) + ngữ cảnh (bài, topic), mặt sau là tiêu đề + nội dung (quy trình hiển thị theo bước). Lọc theo chương, loại, ngôn ngữ (Việt/Anh/song ngữ), thứ tự (quan trọng trước — mặc định / theo bài).
- Nút/phím: Space lật thẻ, → "Đã nhớ", ← "Chưa nhớ" (thẻ quay lại sau vài thẻ); tiến độ và bộ thẻ lưu trong `localStorage` của trình duyệt.

## 13. Cấu hình (`config.yaml`)

```yaml
paths: {input_dir: data/input, clean_dir: data/clean, work_dir: data/work,
        export_dir: data/export, database: data/learning.db, auth_dir: data/.auth}
default_lang: en
learner:
  cefr_level: null            # A2 | B1 | B2 | C1; null → skill hỏi người dùng
clean:
  paragraph_pause_seconds: 1.5
  max_sentences_per_paragraph: 6
notebooklm:
  by: chapter
  max_sources: 45
  max_words_per_file: 200000
vocabulary:
  batch_size: 100
  contexts_per_candidate: 3
  zipf_threshold_by_level: {A2: 5.0, B1: 4.5, B2: 4.0, C1: 3.5}   # heuristic, cần benchmark
  keyness_min: 4.0                                                # benchmark CCAR
  phrase_min_frequency: 3
  export_min_importance: 70
  enrich_batch_size: 50
knowledge:
  max_lesson_words: 8000
  output_languages: [en, vi]
  enrich_batch_size: 60
  export_min_importance: 50
ai:
  runner: claude_code         # Future: claude_api
  subagent_model: haiku       # model của subagent trích xuất
  tasks_per_subagent: {knowledge_extract: 5, vocab_eval: 2, vocab_enrich: 4, knowledge_enrich: 3}
  max_parallel_subagents: 4
  max_retries: 2
  review_threshold: 0.7
udemy:
  base_url: https://www.udemy.com
  max_concurrency: 4
```

Thay đổi so với Giai đoạn 1: bỏ `chunking.max_words`; thêm `paths.clean_dir`, `paths.work_dir`, `paths.export_dir` và các nhóm mới. `.gitignore` đổi thành bỏ qua toàn bộ `data/`.

## 14. Yêu cầu phi chức năng

- **Xác định & lặp lại được:** Ingestion, Clean, NotebookLM export và Candidate Extraction cho cùng input + version luôn ra cùng output.
- **Idempotent:** chạy lại cùng dữ liệu không tạo bản ghi trùng; chỉ xử lý phần mới/đổi/stale.
- **Phục hồi:** checkpoint theo file (ingestion/clean) và theo task (AI); dừng giữa chừng tiếp tục được.
- **Truy nguồn:** mọi kết quả trích xuất có `transcript_id` + khoảng id câu → timestamp.
- **Không bịa:** ví dụ là câu gốc; nghĩa/giải thích do AI viết phải gắn nguồn và qua validate.
- **Hiệu năng (tham chiếu):** fetch khóa ~400 bài lần đầu ≤ ~3 phút, lần sau ≤ ~15 giây; clean và NotebookLM export toàn khóa ≤ 1 phút trên máy cá nhân.
- **Bảo mật:** token chỉ nằm trong `config.local.yaml`/env, không log, không gửi tới host ngoài Udemy.
- **Môi trường:** Windows/macOS/Linux, Python 3.10–3.14 (giới hạn bởi spaCy), không cần GPU, không cần dịch vụ ngoài ngoài Udemy và Claude.
- **Giấy phép:** danh sách tần suất từ kèm ghi công CC BY-SA 4.0; spaCy/model MIT.

## 15. Roadmap và Milestones

| Giai đoạn | Nội dung | Milestone / nghiệm thu | Trạng thái |
|---|---|---|---|
| 1. Ingestion | login, fetch, import, stats; manifest theo locale | 3 khóa (719 bài) tải và import, chạy lại không trùng | **Xong** |
| 2. Clean Dataset + NotebookLM | Parser trả cue có timestamp; cleaner (rolling caption theo mục 5.1, câu, đoạn); Clean JSON; schema mới + migration; `clean`, `export notebooklm`; viết lại test parser/rolling/cue trùng theo quy tắc mới; cập nhật `.gitignore`, `config.yaml`, SKILL.md, README | Khóa CCAR có Clean JSON; xuất theo chapter vừa giới hạn Free 50 nguồn; người dùng upload thử 1 file lên NotebookLM | Tiếp theo |
| 3. AI Orchestrator + Vocabulary Mode | Task packet, giao thức prepare/ingest, Claude Code runner (subagent Haiku), cache, validate; normalizer; spaCy candidates, danh sách tần suất, keyness, đánh giá AI, xếp hạng, export; `review` cơ bản | Benchmark 5 bài đại diện của khóa CCAR để chốt prompt, rubric, ngưỡng và đo usage; rồi chạy trọn khóa CCAR | |
| 4. Knowledge Mode | Task theo bài, pre-split, phân cấp, item, gom khái niệm, export | Benchmark 5 bài CCAR, rồi chạy trọn khóa CCAR | |
| 5. Hoàn thiện V1 | `review` cho cả hai mode, `stats` theo hướng, `evaluations/report.py` (báo cáo chất lượng + bộ benchmark 5 bài), app `study/`, tài liệu | Tiêu chí mục 16 đạt | |

Điều chỉnh so với thứ tự đề xuất ban đầu: AI Orchestrator được xây cùng Vocabulary Mode (người dùng đầu tiên của nó) thay vì tách riêng; "lưu trữ kiến thức có cấu trúc và liên kết" ở mức cơ bản nằm trong Giai đoạn 4, mức sâu thuộc Future.

**Khóa phát triển và kiểm thử:** các giai đoạn 2–5 sinh dữ liệu và kiểm thử trên **một khóa** — `certified-claude-architect-masterclass-2026` (CCAR: 136 bài, 21 chapter, ~138k từ, caption auto). Hai khóa AWS đã tải không được xử lý AI trong V1 để tiết kiệm usage; trường hợp khóa lớn (> 45 chapter, > 300 bài) được kiểm bằng test dữ liệu giả.

Trước khi tối ưu prompt hoặc ngưỡng, benchmark trên 5 bài đại diện. Ưu tiên chất lượng, khả năng truy nguồn và độ tin cậy hơn số lượng tính năng.

## 16. Phạm vi V1 và tiêu chí nghiệm thu

**V1 (MVP):** Giai đoạn 1–5 ở trên.

V1 hoàn thành khi:
1. Tải/nhập được khóa học > 100 bài; chạy lại không tạo bản ghi trùng.
2. Clean Dataset sinh ra cho mọi transcript, không sửa file gốc, giữ thứ tự câu và timestamp; rolling caption được loại, lặp có chủ đích được giữ (có test cho cả hai).
3. Xuất NotebookLM theo chapter, course và lesson, có index; xuất theo chapter vừa giới hạn 50 nguồn (gộp volume khi > 45 chapter — kiểm bằng test); `--by lesson` cảnh báo khi vượt giới hạn.
4. Vocabulary Mode (trên khóa CCAR) xuất JSON/CSV/Markdown; giữ các thuật ngữ ngắn (`S3`, `EC2`, `IAM`, `API`, `SQL`, `DNS`) và cụm nhiều từ; mọi mục có nguồn; thêm bài mới chỉ tạo task cho ứng viên mới/thay đổi.
5. Knowledge Mode tạo cây Chapter → Lesson → Topic → [Subtopic] → Item cho khóa CCAR; mọi node/item có khoảng câu nguồn hợp lệ.
6. Hai chế độ AI chạy độc lập; dừng giữa chừng tiếp tục được mà không chạy lại task đã `done`.
7. Kết quả AI không qua validate cứng không được lưu; kết quả nghi ngờ được đánh dấu `needs_review`; quyết định duyệt của người dùng không bị ghi đè khi chạy lại.
8. Hoạt động không cần GPU, vector database, embedding hay API key.

## 17. Giả định, ràng buộc và ngoài phạm vi

**Giả định:**
- Transcript nguồn của hai chế độ AI là tiếng Anh; các locale khác dùng cho NotebookLM export.
- Mỗi bài học vừa context của model (đã kiểm chứng trên 3 khóa hiện có).
- Người dùng có Claude subscription dùng được Claude Code.

**Ràng buộc:**
- API Udemy là API nội bộ, không công bố; có thể thay đổi. Chỉ dùng cho khóa đã đăng ký, mục đích cá nhân.
- Throughput AI V1 phụ thuộc giới hạn sử dụng của gói Claude subscription.

**Future (ngoài V1):**
- Claude API runner (batch, concurrency, kiểm soát chi phí).
- Cây chủ đề cấp khóa, liên kết kiến thức xuyên bài/xuyên khóa sâu hơn.
- Xuất Anki và spaced repetition thật (V1 chỉ có app flashcard tĩnh `study/`, mục 12.3).
- Thêm định dạng export/tích hợp; đầu vào PDF/DOCX.
- Chế độ AI cho transcript không phải tiếng Anh.

**Ngoài phạm vi:**
- Vector database, embedding, RAG, LLM/GPU local.
- Dashboard web, đăng nhập/phân quyền, đồng bộ đám mây.
- Hệ thống spaced repetition riêng, tạo audio.
- Tích hợp trực tiếp với NotebookLM (upload tự động).

## 18. Open Questions

1. **Hiển thị Markdown trong NotebookLM:** Google không công bố cách viewer hiển thị heading. Cần người dùng upload thử 1 file xuất ở Giai đoạn 2 để chốt định dạng (có thể cần thêm tùy chọn `.txt`).
2. **Giới hạn Claude subscription:** chưa biết usage thực tế của một khóa (ước lượng thô cho CCAR: Knowledge ~10 subagent Haiku × 15 bài; Vocabulary vài lô); đo ở benchmark Giai đoạn 3 để chốt `ai.tasks_per_subagent`, `ai.max_parallel_subagents` và thời điểm cần Claude API runner.
3. **Chất lượng Haiku:** Haiku là mặc định cho subagent trích xuất; nếu benchmark cho thấy tỉ lệ `invalid`/`needs_review` cao ở một mode, cân nhắc đổi `ai.subagent_model` cho riêng mode đó.
4. **Ngưỡng lọc từ:** ánh xạ CEFR → Zipf, `keyness_min` và rubric điểm `importance` là heuristic; chốt sau benchmark.
5. **Khái niệm trùng tên giữa các khóa:** V1 gom theo tên chuẩn hóa trên toàn hệ thống; cần xác nhận có tách theo khóa khi cùng tên khác nghĩa không.
6. **Chất lượng caption tự động:** một số bài chỉ có caption auto; ảnh hưởng tới tách câu và trích xuất cần đánh giá trong benchmark.
7. **Ngưỡng rolling caption:** dung sai 0,05s và cue "nháy" < 0,1s dựa trên mô tả caption cuộn kiểu YouTube; caption Udemy thật hiện chưa có dạng cuộn. Kiểm tra lại khi gặp nguồn caption cuộn thật.
