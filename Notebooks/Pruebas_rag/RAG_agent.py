from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.chat_models import init_chat_model
from langgraph.graph import START, StateGraph
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain import hub
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.agents.agent_toolkits import create_retriever_tool


import os
from dotenv import load_dotenv
import ast
import re

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

#Conexion OpenAI
if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

llm = init_chat_model("gpt-4o-mini", model_provider="openai")

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

tools = toolkit.get_tools()

#Systm prompt for the agent: Instructions on how to behave


prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")

##Parameter fill in the message
system_message = prompt_template.format(dialect=db.dialect, top_k=5)

#Stablishing the agent from prebuilt in langraph

agent_executor = create_react_agent(llm, tools, prompt=system_message)

question = "¿Cual es el coche mas caro?"

for step in agent_executor.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

#Model is not very precise, lets add embeddings and vector search
##Before adding embeddings we will cite the columns in which we want to aproximate the queries

def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))


marca_caracteristicas = query_as_list(db, "SELECT marca FROM caracteristicas")
modelo_caracteristicas = query_as_list(db, "SELECT modelo FROM caracteristicas")


embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="documentos",
    connection=f"postgresql+psycopg2://{os.getenv('SUPA_USER')}:{os.getenv('SUPA_PASSWORD')}@{os.getenv('SUPA_HOST')}:{os.getenv('SUPA_PORT')}/postgres"
)


_ = vector_store.add_texts(marca_caracteristicas + modelo_caracteristicas)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})
description = (
    "Use to look up values to filter on. Input is an approximate spelling "
    "of the proper noun, output is valid proper nouns. Use the noun most "
    "similar to the search."
)
retriever_tool = create_retriever_tool(
    retriever,
    name="search_proper_nouns",
    description=description,
)

print(retriever_tool.invoke("Siat Fibiza"))

# Add to system message
suffix = (
    "If you need to filter on a proper noun like a Name, you must ALWAYS first look up "
    "the filter value using the 'search_proper_nouns' tool! Do not try to "
    "guess at the proper name - use this function to find similar ones."
)

system = f"{system_message}\n\n{suffix}"

tools.append(retriever_tool)

agent = create_react_agent(llm, tools, prompt=system)
