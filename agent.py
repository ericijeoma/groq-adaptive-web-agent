import nodriver
from typing import Annotated
from typing_extensions import TypedDict
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from scraping_tools import search_web, scrape_page,crawl_website, map_website, scrape_amazon_product
import datetime

class State(TypedDict):
    messages: Annotated[list, add_messages]

tools = [search_web, scrape_page, crawl_website, map_website, scrape_amazon_product]

llm = ChatOllama(
    model="llama3-groq-tool-use:8b",
    base_url="http://localhost:11434",
    temperature=0.1,
    num_ctx=32768
)

llm_with_tools = llm.bind_tools(tools)

async def call_model(state: State):
    tool_failed = state.get("tool_failed", False)
    system = SystemMessage(content=
    # ── FALLBACK: tool gave nothing useful ──────────────────────────────
    f"""You are a helpful assistant. Today is {datetime.date.today()}.
YYour tools returned no useful results. For this user query, answer directly from your own knowledge. If you still need external data, ask a clarification or request permission to run another search."""

    if tool_failed else

    # ── NORMAL: use tools ───────────────────────────────────────────────
    f"""
    1) You are a web data extraction agent. Today is {datetime.date.today()}.
    2) Prefer using tools when the user asks for web data, current events, or to scrape a page. For simple factual questions that do not need up-to-date web results, answer from your own knowledge. When you decide to call a tool, call the most appropriate one (search_web for queries, scrape_page for a URL, scrape_amazon_product for Amazon).
    3) You are a helpful web research assistant.
    4) You have access to tools to search the web and scrape data. 
    5) If a user asks about current events (like the President), you MUST use the search_web tool first.
    6) When your tool does not return any result then answer from memory.
    
    Tools available:
    - search_web(query): use when user asks for current events or searches.
    - scrape_page(url): use when user gives a URL to extract content.
    - scrape_amazon_product(asin or url): use for Amazon product details.
    When you call a tool, invoke it with the relevant query/url and wait for the tool result before producing a final answer.
    """
)

#     system = SystemMessage(content=f"""
# 1) You are a web data extraction agent. Today is {datetime.date.today()}.
# 2) You MUST always call a tool first before responding. Always use your tools first.
# 3) You are a helpful web research assistant.
# 4) You have access to tools to search the web and scrape data. 
# 5) If a user asks about current events (like the President), you MUST use the search_web tool first.
# 6) When your tool does not return any result then answer from memory.""")
    messages = [system] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)
def _tool_result_is_empty(msg) -> bool:
    """Return True if a ToolMessage has no meaningful content."""
    if not isinstance(msg, ToolMessage):
        return False
    content = msg.content
    if not content:
        return True
    # Treat common "no result" strings as empty
    empty_signals = ["no results", "none", "error", "[]", "{}", "null", "not found"]
    return any(sig in content.lower() for sig in empty_signals)


def should_continue(state: State):
    last_message = state["messages"][-1]

    # 1) If the model just returned a ToolMessage that is empty -> go back to model with tool_failed
    if isinstance(last_message, ToolMessage) and _tool_result_is_empty(last_message):
        state["tool_failed"] = True
        return "model"

    # 2) Otherwise, if the model requested a tool call, run tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END

graph = StateGraph(State)
graph.add_node("model", call_model)
graph.add_node("tools", tool_node)
graph.set_entry_point("model")
graph.add_conditional_edges("model", should_continue)
graph.add_edge("tools", "model")
agent = graph.compile(checkpointer=MemorySaver())

async def run(query: str):
    print("Agent ready.\n")
    config = {"configurable": {"thread_id": "thread-1"}}
    async for step in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        config=config,
        stream_mode="values"
    ):
        step["messages"][-1].pretty_print()

if __name__ == "__main__":
    nodriver.loop().run_until_complete(run("search online who is the president of USA?"))

#Tip: If you want the model to search online for a particular information prefix your prompt with "Search online"
#Example if you want to know the recent news in AI, the use this: Search online for the recent AI news