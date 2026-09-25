from langchain_core.prompts import ChatPromptTemplate


def main() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a concise assistant."),
            ("human", "Explain {topic} in one sentence."),
        ]
    )
    messages = prompt.invoke({"topic": "LangChain"})

    print("Python project is ready.")
    for message in messages.messages:
        print(f"{message.type}: {message.content}")


if __name__ == "__main__":
    main()

