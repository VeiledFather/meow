import os

from dotenv import load_dotenv
from google import genai


load_dotenv(
    "/home/godhunter/CampusHub/.env"
)


class EVAI:

    def __init__(self):

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "EVAI_MODEL",
            "gemini-3.5-flash-lite"
        )


    def ask(
        self,
        message,
        context=""
    ):

        system_prompt = """
You are EvAi, the intelligent campus
assistant inside CampusHub.

Your name is EvAi.

You help students, organizers, volunteers,
and administrators use CampusHub.

You must:

- Be helpful, concise, friendly, and natural.
- Never invent CampusHub data.
- Treat supplied CampusHub context as factual.
- Use the detected user intent when answering.
- Answer the user's actual question first.
- Do not dump the entire supplied context.
- Clearly say when supplied context does not
  contain the requested information.
- Never reveal private information belonging
  to another user.
- Respect the current user's role.
- Help users understand and navigate CampusHub.
- Help with events, registrations, venues,
  schedules, tickets, certificates,
  notifications, reviews, assignments,
  and CampusHub features.
- Never claim an action was completed unless
  CampusHub actually completed it.
- Do not expose internal database details.
- Your name is EvAi, not Gemini.
- Always refer to yourself as EvAi.
"""

        if context:

            system_prompt += f"""

CURRENT CAMPUSHUB CONTEXT:

{context}
"""


        prompt = f"""
{system_prompt}

USER MESSAGE:

{message}
"""


        response = self.client.models.generate_content(

            model=self.model,

            contents=prompt

        )


        return response.text
