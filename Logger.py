import datetime
import os.path
import logging.handlers


class Logger:
    file = None
    _print = print
    logger = logging.getLogger('discord')

    def __init__(self, base_path, enable_logs, log_level=logging.INFO):
        self.base_path = base_path
        self.enable_logs = enable_logs

        formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', '%Y-%m-%d %H:%M:%S', style='{')

        self.logger.setLevel(log_level)
        logging.getLogger('discord.http').setLevel(logging.INFO)

        handler = logging.handlers.RotatingFileHandler(
            filename='discord.log',
            encoding='utf-8',
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.setup_log_file()

    def setup_log_file(self):
        now = datetime.datetime.now()
        iteration = 0
        while True:
            self.file = str(self.base_path) + 'log_' + now.strftime('%Y%m%d_') + str(iteration) + '.log'
            if not os.path.isfile(self.file):
                break
            iteration += 1

        # Overrides original print function
    def print(self, log_level, print_statement):
        if self.enable_logs and log_level >= self.logger.level:
            timestamp = datetime.datetime.now().ctime()
            log_message = f"[{timestamp}] [{self.get_log_level_name(log_level)}] -- {print_statement}"
            
            # prints to console
            self._print(print_statement)

            # prints to log file
            with open(self.file, "a+") as log:
                self._print(log_message, file=log)

    def get_log_level_name(self, log_level):
        if log_level == 0:
            return "TRACE"
        else:
            return logging.getLevelName(log_level)

    def trace(self, print_statement):
        self.print(logging.NOTSET, print_statement)

    def debug(self, print_statement):
        self.print(logging.DEBUG, print_statement)

    def info(self, print_statement):
        self.print(logging.INFO, print_statement)

    def warning(self, print_statement):
        self.print(logging.WARNING, print_statement)

    def error(self, print_statement):
        self.print(logging.ERROR, print_statement)

    def critical(self, print_statement):
        self.print(logging.CRITICAL, print_statement)
