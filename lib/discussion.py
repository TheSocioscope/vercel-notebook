import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class Message:
    order: int
    session_id: str  # User session isolation - prevents cross-user result mixing
    model: str
    question: str
    contents: list
    responses: list
    final_response: str


# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You're a helpful AI academic research assistant.
Given a user question and some provided documents, answer the user question.
If none of the documents answer the question, just say you don't know. Format your final answer in markdown."""

REDUCE_PROMPT = """The following is a set of intermediate responses:
{responses}

Take these and distill it into a final, consolidated response to the main user question:
{question}"""


def _map_document(question: str, content: str, model: str) -> str:
    """Process a single document and generate a response."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Document:\n{content}\n\nQuestion: {question}",
            },
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _reduce_responses(question: str, responses: list[str], model: str) -> str:
    """Consolidate multiple responses into a final answer."""
    responses_text = "\n\n---\n\n".join(
        [f"Response {i+1}:\n{r}" for i, r in enumerate(responses)]
    )
    prompt = REDUCE_PROMPT.format(responses=responses_text, question=question)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that consolidates information from multiple sources into a coherent final answer.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def send_rag(docs, message, model="qwen/qwen3-32b"):
    """
    Process documents using map-reduce pattern with Groq API.

    Args:
        docs: List of documents with 'page_content' key
        message: The user's question
        model: The Groq model to use

    Returns:
        dict with question, contents, responses, and final_response
    """
    # Map phase: process each document
    responses = []
    contents = [doc["page_content"] for doc in docs]

    for content in contents:
        response = _map_document(message, content, model)
        responses.append(response)

    # Reduce phase: consolidate responses
    if len(responses) == 1:
        final_response = responses[0]
    else:
        final_response = _reduce_responses(message, responses, model)

    return {
        "question": message,
        "contents": contents,
        "responses": responses,
        "final_response": final_response,
    }
