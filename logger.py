"""Special logging class that maintains a buffer of everything that has been logged."""


class Logger(object):

    def __init__(self, flush_to_file):
        self.log_buffer = []
        self.flush_to_file = flush_to_file

    def Log(self, message):
        print(message)
        self.log_buffer.append(message)

    def GetBuffer(self):
        return list(self.log_buffer)

    def ClearBuffer(self):
        if self.flush_to_file:
            with open('log.txt', 'w') as log_file:
                for log_line in self.log_buffer:
                    log_file.write(log_line)
                    log_file.write('\n')
        self.log_buffer = []



