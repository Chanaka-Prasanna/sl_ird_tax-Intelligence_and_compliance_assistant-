from dotenv import load_dotenv
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Literal, List
from langchain.messages import HumanMessage, AIMessage
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
    "CITATION USAGE IN ANSWER:\n"
    "- Use inline citation numbers (e.g., [1], [2]) ONLY at section headings or when introducing a topic\n"
    "- DO NOT add citations after every list item\n"
    "- When presenting a list from the same source, cite once in the heading\n"
    "- Example: 'The following rates apply [1]:' then list items without individual citations\n\n"
    "Question: {question}\n\n"
    "Context: {context}\n\n"
    "SOURCES EXTRACTION:\n"
    "For each unique source you reference:\n"
    "1. Extract 'source' from metadata and clean it (remove path, remove .pdf extension)\n"
    "2. Extract 'source_url' from metadata (the actual URL)\n"
    "3. Extract 'page' number from metadata\n"
    "4. Extract the section from document BODY CONTENT ONLY:\n"
    "   \n"
    "   STRICT RULES FOR SECTION EXTRACTION:\n"
    "   ════════════════════════════════════\n"
    "   ✓ ONLY extract MAIN SECTION HEADINGS with DECIMAL NUMBERING: '12.2', '12.3', '4.1', '13', '2.5.1'\n"
    "   ✓ Extract the section number and its title (e.g., '12.2 For the second six months period')\n"
    "   ✓ Valid section patterns: '1.', '2.3', '12.3.1', 'Section 5', 'Part III'\n"
    "   \n"
    "   ✗ NEVER extract LIST ITEMS as sections:\n"
    "   • Items starting with (a), (b), (c), (d), etc. - these are SUB-POINTS, not sections\n"
    "   • Items starting with (i), (ii), (iii), (iv), etc. - these are SUB-POINTS, not sections\n"
    "   • Items starting with (1), (2), (3), etc. in parentheses - these are LIST ITEMS\n"
    "   • Bullet points or dash items\n"
    "   • Individual tax rates or percentages (e.g., '24% Tax Rate')\n"
    "   \n"
    "   ✗ NEVER extract:\n"
    "   • Page headers (text that appears at top of page repeatedly)\n"
    "   • Page footers (text at bottom of page)\n"
    "   • Document titles (e.g., 'GUIDE TO CORPORATE RETURN OF INCOME TAX')\n"
    "   • Document codes (e.g., 'PN/IT/2025-01', 'SET_25_26')\n"
    "   • Year references (e.g., 'YEAR OF ASSESSMENT – 2022/2023')\n"
    "   • Text that looks like a title bar or document identifier\n"
    "   \n"
    "   EXAMPLE OF CORRECT EXTRACTION:\n"
    "   From: '12.2 For the second six months period (from 01.10.2022 to 31.032023) of the year...'\n"
    "   Extract: '12.2 For the second six months period'\n"
    "   \n"
    "   From: '13. Payment of tax'\n"
    "   Extract: '13. Payment of tax' or just '13'\n"
    "   \n"
    "   EXAMPLE OF WRONG EXTRACTION:\n"
    "   DON'T extract: 'GUIDE TO CORPORATE RETURN OF INCOME TAX- YEAR OF ASSESSMENT – 2022/2023'\n"
    "   This is a page header/document title, NOT a section!\n"
    "   \n"
    "   DON'T extract: '(b) Business of export of goods'\n"
    "   This is a LIST ITEM under a section, NOT a section heading!\n"
    "   \n"
    "   DON'T extract: '(ii) 24% Tax Rate'\n"
    "   This is a LIST ITEM, NOT a section heading!\n"
    "   \n"
    "   Instead, find the PARENT SECTION that contains these list items (e.g., '12. Tax Rates' or '5.2 Export Income')\n"
    "   \n"
    "   If you cannot find a clear section heading in the actual content, leave the section field empty.\n"
    "5. NO DUPLICATES - each unique source (document + page + section) should appear only once\n\n"
    "Return your response as:\n"
    "- content: Your answer in markdown format with inline citations [1], [2], etc.\n"
    "- sources: List of Source objects with document_name, source_url, page_number, section\n\n"
    "Add this disclaimer at the end of your content:\n"
    "---\n"
    "*Disclaimer: This response is based solely on IRD-published documents and is not professional tax advice. "
    "Please consult a qualified tax professional for personalized guidance.*"
)

class GradeDocuments(BaseModel):  
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )

class Source(BaseModel):
    """A single source citation."""
    document_name: str = Field(description="Clean document name without path or extension")
    source_url: str = Field(description="The actual URL from metadata")
    page_number: int = Field(description="Page number from metadata")
    section: str = Field(description="MAIN SECTION HEADING ONLY (e.g., '12.3 Dividend', '13. Payment of tax'). NEVER use list items like (a), (b), (i), (ii). Leave empty if no clear section heading.")

class StructuredAnswer(BaseModel):
    """Structured answer with content and sources."""
    content: str = Field(description="The main answer content in markdown format")
    sources: List[Source] = Field(description="List of unique sources used, no duplicates")



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
    """Generate an answer with structured output."""
    messages = state["messages"]
    question = next((m.content for m in reversed(messages) if hasattr(m, 'type') and m.type == 'human'), messages[0].content)
    context = messages[-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    
    structured_response = model.with_structured_output(StructuredAnswer).invoke([{"role": "user", "content": prompt}])
    
    formatted_content = structured_response.content + "\n\n**Sources:**\n\n"
    
    seen_sources = set()
    formatted_sources = []
    
    for idx, source in enumerate(structured_response.sources, 1):
        source_key = (source.document_name, source.page_number, source.section)
        
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            
            if source.section:
                formatted_sources.append(
                    f"[{idx}]- [{source.document_name}]({source.source_url}) - Page {source.page_number} - {source.section}\n"
                )
            else:
                formatted_sources.append(
                    f"[{idx}]- [{source.document_name}]({source.source_url}) - Page {source.page_number}\n"
                )
    
    formatted_content += "\n".join(formatted_sources)
    
    return {"messages": [AIMessage(content=formatted_content)]}


