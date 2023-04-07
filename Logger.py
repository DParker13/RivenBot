import datetime
import os.path
import logging.handlers


class Logger:
    file = None
    _print = print
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def __init__(self, base_path, enable_logs):
        self.base_path = base_path
        self.enable_logs = enable_logs

    def setup_logs(self):
        now = datetime.datetime.now()
        iteration = 0
        while True:
            self.file = str(self.base_path) + 'log_' + now.strftime('%Y%m%d_') + str(iteration) + '.log'
            if not os.path.isfile(self.file):
                break
            iteration += 1

    # Overrides original print function
    def print(self, *args, **kwargs):
        # prints to console
        self._print(*args, **kwargs)
        # logs to file
        if self.enable_logs:
            timestamp = datetime.datetime.now().ctime()
            with open(self.file, "a+") as log:
                self._print(timestamp + ' --', *args, file=log, **kwargs)
