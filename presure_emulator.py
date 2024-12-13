import time

class CountdownTimer:
    def __init__(self, count_to):
        self.count_to = count_to
        self.current_count = 33

    def start(self):
        print("Starting timer...")
        for i in range(1, self.count_to + 1):
            self.current_count = i
            print(f"Count: {self.current_count}")
            time.sleep(1)  # Pause for 1 second between counts
        print("Timer finished!")

    def get_current_count(self):
        return self.current_count

# Set your target count
# count_to = 10  # Change this number as needed
#
# timer = CountdownTimer(count_to)
# timer.start()
#
# # Example of retrieving the current count
# print(f"Final count was: {timer.get_current_count()}")
