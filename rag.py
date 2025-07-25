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

# Cite snippets
class Citation(BaseModel):
    source_id: int = Field(
        ...,
        description="The integer ID of a SPECIFIC source which justifies the answer.",
    )
    quote: str = Field(
        ...,
        description="The VERBATIM quote from the specified source that justifies the answer.",
    )

def format_docs_with_id(docs: List[Document]) -> str:
    formatted = [
        f"Source ID: {i}\nProject name: {doc.metadata['NAME']}\nInterview Snippet: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]
    return "\n\n" + "\n\n".join(formatted)

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

system_prompt = (
    "You're a helpful AI assistant."
    "Given a user question and some project interview, answer the user question."
    "If none of the documents answer the question, just say you don't know."
    "\n\nHere are the project interviews: "
    "{context}"
)

class Rag:
    def __init__(self, model="openai:gpt-4o-mini"):
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}"),
            ]
        )

        provider, model = model.split(":")
        if provider == "openai":
            api_key = os.getenv["OPENAI_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        elif provider == "mistralai":
            api_key = os.getenv["MISTRAL_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        elif provider == "vllm":
            self.llm = VLLMOpenAI(
                openai_api_key=os.getenv['HF_TOKEN'],
                openai_api_base="https://socioscope2--vllm-serve.modal.run/v1",
                model_name="neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w4a16",
                #model_kwargs={"stop": ["."]},
            )
        elif provider == "groq":
            api_key = os.getenv["GROQ_API_KEY"]
            self.llm = init_chat_model(model=model, model_provider=provider, api_key=api_key)
        else:
            self.llm = None

        print(f"Loaded LLM model {provider}:{model}")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv["OPENAI_API_KEY"])
        self.vector_store = InMemoryVectorStore(embedding=self.embeddings)
        self.retriever = None
    
    def load_documents(self, docs):
        # Build vector store
        documents = [Document(page_content=source['page_content'], metadata=source['metadata']) for source in sources]
        self.vector_store.add_documents(documents=documents)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": len(documents)})
        
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
        print(f"Vector database ready: {len(self.vector_store.store)} documents.")

def prompt(docs, question, model="openai:gpt-4o-mini"):
    # Load model
    rag = Rag(model=model)

    # Load docs
    rag.load_documents(docs)

    # Ask question
    rag.prompt.pretty_print()
    return rag.graph.invoke({"question": question})