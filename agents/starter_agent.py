"""A tiny starter agent loop you can run before connecting real AI APIs."""

from __future__ import annotations


SYSTEM_PROMPT = "You are a practical assistant that gives concise software advice."


def respond(user_message: str) -> str:
    """Placeholder agent response function.

    Replace this with an OpenAI API call once your `.env` contains an API key.
    """
    cleaned = user_message.strip()
    if not cleaned:
        return "Ask me something and I will respond."

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Received: {cleaned}\n"
        "Next step: wire this function to an LLM call when you are ready."
    )


def main() -> None:
    print("Starter agent. Type 'exit' to quit.")

    while True:
        user_message = input("> ")
        if user_message.strip().lower() in {"exit", "quit"}:
            break

        print(respond(user_message))


if __name__ == "__main__":
    main()
