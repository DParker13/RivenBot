import openai


class OpenAICommands:
    chat_history = []

    def __init__(self, client, logger, api_key, chat_file_path):
        self.client = client
        self.logger = logger
        openai.api_key = api_key
        self.chat_file_path = chat_file_path
        self.setup_chat_file(chat_file_path)

    def setup_chat_file(self, chat_file_path):
        with open(chat_file_path, "a+") as file:
            self.chat_history = file.readlines()
        file.close()


    def addOpenAICommands(self):
        @self.client.command(name='chat',
                             help='Chat with OpenAI ChatGPT 3.5 Turbo bot model')
        async def chat(ctx):
            content = ctx.message.content[5:].strip()

            self.logger.print("Chat -", content)
            self.chat_history.append(str({"role": "user", "content": content}))
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.chat_history)
            resp = completion.choices[0].message.content.strip("\n").strip()
            self.chat_history.append(str({"role": "assistant", "content": resp}))

            # Writes user content and chatGPT response to file
            with open(self.chat_file_path, "w") as file:
                file.writelines(self.chat_history)

            self.logger.print("ChatGPT Response -", resp)
            await ctx.send(resp)
