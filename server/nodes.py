from dotenv import load_dotenv
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Literal
from langchain.messages import HumanMessage
from langchain.chat_models import init_chat_model
from tools import retriever_tool

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
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n\n"
    "Question: {question} \n\n"
    "Context: {context}\n\n"
    "IMPORTANT: At the end of your answer, provide citations in markdown format.\n"
    "For each citation, create a clickable link using this exact format:\n"
    "• Source: [Document Name](actual_url_here) – Page X\n\n"
    "Extract the 'source_url' value from the metadata and use it as the actual URL in the markdown link.\n"
    "Example: If source is 'Tax Guide' and source_url is 'https://example.com/tax.pdf', write:\n"
    "• Source: [Tax Guide](https://example.com/tax.pdf) – Page 5\n\n"
    "DO NOT write (source_url) literally - use the ACTUAL URL value from the metadata.\n"
    "Format your entire answer in markdown with proper clickable links."
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
    question = state["messages"][0].content
    context = state["messages"][-1].content

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
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}

def generate_answer(state: MessagesState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


