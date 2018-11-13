class Session():
    def __init__(self, matcher):
        self.messages = []
        self.matcher = matcher

    def message(self, message):
        self.messages.append(message)
        message.resolve_objects(self)
        if self.matcher.matches(message):
            print(message)

    def print_messages(self, matcher):
        for i in self.messages:
            if matcher.matches(i):
                print(i)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
