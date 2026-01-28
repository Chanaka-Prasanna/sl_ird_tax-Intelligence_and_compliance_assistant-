from dotenv import load_dotenv
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Literal
from langchain.messages import HumanMessage
from langchain.chat_models import init_chat_model
from tools import retriever_tool

load_dotenv()
model = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=0)

GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)

REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks about tax regulations and compliance. "
    "CRITICAL RULES:\n"
    "1. Answer ONLY based on the retrieved context provided below - do not use external knowledge\n"
    "2. If the context does not contain the answer, clearly state: 'I don't have this information in the available documents'\n"
    "3. NEVER provide speculative, interpretative, or advisory language\n"
    "4. Present facts exactly as stated in the source documents without adding personal opinions or recommendations\n"
    "5. If tables are present in the context, reproduce them as markdown tables to maintain clarity\n"
    "6. If the user explicitly asks to compare across different years or documents, analyze and compare the information from multiple sources\n"
    "7. Only provide comparisons when explicitly requested by the user - otherwise focus on answering the specific question\n\n"
    "Provide a comprehensive and descriptive answer with sufficient detail to fully address the user's query. "
    "Include relevant examples, explanations, and specific details from the context. "
    "Adjust the length and depth of your answer based on the complexity of the question.\n\n"
    "CITATION USAGE RULES IN YOUR ANSWER:\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "✓ CORRECT: 'The following rates apply [1]:'\n"
    "  - Rate 1\n"
    "  - Rate 2\n"
    "  - Rate 3\n\n"
    "✗ WRONG: DO NOT DO THIS:\n"
    "  - Rate 1 [1]\n"
    "  - Rate 2 [1]\n"
    "  - Rate 3 [1]\n\n"
    "RULE: Place citations ONLY at section headings or topic introductions, NEVER after individual list items.\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Question: {question} \n\n"
    "Context: {context}\n\n"
    "══════════════════════════════════════════════\n"
    "SOURCES SECTION FORMATTING (CRITICAL)\n"
    "══════════════════════════════════════════════\n\n"
    "After your answer, create a sources section using this EXACT format:\n\n"
    "**Sources:**\n\n"
    "[1]- [Document Name](actual_url_here) - Page X - Section Title\n\n"
    "[2]- [Document Name](actual_url_here) - Page Y - Section Title\n\n"
    "FORMAT RULES:\n"
    "• Start with [number]- (bracket number bracket dash)\n"
    "• Document name must be clickable: [Document Name](url)\n"
    "• Use single dash - between elements\n"
    "• Format: [X]- [Name](url) - Page Y - Section (Section is optional)\n"
    "• Each citation on a new line with blank line after it\n"
    "• NO duplicates - each unique source listed only once\n\n"
    "EXAMPLE:\n"
    "[1]- [Tax Guide 2023](https://ird.gov.lk/tax2023.pdf) - Page 15 - 12.2 Company Tax Rates\n\n"
    "[2]- [Corporate Tax Manual](https://ird.gov.lk/manual.pdf) - Page 42\n\n"
    "Instructions for creating citations:\n"
    "1. Extract 'source_url' from metadata - use this as the clickable URL\n"
    "2. Extract clean document name from 'source' metadata (remove path and .pdf extension)\n"
    "3. Extract page number from metadata\n"
    "4. Extract EXACT section title from document context (optional if not clear)\n"
    "5. Include section numbers if present (e.g., '12.2 Company Tax Rates')\n"
    "6. Each citation must be UNIQUE - check for duplicates before listing\n"
    "7. Put a blank line after EACH citation\n\n"
    "VERIFICATION CHECKLIST:\n"
    "□ Are citations only at headings, NOT on every list item?\n"
    "□ Is format [X]- [Name](url) - Page Y - Section?\n"
    "□ Is document name clickable with actual URL?\n"
    "□ Is each citation on its own line with blank line after?\n"
    "□ Are all sources unique with NO duplicates?\n\n"
    "MANDATORY DISCLAIMER: End your response with:\n"
    "---\n"
    "*Disclaimer: This response is based solely on IRD-published documents and is not professional tax advice. "
    "Please consult a qualified tax professional for personalized guidance.*"
)

class GradeDocuments(BaseModel):  
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )



load_dotenv()

def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """
    response = (
        model
        .bind_tools([retriever_tool]).invoke(state["messages"])  
    )
    return {"messages": [response]}


def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    messages = state["messages"]
    question = next((m.content for m in reversed(messages) if hasattr(m, 'type') and m.type == 'human'), messages[0].content)
    context = messages[-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (
        model
        .with_structured_output(GradeDocuments).invoke(  
            [{"role": "user", "content": prompt}]
        )
    )
    score = response.binary_score

    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"
    

def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = next((m.content for m in reversed(messages) if hasattr(m, 'type') and m.type == 'human'), messages[0].content)
    prompt = REWRITE_PROMPT.format(question=question)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}

def generate_answer(state: MessagesState):
    """Generate an answer."""
    messages = state["messages"]
    question = next((m.content for m in reversed(messages) if hasattr(m, 'type') and m.type == 'human'), messages[0].content)
    context = messages[-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


