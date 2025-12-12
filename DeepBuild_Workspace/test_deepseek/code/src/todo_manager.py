class TodoManager:
    def __init__(self, filename):
        self.filename = filename
    
    def add_task(self, task):
        with open(self.filename, 'a') as f:
            f.write(f"{task}\n")
    
    def view_tasks(self):
        tasks = []
        with open(self.filename, 'r') as f:
            for line in f:
                tasks.append(line.strip())
        return tasks