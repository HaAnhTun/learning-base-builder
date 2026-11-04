# NHIỆM VỤ: REVIEW VÀ CẬP NHẬT SPEC DỰ ÁN

Bạn đóng vai trò Senior Software Architect, chịu trách nhiệm đánh giá kiến trúc và cập nhật tài liệu đặc tả dự án (SPEC).

Nhiệm vụ: Đọc SPEC hiện tại, đối chiếu với định hướng sản phẩm mới bên dưới và cập nhật trực tiếp vào tài liệu.

**Lưu ý: Chỉ review và cập nhật tài liệu SPEC. KHÔNG triển khai code trong nhiệm vụ này.**

## 1. Khảo sát dự án hiện tại

Trước khi chỉnh sửa:

1. Tìm và đọc SPEC hiện tại cùng các tài liệu liên quan.
2. Hiểu mục tiêu, kiến trúc, phạm vi, công nghệ và kế hoạch triển khai hiện có.
3. Xác định những yêu cầu đã lỗi thời, thiếu sót, mâu thuẫn hoặc chưa phù hợp với định hướng mới.
4. Giữ lại những quyết định kiến trúc vẫn còn hợp lý. Không viết lại toàn bộ SPEC nếu không cần thiết.

## 2. Định hướng sản phẩm mới

Dự án có mục tiêu xử lý tài liệu học tập, đặc biệt là transcript khóa học Udemy định dạng VTT, để tạo thành một bộ dữ liệu học tập sạch, có cấu trúc và có thể tái sử dụng.

Hệ thống cần hỗ trợ 3 hướng sử dụng độc lập.

### Hướng 1: Chuẩn bị dữ liệu cho NotebookLM

Mục tiêu: Làm sạch transcript và xuất tài liệu để người dùng đưa lên NotebookLM.

Luồng xử lý:

`Raw VTT → Transcript Cleaner → Clean Markdown Dataset → NotebookLM`

Yêu cầu:

- Làm sạch và chuẩn hóa nội dung VTT.
- Giữ nguyên ranh giới giữa các bài học.
- Bảo toàn metadata của khóa học và bài học.
- Xuất dữ liệu thành các file Markdown dễ đọc.
- Hỗ trợ xuất từng bài học hoặc toàn bộ khóa học.
- Tạo file index để điều hướng giữa các bài học.
- Không yêu cầu AI xử lý dữ liệu trước khi xuất.
- NotebookLM là công cụ bên ngoài sử dụng dữ liệu đầu ra, không phải thành phần bắt buộc của hệ thống.

Người dùng có thể tự đưa dữ liệu đã làm sạch lên NotebookLM và sử dụng prompt tùy ý để tóm tắt, giải thích, đặt câu hỏi hoặc phục vụ các hoạt động học tập khác.

### Hướng 2: Trích xuất từ vựng (Vocabulary Extraction)

Mục tiêu: Trích xuất từ vựng và thuật ngữ có giá trị từ transcript khóa học.

Luồng xử lý:

`Clean Dataset → Candidate Extraction → Normalization & Deduplication → AI Evaluation → Important Vocabulary`

Yêu cầu:

1. Trích xuất danh sách từ và cụm từ ứng viên từ dữ liệu đã làm sạch.
2. Chuẩn hóa dạng từ và loại bỏ các mục trùng lặp.
3. Nhận diện những từ phổ thông, dễ hiểu hoặc ít giá trị để giảm nhiễu.
4. Giữ lại các thuật ngữ kỹ thuật, từ viết tắt, chữ viết tắt và cụm từ chuyên ngành.
5. Gửi danh sách ứng viên kèm ngữ cảnh cho AI đánh giá.
6. AI lựa chọn và xếp hạng từ vựng dựa trên:
   - Mức độ liên quan đến nội dung khóa học.
   - Tầm quan trọng trong lĩnh vực chuyên môn.
   - Tần suất và ý nghĩa trong ngữ cảnh.
   - Giá trị ứng dụng thực tế.
7. Xuất kết quả thành dữ liệu từ vựng có cấu trúc.

Các lưu ý quan trọng:

- Không sử dụng độ dài ký tự làm tiêu chí lọc chính.
- Những thuật ngữ ngắn như API, IAM, SQL, S3, EC2, DNS vẫn phải được giữ lại.
- Phải hỗ trợ trích xuất cụm từ nhiều từ, không chỉ từ đơn.
- Lưu nguồn tham chiếu đến khóa học, bài học và ngữ cảnh transcript.
- AI nên tập trung đánh giá và ưu tiên các ứng viên thay vì xử lý toàn bộ transcript thô một cách thiếu kiểm soát.

Vocabulary Extraction phải là một chế độ xử lý độc lập.

### Hướng 3: Trích xuất kiến thức (Knowledge Extraction)

Mục tiêu: Chuyển transcript khóa học thành hệ thống kiến thức có cấu trúc, có thể tái sử dụng.

Luồng xử lý:

`Clean Dataset → Semantic Segmentation → Topic Identification → Concept Extraction → Structured Knowledge`

Yêu cầu:

1. Xử lý transcript theo từng bài học.
2. Xác định các chủ đề và chủ đề con có ý nghĩa trong mỗi bài.
3. Chia nội dung dựa trên ranh giới ngữ nghĩa, không chỉ dựa vào số lượng token cố định.
4. Trích xuất các thành phần kiến thức phù hợp, bao gồm:
   - Khái niệm.
   - Định nghĩa và giải thích.
   - Các ý chính.
   - Quy trình và cách thức hoạt động.
   - Ví dụ.
   - Ưu điểm và nhược điểm.
   - Mối quan hệ giữa các khái niệm.
   - Cảnh báo và giới hạn quan trọng.
5. Tổ chức kiến thức theo cấu trúc phân cấp.

Ví dụ:

Khóa học: AWS SQS Fundamentals

- Introduction
- Queue Types
  - Standard Queue
  - FIFO Queue
- Message Lifecycle
  - Send Message
  - Receive Message
  - Delete Message
- Reliability
  - Visibility Timeout
  - Dead Letter Queue
  - Retry Mechanism
- Performance
  - Long Polling
  - Batching

Đây chỉ là ví dụ minh họa. Hệ thống phải tự xác định chủ đề dựa trên nội dung transcript thực tế, không phụ thuộc vào danh mục được định nghĩa cứng.

Mỗi bản ghi kiến thức phải có nguồn tham chiếu để người dùng truy ngược về bài học và nội dung transcript gốc.

Knowledge Extraction phải là một chế độ xử lý độc lập với Vocabulary Extraction.

## 3. Kiến trúc dùng chung

Hai hướng Vocabulary Extraction và Knowledge Extraction nên sử dụng chung những thành phần AI Processing có thể tái sử dụng.

Đánh giá và thiết kế các thành phần phù hợp, ví dụ:

- Transcript Cleaner.
- Document Parser.
- Dataset Manager.
- Candidate Extractor.
- Semantic Segmenter.
- AI Orchestrator.
- Vocabulary Extraction Mode.
- Knowledge Extraction Mode.
- Source Tracking.
- Result Storage.
- Cache và Checkpoint Management.
- Export Manager.

Không bắt buộc phải đưa tất cả thành phần trên vào kiến trúc nếu chúng không thực sự cần thiết.

Nguyên tắc:

- Tránh trùng lặp logic xử lý giữa hai chế độ.
- Tái sử dụng các thành phần chung khi hợp lý.
- Giữ riêng workflow và output schema của Vocabulary Mode và Knowledge Mode vì mục đích của chúng khác nhau.

## 4. Ràng buộc kỹ thuật và nguyên tắc thiết kế

Review SPEC hiện tại và đảm bảo tài liệu phản ánh các nguyên tắc sau.

### Xử lý dữ liệu xác định (Deterministic Processing)

- Parsing và cleaning VTT chủ yếu sử dụng Python.
- Làm sạch dữ liệu không cần phụ thuộc vào AI.
- Không chỉnh sửa hoặc ghi đè file VTT gốc.
- Tạo file đã làm sạch dưới dạng dữ liệu dẫn xuất.
- Bảo toàn thứ tự câu và những nội dung lặp lại có ý nghĩa.
- Loại bỏ timestamp, định dạng VTT và các đoạn subtitle lặp do cơ chế rolling captions.
- Tránh xóa nhầm những nội dung được lặp lại có chủ đích.

### Xử lý AI

- AI được sử dụng cho các tác vụ cần hiểu ngữ nghĩa, đánh giá từ vựng và trích xuất kiến thức.
- Giai đoạn đầu ưu tiên sử dụng Claude Code / Claude subscription khi phù hợp.
- Python xử lý các tác vụ xác định và điều phối quy trình.
- Không giả định rằng sử dụng Claude Code đồng nghĩa với việc inference chạy trên LLM hoặc GPU local.
- Thiết kế mở để có thể tích hợp Claude API trong tương lai nhằm hỗ trợ batch processing, concurrency, retry và kiểm soát chi phí.

### Chunking và Semantic Segmentation

- Không mặc định một chunk size cố định cho mọi trường hợp.
- Vocabulary Extraction và Knowledge Extraction có thể cần chiến lược phân đoạn khác nhau.
- Knowledge Extraction phải ưu tiên ranh giới ngữ nghĩa.
- Tránh chia cắt một khái niệm hoặc phần giải thích giữa chừng.
- Hỗ trợ chia nhỏ thêm khi một segment vượt quá giới hạn context của model.
- Mỗi segment phải giữ được nguồn tham chiếu.

### Lưu trữ và chất lượng dữ liệu

- Tách biệt dữ liệu raw, cleaned và extracted.
- Sử dụng định dạng có cấu trúc, có thể tái sử dụng như JSON và Markdown.
- Xem xét mối quan hệ giữa course, lesson, segment, vocabulary và concept.
- Không đưa vector database, embedding, RAG hoặc hạ tầng LLM local vào V1 nếu chưa có yêu cầu thực sự cần thiết.

### Khả năng mở rộng

Clean Dataset phải có khả năng tái sử dụng cho:

- NotebookLM.
- Claude và các AI Assistant khác.
- Công cụ trích xuất từ vựng.
- Công cụ trích xuất kiến thức.
- Các hệ thống flashcard hoặc Anki trong tương lai.

Không đưa Anki hoặc flashcard generation thành yêu cầu cốt lõi của V1.

## 5. Phạm vi và thứ tự triển khai

Cập nhật SPEC với roadmap thực tế.

Thứ tự đề xuất:

1. Transcript Ingestion và quản lý dữ liệu gốc.
2. Transcript Cleaning và tạo Clean Dataset.
3. Xuất Markdown tương thích NotebookLM.
4. Xây dựng Vocabulary Extraction Mode.
5. Xây dựng Knowledge Extraction Mode.
6. Xây dựng hệ thống lưu trữ kiến thức có cấu trúc và liên kết dữ liệu.
7. Bổ sung các hình thức export và tích hợp khác trong tương lai.

Hãy đánh giá và điều chỉnh thứ tự nếu kiến trúc hiện tại cho thấy phương án khác hợp lý hơn.

Phân loại rõ:

- Yêu cầu thuộc V1 / MVP.
- Tính năng dự kiến trong tương lai.
- Những nội dung nằm ngoài phạm vi dự án.

Tránh đưa quá nhiều tính năng vào phiên bản đầu tiên.

## 6. Các nội dung SPEC cần cập nhật

Sau khi review tài liệu hiện tại:

1. Cập nhật Product Overview và Product Goals.
2. Cập nhật Functional Requirements.
3. Cập nhật System Architecture và Data Flow.
4. Cập nhật trách nhiệm của từng module.
5. Cập nhật Data Model và Output Format nếu cần.
6. Cập nhật workflow cho cả 3 hướng sử dụng.
7. Cập nhật Non-functional Requirements.
8. Cập nhật Implementation Roadmap và Milestones.
9. Cập nhật Assumptions, Constraints và Out of Scope.
10. Loại bỏ hoặc điều chỉnh những yêu cầu cũ mâu thuẫn với định hướng mới.

Nếu dự án đang sử dụng sơ đồ kiến trúc hoặc sơ đồ luồng xử lý, hãy cập nhật chúng để thể hiện rõ 3 hướng sử dụng độc lập.

## 7. Các nguyên tắc bắt buộc

- Không triển khai code.
- Không tạo thêm tài liệu không cần thiết nếu có thể cập nhật SPEC hiện tại.
- Không tự ý thay đổi các quyết định kiến trúc hợp lý mà không giải thích.
- Không đưa công nghệ vào dự án chỉ vì chúng phổ biến.
- Không mặc định mọi tính năng đều phải sử dụng AI.
- Không khiến NotebookLM phụ thuộc vào AI Extraction Pipeline của hệ thống.
- Không gộp Vocabulary Mode và Knowledge Mode thành một workflow không phân biệt được.
- Không đưa Anki, flashcard, RAG hoặc vector database thành thành phần bắt buộc của V1.

Nếu có quyết định kiến trúc quan trọng chưa đủ thông tin để xác định, hãy ghi nhận thành Open Question thay vì tự suy đoán.

## 8. Báo cáo sau khi hoàn thành

Sau khi cập nhật SPEC, cung cấp báo cáo ngắn gọn gồm:

1. Những file đã kiểm tra.
2. Những file đã chỉnh sửa.
3. Những thay đổi quan trọng.
4. Các yêu cầu mới được bổ sung.
5. Các yêu cầu cũ đã loại bỏ hoặc điều chỉnh.
6. Những quyết định kiến trúc cần xác nhận thêm.
7. Các mâu thuẫn hoặc rủi ro còn tồn tại.

**Tiêu chí hoàn thành:** SPEC mới phải mô tả rõ một nền tảng dữ liệu học tập dùng chung, hỗ trợ ba hướng sử dụng độc lập: chuẩn bị dữ liệu cho NotebookLM, trích xuất từ vựng và trích xuất kiến thức.