from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.chat_models import init_chat_model
from langgraph.graph import START, StateGraph

import os
from dotenv import load_dotenv

from typing_extensions import TypedDict
from typing_extensions import Annotated
import getpass





class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

load_dotenv()

#Conexión a la bdd
db = SQLDatabase.from_uri(f"postgresql://{os.getenv('SUPA_USER')}:{os.getenv('SUPA_PASSWORD')}@{os.getenv('SUPA_HOST')}:{os.getenv('SUPA_PORT')}/postgres")
# print(db.dialect)
# print(db.get_usable_table_names())

#Conexion OpenAI
if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

llm = init_chat_model("gpt-4o-mini", model_provider="openai")

#Pulling a prompt from the prompt hub to instruct the model
from langchain import hub

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

#Instructing the LLM to give out sql queries

class QueryOutput(TypedDict):
   """Generated SQL Query."""
   query: Annotated[str, ...,"Syntactically valid SQL query."]

def write_query(state:State):
   """Generate SQL query to fetch information"""
   prompt = query_prompt_template.invoke({
      "table_info":db.get_table_info(),
      "input": state["question"],
      "dialect": db.dialect,
      "top_k": 2,
    }
   )
   structured_llm = llm.with_structured_output(QueryOutput)
   result = structured_llm.invoke(prompt)
   return {"query": result["query"]}

#Telling the RAG to execute the function

def execute_query(state:State):
   """Execute SQL query"""
   execute_query_tool = QuerySQLDatabaseTool(db=db)
   return {"result": execute_query_tool.invoke(state["query"])}

#Trying the function

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


#Creating a process
graph_builder = StateGraph(State).add_sequence(
    [write_query, execute_query, generate_answer]
)
graph_builder.add_edge(START, "write_query")
graph = graph_builder.compile()

for step in graph.stream(
    {"question": "Qué me puedes decir de las sensaciones de conducción del Jaecoo 7?"}, stream_mode="updates"
):
    print(step)
