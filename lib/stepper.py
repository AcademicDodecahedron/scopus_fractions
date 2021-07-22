from typing import List

class Stepper:
    def __init__(
        self,
        start: int,
        total: int,
        steps: List[int]
    ):
        self.total = total
        self.steps = steps
        self.index = 0
        self.start_current = start

    def reset_step(self):
        self.index = 0

    def step_success(self):
        self.start_current += self.steps[self.index]
        self.reset_step()

    #Если запись была пропущена, возвращает ее номер
    def step_failed(self):
        self.index += 1
        if self.index >= len(self.steps):
            start_previous = self.start_current
            self.start_current += 1
            self.reset_step()
            return start_previous

    def __iter__(self):
        while self.start_current <= self.total:
            steps_current = self.steps[self.index]
            if (self.start_current + steps_current - 1) > self.total:
                steps_current = self.total - self.start_current + 1;

            yield self.start_current, steps_current
