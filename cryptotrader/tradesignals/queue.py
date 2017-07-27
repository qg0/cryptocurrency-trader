class Queue(object):
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return len(self.items) == 0

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()
    
    def peek(self):
        if self.isEmpty():
            return None
        return self.items[self.size()-1]

    def size(self):
        return len(self.items)