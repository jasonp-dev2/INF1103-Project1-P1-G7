import asyncio
import os

from copilot import CopilotClient

DEFAULT_MODEL = "gpt-5.4"

def get_model_name() -> str:
    return os.environ.get("AI_MODEL", DEFAULT_MODEL)


async def test_ai_connection() -> str:
    async with CopilotClient() as client:
        async with await client.create_session(
            model=get_model_name()
        ) as session:
            response = await session.send_and_wait(
                "Reply with exactly: AI connection successful"
            )

            if response is None:
                return ""

            return response.data.content

def main() -> None:
    result = asyncio.run(test_ai_connection())
    print(result)

if __name__ == "__main__":
    main()
