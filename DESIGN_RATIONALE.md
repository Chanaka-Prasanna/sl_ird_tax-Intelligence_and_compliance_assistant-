# Design Rationale Document

## Tax Intelligence & Compliance Assistant

---

## 1. Architecture Overview

### Agentic RAG System

**Rationale:** Traditional RAG systems retrieve and generate immediately. Our **agentic approach** uses LangGraph to make intelligent decisions at each step—whether to retrieve, when documents are relevant, and when to rewrite queries. This reduces hallucinations and improves answer quality by validating relevance before generation.

### Separation of Concerns

- **Frontend (Next.js):** Handles UI/UX only
- **Backend (FastAPI):** Manages business logic, AI orchestration, and data ingestion
- **Vector Store (ChromaDB):** Persists document embeddings separately

**Rationale:** Clear separation enables independent scaling, technology swaps, and easier testing. Frontend can be replaced without touching AI logic.

---

## 2. Backend Design Decisions

### 2.1 Design Patterns

#### **Factory Pattern** (`factories.py`)

```python
DocumentLoaderFactory.create_loader("pdf")
VectorStoreFactory.create_vector_store("chroma", ...)
```

**Rationale:**

- **Extensibility:** Adding new loaders (Word, Excel) or vector stores (Pinecone, Weaviate) requires only adding factory methods
- **Testability:** Mock factories for unit testing without real dependencies
- **Configuration centralization:** All object creation logic in one place

#### **Abstract Base Classes** (`interfaces.py`)

```python
class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: str, source_url: str) -> List
```

**Rationale:**

- **Enforces contracts:** All loaders must implement `load()` method
- **Polymorphism:** Services work with interfaces, not concrete implementations
- **Type safety:** Python's type system ensures correct usage

#### **Service Layer Pattern** (`services.py`)

```python
class DocumentIngestionService:
    def ingest_documents(self, file_paths_with_urls)
```

**Rationale:**

- **Business logic isolation:** Core operations separated from API endpoints
- **Reusability:** Services can be used in CLI, API, or background jobs
- **Testability:** Services can be unit tested without FastAPI

#### **Dependency Injection**

```python
class DocumentIngestionService:
    def __init__(self, document_loader, text_splitter, vector_store):
```

**Rationale:**

- **Loose coupling:** Services don't create their dependencies
- **Testing:** Inject mocks for isolated unit tests
- **Flexibility:** Swap implementations at runtime

---

### 2.2 LangGraph Workflow Design

#### **State Machine Architecture**

```
generate_query_or_respond → retrieve → grade_documents
                                      ↓              ↓
                                 generate_answer  rewrite_question
                                      ↓              ↓
                                     END     <-> (retry retrieve)
```

**Rationale:**

- **Explicit control flow:** No hidden decision logic—graph visualizes the entire process
- **Error recovery:** `rewrite_question` node provides graceful retry mechanism
- **Observability:** Each node is a checkpoint for debugging and logging
- **Stateful conversations:** Checkpointer maintains conversation history across turns

#### **Tool-based Retrieval**

Model decides whether to call `retriever_tool` or respond directly.

**Rationale:**

- **Avoids unnecessary retrieval:** Simple greetings or clarifications don't need database search
- **Cost optimization:** Fewer embedding calls when not needed
- **Natural conversation:** Model can engage in dialogue without always searching

#### **Document Grading**

After retrieval, `grade_documents` checks relevance before generation.

**Rationale:**

- **Prevents hallucinations:** Don't generate answers from irrelevant context
- **Query refinement:** Triggers rewrite if initial retrieval fails
- **Quality assurance:** Acts as a guard before expensive generation step

---

### 2.3 Query Optimization

#### **Acronym Expansion** (`tools.py`)

```python
TAX_ACRONYMS = {"SET": "Statement of Estimated Tax Payable", ...}
```

**Rationale:**

- **Disambiguation:** "SET" (acronym) vs "set" (common word) causes false matches
- **Domain knowledge injection:** Tax-specific understanding improves retrieval
- **Transparent augmentation:** Happens at query time, doesn't pollute documents

#### **Increased Retrieval Count** (`k=6`)

**Rationale:**

- **Better coverage:** More documents increase chance of relevant match
- **Acronym variations:** Different documents may use full form or acronym
- **Ranking confidence:** Model has more context to grade relevance

---

### 2.4 Structured Output

```python
class StructuredAnswer(BaseModel):
    content: str
    sources: List[Source]
```

**Rationale:**

- **Consistent formatting:** Every response has citations in same format
- **Type safety:** Pydantic validates LLM output structure
- **Post-processing:** Can deduplicate sources, format links programmatically
- **API reliability:** Guaranteed response schema for frontend

---

### 2.5 Technology Choices

| Technology        | Rationale                                                                     |
| ----------------- | ----------------------------------------------------------------------------- |
| **FastAPI**       | Async support, automatic OpenAPI docs, Pydantic integration, fast performance |
| **LangGraph**     | State machine design, checkpointing, built-in tool support, visual debugging  |
| **ChromaDB**      | Local-first, no external services, easy setup, good for prototypes            |
| **Google Gemini** | Fast, cheap, large context window (1M tokens), good for RAG                   |
| **PyMuPDF**       | Extracts tables as markdown, preserves structure, handles complex PDFs        |
| **Tiktoken**      | Token-based splitting prevents mid-word cuts, respects model context limits   |

---

## 3. Frontend Design Decisions

### 3.1 Next.js Architecture

#### **Client-Side Rendering** (`"use client"`)

**Rationale:**

- **Real-time interactions:** Chat requires dynamic state updates without page refreshes
- **WebSocket readiness:** Client components can easily add streaming later
- **Form handling:** File uploads need client-side logic for progress tracking

#### **Server Components (where possible)**

Layout and static pages use server components.

**Rationale:**

- **SEO optimization:** Pre-rendered HTML for search engines
- **Reduced JS bundle:** Less code sent to browser
- **Security:** API keys never exposed to client

---

### 3.2 UI/UX Patterns

#### **Markdown Rendering** (`react-markdown`)

**Rationale:**

- **Rich formatting:** Tables, lists, bold text improve readability
- **Citation links:** Clickable `[1]` references to source documents
- **Code blocks:** Future support for tax calculation examples

#### **Auto-scroll to Bottom**

```typescript
useEffect(() => scrollToBottom(), [messages]);
```

**Rationale:**

- **Chat convention:** Users expect latest message to be visible
- **Mobile friendliness:** Automatic scroll on small screens

#### **Session-based Thread IDs**

```typescript
const [threadId] = useState(() => `session_${Date.now()}_${Math.random()}`);
```

**Rationale:**

- **Conversation continuity:** Follow-up questions reference previous context
- **Multi-tab support:** Each browser tab has independent conversation
- **No authentication:** Simple demo without user management

---

### 3.3 Admin Page Design

#### **Batch Upload with URL Mapping**

Each PDF has a corresponding source URL field.

**Rationale:**

- **Source provenance:** Citations link back to official IRD documents
- **Trust building:** Users can verify information at the source
- **Audit trail:** Track which documents contributed to answers

#### **Inline Progress Feedback**

**Rationale:**

- **User confidence:** Large PDFs take time—show activity during upload
- **Error handling:** Immediate feedback if upload fails
- **Success metrics:** Display number of document chunks ingested

---

## 4. Special Design Choices

### 4.1 AIMessage for Rewrite Node

`rewrite_question` returns `AIMessage`, not `HumanMessage`.

**Rationale:**

- **Detect internal routing:** Next node knows this is rewritten query, not user input
- **Prevent polite responses:** Model doesn't thank itself for clarification
- **State management:** Clear signal in message history for debugging

### 4.2 No Thank-You Instruction

System prompt added when processing rewritten queries.

**Rationale:**

- **User experience:** "Thank you for the clarification" is confusing when user didn't clarify
- **Professional tone:** Direct questions sound more competent
- **Context awareness:** Model knows it's in error-recovery mode

### 4.3 Section Extraction Rules

Long prompt rules for extracting sections from documents.

**Rationale:**

- **Citation precision:** "(b) Business of export" is not a section—it's a list item
- **User navigation:** Main section numbers help users find content in PDF
- **Avoid noise:** Page headers and document titles pollute citations

### 4.4 In-Memory Checkpointer

**Rationale:**

- **Development simplicity:** No database setup required for demos
- **Fast iteration:** Instant startup without persistence overhead
- **Stateless deployment:** Can be replaced with Redis/Postgres for production

---

## 5. Trade-offs and Future Considerations

### Current Limitations

1. **No authentication:** Single-user system for demo purposes
2. **In-memory state:** Conversations lost on server restart
3. **No streaming:** User waits for full response
4. **Local vector store:** Not scalable beyond thousands of documents

### Production Readiness Path

1. **Add authentication:** JWT tokens, user-specific conversations
2. **PostgreSQL checkpointer:** Persistent conversation history
3. **Streaming responses:** Server-Sent Events for progressive display
4. **Pinecone/Weaviate:** Cloud vector store for scale
5. **Observability:** Add logging, tracing, and metrics (LangSmith)
6. **Rate limiting:** Prevent abuse of expensive LLM calls

---

## 6. Summary

This design prioritizes:

- **Modularity:** Swap components via interfaces and factories
- **Reliability:** Validate before generating, retry on failure
- **Maintainability:** Clear separation of concerns, explicit control flow
- **User experience:** Accurate citations, contextual clarifications, clean UI
- **Developer experience:** Type safety, visual debugging, simple setup

The agentic architecture with query optimization and structured outputs creates a **trustworthy** system for tax document Q&A, where accuracy and provenance are critical.
