import streamlit as st
import os
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain import hub
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain.agents.agent_toolkits import create_retriever_tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import getpass
import ast
import re

load_dotenv()

def mostrar_historial():
    st.write("### 🗂️ Historial de Conversación")
    if  st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            role = "👤 Usuario:" if isinstance(msg, HumanMessage) else "🤖 RAG:"
            st.write(f"**{role}** {msg.content}")
    else:
        st.write("No hay historial de conversación.")

def create_agent(db,openai_api_key, contexto):

    #Conexion OpenAI
    if not openai_api_key:
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

    llm = init_chat_model("gpt-4o-mini", model_provider="openai")

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    tools = toolkit.get_tools()

    #Systm prompt for the agent: Instructions on how to behave


    prompt_template = """You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        DO NOT answer with null values.
        DO NOT hallucinate. Keep your responses tied to the content you know.
        YOU ARE NOT ALLOWED to answer questions related to content not in the database.

        To start you should ALWAYS look at the tables in the database to see what you can query.
        Do NOT skip this step.
        Then you should query the schema of the most relevant tables.
        
        If asked about a parameter not explicitly present in the "caracteristicas" or "modelos" columns you should ALWAYS look for similar parameters inside "reviews".
        """

    ##Parameter fill in the message
    system_message = prompt_template.format(dialect=db.dialect, top_k=5)

    #Stablishing the agent from prebuilt in langraph

    # agent_executor = create_react_agent(llm, tools, prompt=system_message)

    # question = "¿Cual es el coche mas caro?"

    # for step in agent_executor.stream(
    #     {"messages": [{"role": "user", "content": question}]},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()

    #Model is not very precise, lets add embeddings and vector search for proper car nouns
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
        connection=f"postgresql://{os.getenv('SUPA_USER')}:{os.getenv('SUPA_PASSWORD')}@{os.getenv('SUPA_HOST')}:{os.getenv('SUPA_PORT')}/postgres"
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

    # Add to system message
    suffix = (
        "If you need to filter on a proper noun like a Name, you must ALWAYS first look up "
        "the filter value using the 'search_proper_nouns' tool! Do not try to "
        "guess at the proper name - use this function to find similar ones."
    )

    system = f"{system_message}\n\n{suffix}\n\n {contexto}"

    # aware_retriever = vector_store.as_retriever()
    # prompt = "Use this tool to retrieve relevant context from previous conversations based on the input query."

    # retriever_aware = create_retriever_tool(
    # aware_retriever,
    # name="History_aware",
    # description=prompt,
    # )

    # tools.append(retriever_aware)

    tools.append(retriever_tool)

    agent = create_react_agent(llm, tools, prompt=system)

    return agent

def main():

    st.title("🚗 Recomendador de Coches con RAG")
    st.sidebar.header("🔧 Configuración")
    with st.sidebar:
        default_openai_api_key = os.getenv("OPENAI_API_KEY") if os.getenv("OPENAI_API_KEY") is not None else ""
        with st.popover("🔐 OpenAI"):
            openai_api_key = st.text_input(
            "Introduce your OpenAI API Key (https://platform.openai.com/)", 
            value=default_openai_api_key, 
            type="password",
            key="openai_api_key",
    )
        


    missing_openai = openai_api_key == "" or openai_api_key is None or "sk-" not in openai_api_key

    if missing_openai:
        st.write("#")
        st.warning("⬅️ Please introduce an API Key to continue...")
    

    
    with st.sidebar:
        default_user = os.getenv('SUPA_USER') if os.getenv('SUPA_USER') is not None else ""
        with st.popover("🔐 USER"):
            supabase_user = st.text_input(
            "Introduce your Supabase user", 
            value=default_user, 
            key="supabase_user",
    )
            
        default_pw = os.getenv('SUPA_PASSWORD') if os.getenv('SUPA_PASSWORD') is not None else ""
        with st.popover("🔐 PASSWORD"):
            supabase_pw = st.text_input(
            "Introduce your Supabase password",
            type = "password", 
            value=default_pw, 
            key="supabase_password",
    )
        default_host = os.getenv('SUPA_HOST') if os.getenv('SUPA_HOST') is not None else ""
        with st.popover("HOST"):
            supabase_host = st.text_input(
            "Introduce your Supabase host", 
            value=default_host, 
            key="supabase_host",
    )
            
        default_port = os.getenv('SUPA_PORT') if os.getenv('SUPA_PORT') is not None else ""
        with st.popover("PORT"):
            supabase_port = st.text_input(
            "Introduce your Supabase port", 
            value=default_port, 
            key="supabase_port",
    )
                
    with st.sidebar:
        st.divider()
        cols0 = st.columns(2)
        with cols0[0]:
            st.button("Clear Chat", on_click = lambda: st.session_state.messages.clear(), type = "primary")
        with cols0[-1]:
            st.button("🗂️ Ver Historial de Conversación",on_click = mostrar_historial)




    db = SQLDatabase.from_uri(f"postgresql://{supabase_user}:{supabase_pw}@{supabase_host}:{supabase_port}/postgres")



    # Inicializar el agente en session_state si no existe
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    chat_history = st.session_state.chat_history
    
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent(db,openai_api_key,chat_history)  
    


    user_input = st.text_input("Escribe tu consulta sobre coches:")

    if user_input:
        with st.spinner("Buscando información... 🔎"):
            response = st.session_state.agent.invoke({"messages": [{"role": "user", "content": user_input}]})
            
            # Obtener la respuesta del modelo
            respuesta_modelo = response["messages"][-1].content  
            
            # Guardar en historial´
            st.session_state.chat_history.append(HumanMessage(content=user_input))
            st.session_state.chat_history.append(AIMessage(content=respuesta_modelo))

            # Mostrar respuesta
            st.write("### 📌 Respuesta:")
            st.write(respuesta_modelo)


if __name__ == "__main__":
    main()

