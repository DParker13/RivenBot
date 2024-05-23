import openai
import logging

class OpenAICommands:
    chat_history = []

    def __init__(self, client, logger, api_key):
        self.client = client
        self.logger = logger
        openai.api_key = api_key

    def addOpenAICommands(self):
        @self.client.command(name='chat',
                             help='Chat with OpenAI ChatGPT 3.5 Turbo bot model')
        async def chat(ctx):
            content = ctx.message.content[5:].strip()

            if len(self.chat_history) >= 25:
                del self.chat_history[0]

            self.logger.info("Chat -" + str(content))
            self.chat_history.append({"role": "user", "content": content})
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.chat_history)
            resp = completion.choices[0].message.content.strip("\n").strip()
            self.chat_history.append({"role": "assistant", "content": resp})

            self.logger.info("ChatGPT Response -" + str(resp))
            await ctx.send(resp)

        @self.client.command(name='image',
                             help='Create an image from a text prompt using DALL-E model')
        async def image(ctx):
            prompt = ctx.message.content[5:].strip()
            image_resp = openai.Image.create(prompt=prompt, n=1, size="1024x1024", response_format="url")

            await ctx.send(image_resp["data"][0]["url"])
