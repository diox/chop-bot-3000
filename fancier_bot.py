import simplematrixbotlib as botlib


class ApiWithHTML(botlib.Api):
    async def send_html_message(self, room_id, message, msgtype='m.text'):
        await self._send_room(
            room_id=room_id,
            content={
                'msgtype': msgtype,
                'body': message,
                'format': 'org.matrix.custom.html',
                'formatted_body': message,
            },
        )


class BotWithHTML(botlib.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = ApiWithHTML(self.creds, self.config)
