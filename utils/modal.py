import modal
from pydantic import BaseModel

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "langchain",
    "langchain-openai",
    "langchain-community",
    "langgraph",
    "openai",
    "fastapi[standard]",
    "pydantic==2.10.6"
    )

with image.imports():
    from langchain.chat_models import init_chat_model
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_openai import OpenAIEmbeddings
    import os
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    import operator
    from typing import Annotated, List, Literal, TypedDict
    from langchain.chains.combine_documents.reduce import (
        acollapse_docs,
        split_list_of_docs,
    )
    from langchain_core.documents import Document
    from langgraph.constants import Send
    from langgraph.graph import END, START, StateGraph
    from pydantic import BaseModel, Field
    import json

app = modal.App(name="socioscope-rag",
                image=image,
                secrets=[modal.Secret.from_name("openai-api-key"),
                         modal.Secret.from_name("mistral-api-key"),
                         modal.Secret.from_name("huggingface-secret"),
                         modal.Secret.from_name("groq-api-key")])

# Main RAG class
class Rag:
    def __init__(self, model):
        """
        Initialize the RAG class.
        :param model: The name of the LLM model to use (unavailable)
        """
        # Inialize map-reduce chain
        system_prompt = (
            "You're a helpful AI academic research assistant."
            "Given a user question and some provided documents, answer the user question."
            "If none of the documents answer the question, just say you don't know."
            "\n\nHere are the document:\\n\\n"
            "{context}"
        )

        map_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}"),
            ]
        )
        reduce_template = """
        The following is a set of intermediate response:
        {context}
        Take these and distill it into a final, consolidated response
        of the main user question :\\n\\n
        {question}
        """
        reduce_prompt = ChatPromptTemplate([("human", reduce_template)])

        llm = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=os.environ["OPENAI_API_KEY"])
        map_chain = map_prompt | llm | StrOutputParser()
        reduce_chain = reduce_prompt | llm | StrOutputParser()

        token_max = 12800

        def length_function(documents: List[Document]) -> int:
            """Get number of tokens for input contents."""
            return sum(llm.get_num_tokens(doc.page_content) for doc in documents)

        # Load graph
        # This will be the overall state of the main graph.
        # It will contain the input document contents, corresponding
        # responses, and a final summary.
        class OverallState(TypedDict):
            # Notice here we use the operator.add
            # This is because we want combine all the responses we generate
            # from individual nodes back into one list - this is essentially
            # the "reduce" part
            question: str
            contents: List[str]
            responses: Annotated[list, operator.add]
            collapsed_responses: List[Document]
            final_response: str


        # This will be the state of the node that we will "map" all
        # documents to in order to generate summaries
        class ResponseState(TypedDict):
            question: str
            content: str

        # Here we generate a summary, given a document
        async def generate_response(state: ResponseState):
            response = await map_chain.ainvoke({"question": state["question"], "context": state["content"]})
            return {"responses": [response]}

        # Here we define the logic to map out over the documents
        # We will use this an edge in the graph
        def map_responses(state: OverallState):
            # We will return a list of `Send` objects
            # Each `Send` object consists of the name of a node in the graph
            # as well as the state to send to that node
            return [
                Send("generate_response", {"question": state["question"], "content": content}) for content in state["contents"]
            ]

        def collect_responses(state: OverallState):
            return {
                "collapsed_responses": [Document(response) for response in state["responses"]]
            }


        # Add node to collapse responses
        async def collapse_responses(state: OverallState):
            doc_lists = split_list_of_docs(
                state["collapsed_responses"], length_function, token_max
            )
            results = []
            for doc_list in doc_lists:
                results.append(await acollapse_docs(doc_list, reduce_chain.ainvoke))

            return {"collapsed_responses": results}


        # This represents a conditional edge in the graph that determines
        # if we should collapse the responses or not
        def should_collapse(
            state: OverallState,
        ) -> Literal["collapse_responses", "generate_final_response"]:
            num_tokens = length_function(state["collapsed_responses"])
            if num_tokens > token_max:
                return "collapse_responses"
            else:
                return "generate_final_response"


        # Here we will generate the final summary
        async def generate_final_response(state: OverallState):
            response = await reduce_chain.ainvoke({"question":state["question"], "context": state["collapsed_responses"]})
            return {"final_response": response}


        # Construct the graph
        # Nodes:
        graph = StateGraph(OverallState)
        graph.add_node("generate_response", generate_response)  # same as before
        graph.add_node("collect_responses", collect_responses)
        graph.add_node("collapse_responses", collapse_responses)
        graph.add_node("generate_final_response", generate_final_response)

        # Edges:
        graph.add_conditional_edges(START, map_responses, ["generate_response"])
        graph.add_edge("generate_response", "collect_responses")
        graph.add_conditional_edges("collect_responses", should_collapse)
        graph.add_conditional_edges("collapse_responses", should_collapse)
        graph.add_edge("generate_final_response", END)

        self.app = graph.compile()
        print("> LangGraph ready.")

class Query(BaseModel):
    docs: list[dict]
    message: str = "What is Socioscope?"
    model: str = "openai:gpt-4o-mini"

@app.function(max_containers=10)
@modal.fastapi_endpoint(method="POST", docs=True, requires_proxy_auth=True)
async def query(query:Query):
    """
    Query the RAG system.
    :param query: The query to send to the RAG system.
    :return: The response from the RAG system.
    """
    # Log query
    print(f"> Receiving query:'{query.message}' with model:'{query.model}' on {len(query.docs)} documents.")

    # Load class
    rag = Rag(model=query.model)

    # Ask question
    print(f"> Sending query...")
    response = await rag.app.ainvoke({"question": query.message, "contents": [doc['page_content'] for doc in query.docs]})
    print(f"> Sending response...: {response}")
    return response