# Vietnamese translation guide (every mode that writes Vietnamese)

The reader is a Vietnamese software engineer. Each Vietnamese text should read as if a Vietnamese colleague wrote it
for this AI/software course: same meaning, Vietnamese word order, Vietnamese phrasing.

## Method — translate the meaning, then rewrite

1. Read the whole English sentence and decide what it means **in this course** (AI agents, prompts, APIs, software).
2. Write the Vietnamese from that meaning. Reorder, split or merge clauses freely; drop words Vietnamese does not need.
3. Re-read your Vietnamese alone. Rewrite any phrase that only makes sense when translated back into English, and any
   word used in its everyday dictionary sense instead of its technical sense.

## Technical terms

Keep established technical terms in English: agent, subagent, prompt, system prompt, token, context window, tool,
tool call, hook, schema, API, MCP, server, client, eval, pipeline, workflow, orchestrator, payload, cache, few-shot,
fine-tuning, embedding, batch, retry, log, framework, plus product and proper names (Claude, Claude Code, Anthropic).
Add a short Vietnamese gloss in parentheses when it helps a learner: "agent con (subagent)".

That list is the whole exception. Every other English word is translated, including role and action words the
course uses as jargon: actor → bên xử lý, reviewer → người duyệt, supervisor → người giám sát, escalate → chuyển lên
(người/bên có thẩm quyền), handoff → bàn giao, routing → định tuyến, loop closure → khép vòng phản hồi. A named idea
from the course becomes a Vietnamese phrase with the English name in parentheses the first time:
"Khép vòng phản hồi (loop closure)", "Payload bàn giao (handoff payload)".

Copy names, acronyms, numbers and code exactly as the English writes them (CCAF stays CCAF); never swap in a
similar-looking acronym or a name from elsewhere in the course.

## Words with a technical sense in this course

| English | Vietnamese here | Trap (everyday sense) |
|---|---|---|
| agent, subagent, child agent | agent, subagent, agent con | đại lý |
| fact (in a prompt / memory) | dữ kiện, thông tin | sự kiện (= event) |
| noise (in context) | thông tin nhiễu, thông tin thừa | tiếng ồn |
| business rules / logic | quy tắc nghiệp vụ / logic nghiệp vụ | quy tắc kinh doanh |
| domain | lĩnh vực, nghiệp vụ | miền |
| downstream / upstream | các bước phía sau / phía trước | xuống dòng |
| propagate | lan sang, truyền tới | lan truyền xuống |
| clean (design, context) | gọn gàng, tách bạch | sạch sẽ |
| verbose | dài dòng, nhiều chữ | chi tiết |
| robust | ổn định, chịu lỗi tốt | mạnh mẽ |
| address (a problem) | giải quyết, xử lý | địa chỉ |
| surface (verb) | đưa ra, làm lộ ra | bề mặt |
| leverage | tận dụng | đòn bẩy |
| safety-critical | ảnh hưởng trực tiếp đến an toàn | an toàn quan trọng |
| overkill | quá mức cần thiết | quá mức giết |
| worth it / worth their time | đáng làm / đáng để bỏ thời gian | đáng giá thời gian |
| pass rate | tỷ lệ đạt | tỷ lệ vượt qua |
| ground truth | đáp án chuẩn, dữ liệu chuẩn | sự thật nền |
| state / stateless | trạng thái / không lưu trạng thái | tiểu bang |
| We'll cover… / In this lesson… | Bài này nói về… | Chúng tôi sẽ đề cập… |
| X is only as good as Y | X tốt hay không là do Y | X chỉ tốt như Y |
| draw the line(s) | phân định rõ | vẽ đường |
| be part of | nằm trong, là một phần của | là phần của |
| one-way street | chỉ đi một chiều, không có phản hồi | con phố một chiều |

## Sentence rules

- Prefer active voice: "X is created by Y" → "Y tạo ra X" (not "X được tạo bởi Y").
- Use "các/những" only when plurality matters; drop "của nó/của họ" when the owner is obvious.
- Repeat the noun or omit the subject instead of using "nó" for things.
- Vietnamese modifier order: "persistent fact block" → "khối dữ kiện cố định"; "eval case" → "trường hợp eval".
- Translate idioms by meaning: "make a difference" → "có tác dụng thật sự"; "keep things clean" → "giữ mọi thứ
  gọn gàng, tách bạch".
- Vietnamese titles and questions use sentence case — capitalise only the first word and names ("Khép vòng phản hồi",
  not "Khép Vòng Phản Hồi").
- Split a long English sentence into two Vietnamese sentences when that reads better.

## Examples

| English | Word by word (rewrite this) | Natural |
|---|---|---|
| a sub-agent spawned by a parent agent to handle a delegated task | một đại lý con được tạo bởi đại lý cha để xử lý một nhiệm vụ được phân công | agent con (subagent) do agent cha tạo ra để làm một phần việc được giao |
| Don't dump your entire context window into the handoff payload, because that creates noise. | Không đổ toàn bộ cửa sổ ngữ cảnh vào gói bàn giao, vì điều đó tạo ra tiếng ồn. | Đừng nhét cả context window vào payload bàn giao, vì như vậy chỉ thêm thông tin nhiễu. |
| …validates outputs against business rules before results propagate downstream. | …xác thực kết quả đầu ra so với quy tắc kinh doanh trước khi kết quả lan truyền xuống dòng. | …kiểm tra kết quả theo các quy tắc nghiệp vụ trước khi chuyển sang các bước phía sau. |
| Without loop closure, escalation is a one-way street and the agent never learns what was decided. | Khi không có loop closure, escalation là một chiều và agent không bao giờ biết quyết định gì đã được đưa ra. | Nếu không khép vòng phản hồi, việc chuyển lên chỉ đi một chiều: agent không bao giờ biết người duyệt đã quyết định gì. |
| Reviews make a difference by helping others decide if the course is worth their time. | Các đánh giá tạo ra sự khác biệt bằng cách giúp người khác quyết định liệu khóa học có đáng giá thời gian của họ. | Đánh giá của bạn giúp người khác quyết định khóa học có đáng để bỏ thời gian hay không. |
