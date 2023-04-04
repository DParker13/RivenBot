import datetime
import os.path


class Logger:
    file = None
    _print = print

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
