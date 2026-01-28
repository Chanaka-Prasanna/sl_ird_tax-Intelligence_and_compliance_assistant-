from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from nodes import (
    State, 
    generate_query_or_respond, 
    grade_documents, 
    rewrite_question, 
    generate_answer,
    summarize_conversation,
    should_summarize
)
from tools import retriever_tool

workflow = StateGraph(State)

workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)
workflow.add_node(summarize_conversation)

workflow.add_edge(START, "generate_query_or_respond")


workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)

workflow.add_edge("rewrite_question", "generate_query_or_respond")

# After generate_answer, check if we need to summarize the conversation
workflow.add_conditional_edges(
    "generate_answer",
    should_summarize,
    {
        "summarize_conversation": "summarize_conversation",
        "__end__": END,
    },
)

# After summarization, end the workflow
workflow.add_edge("summarize_conversation", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)


