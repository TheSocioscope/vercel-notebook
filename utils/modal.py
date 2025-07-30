import modal
from pydantic import BaseModel

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "langchain",
    "langchain-openai",
    "langchain-mistralai",
    "langchain-community",
    "langchain-groq",
    "langgraph",
    "openai",
    "fastapi[standard]",
    "pydantic==2.10.6"
    )

with image.imports():
    from langchain.chat_models import init_chat_model
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.llms import VLLMOpenAI
    import os
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.documents import Document
    from langgraph.graph import START, StateGraph
    from typing_extensions import List, TypedDict
    from pydantic import BaseModel, Field

app = modal.App(name="socioscope-rag",
                image=image,
                secrets=[modal.Secret.from_name("openai-api-key"),
                         modal.Secret.from_name("mistral-api-key"),
                         modal.Secret.from_name("huggingface-secret"),
                         modal.Secret.from_name("groq-api-key")])

# Main RAG class
class Rag:
    def __init__(self, model, docs):
        # Initialize vector store
        system_prompt = (
            "You're a helpful AI assistant."
            "Given a user question and some project interview, answer the user question."
            "If none of the documents answer the question, just say you don't know."
            "\n\nHere are the project interviews: "
            "{context}"
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}"),
            ]
        )
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.environ["OPENAI_API_KEY"])
        self.vector_store = InMemoryVectorStore(embedding=self.embeddings)

        # Build vector store
        documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in docs]
        self.vector_store.add_documents(documents=documents)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": len(documents)})
        print(f"> Vector database ready with {len(self.vector_store.store)} documents.")

        # Load LLM model
        provider, model = model.split(":")
        if provider == "openai":
            api_key = os.environ["OPENAI_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        elif provider == "mistralai":
            api_key = os.environ["MISTRAL_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        elif provider == "vllm":
            self.llm = VLLMOpenAI(
                openai_api_key=os.environ['HF_TOKEN'],
                openai_api_base="https://socioscope2--vllm-serve.modal.run/v1",
                model_name="neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w4a16",
                #model_kwargs={"stop": ["."]},
            )
        elif provider == "groq":
            api_key = os.environ["GROQ_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        else:
            self.llm = None
            raise ValueError(f"Invalid LLM provider: {provider}")
        print(f"> LLM {provider}:{model} loaded.")

        # Load graph
        class Citation(BaseModel):
            source_id: int = Field(
                ...,
                description="The integer ID of a SPECIFIC source which justifies the answer.",
            )
            quote: str = Field(
                ...,
                description="The VERBATIM quote from the specified source that justifies the answer.",
            )

        class QuotedAnswer(BaseModel):
            """Answer the user question based only on the given sources, and cite the sources used."""

            answer: str = Field(
                ...,
                description="The answer to the user question, which is based only on the given sources.",
            )
            citations: List[Citation] = Field(
                ..., description="Citations from the given sources that justify the answer."
            )

        class State(TypedDict):
            question: str
            context: List[Document]
            answer: QuotedAnswer

        def format_docs_with_id(docs: List[Document]) -> str:
            formatted = [
                f"Source ID: {i}\nProject name: {doc.metadata['NAME']}\nInterview Snippet: {doc.page_content}"
                for i, doc in enumerate(docs)
            ]
            return "\n\n" + "\n\n".join(formatted)

        # Define application steps
        def retrieve(state: State):
            retrieved_docs = self.retriever.invoke(state["question"])
            return {"context": retrieved_docs}

        def generate(state: State):
            formatted_docs = format_docs_with_id(state["context"])
            messages = self.prompt.invoke({"question": state["question"], "context": formatted_docs})
            structured_llm = self.llm.with_structured_output(QuotedAnswer)
            response = structured_llm.invoke(messages)
            return {"answer": response}

        # Compile application and test
        graph_builder = StateGraph(State).add_sequence([retrieve, generate])
        graph_builder.add_edge(START, "retrieve")
        self.graph = graph_builder.compile()
        print("> LangGraph ready.")

class Query(BaseModel):
    docs: list
    message: str = "What is Socioscope?"
    model: str = "openai:gpt-4o-mini"

@app.function(gpu="any", 
              max_containers=1,)
@modal.fastapi_endpoint(method="POST", docs=True)
def query(query:Query):
    # Log query
    print(f"Receiving query:'{query.message}' with model:'{query.model}' on {len(query.docs)} documents.")

    # Load class
    rag = Rag(model=query.model, docs=query.docs)

    # Ask question
    print(f"> Sending query...")
    response = rag.graph.invoke({"question": query.message})
    return response