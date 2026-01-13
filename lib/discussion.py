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


def map_document(question: str, content: str, model: str = "qwen/qwen3-32b") -> str:
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


def reduce_responses(question: str, responses: list[str], model: str = "qwen/qwen3-32b") -> str:
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
    Note: This is the legacy synchronous version. For better serverless performance,
    use map_document + reduce_responses with client-side orchestration.
    """
    responses = []
    contents = [doc["page_content"] for doc in docs]

    for content in contents:
        response = map_document(message, content, model)
        responses.append(response)

    if len(responses) == 1:
        final_response = responses[0]
    else:
        final_response = reduce_responses(message, responses, model)

    return {
        "question": message,
        "contents": contents,
        "responses": responses,
        "final_response": final_response,
    }
