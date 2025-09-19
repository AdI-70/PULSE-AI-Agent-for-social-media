"""
Load testing for Pulse API using Locust
"""

from locust import HttpUser, task, between, events
import random
import string

# Sample niches for testing
NICHES = [
    "technology", "artificial intelligence", "machine learning", 
    "cybersecurity", "blockchain", "cloud computing", 
    "data science", "software engineering", "mobile development"
]

def random_string(length=10):
    """Generate a random string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class PulseUser(HttpUser):
    """Locust user class for Pulse API load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session."""
        # In a real implementation, you might authenticate here
        self.user_id = random_string(8)
    
    @task(3)
    def fetch_articles(self):
        """Test fetching articles for a random niche."""
        niche = random.choice(NICHES)
        self.client.get(f"/articles/{niche}", name="/articles/[niche]")
    
    @task(2)
    def create_summary(self):
        """Test creating a summary."""
        self.client.post("/summarize", json={
            "article_id": random.randint(1, 1000),
            "max_length": 280
        }, name="/summarize")
    
    @task(1)
    def publish_post(self):
        """Test publishing a post."""
        self.client.post("/publish", json={
            "content": f"Test post from load test user {self.user_id}",
            "platform": "x"
        }, name="/publish")
    
    @task(1)
    def get_system_status(self):
        """Test getting system status."""
        self.client.get("/status", name="/status")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint."""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")


# Custom event handlers
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when a test is started."""
    print("Starting Pulse API load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when a test is stopped."""
    print("Pulse API load test completed.")


# Custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Called for each request."""
    if exception:
        print(f"Request failed: {name} - {exception}")
    else:
        if response_time > 2000:  # Log slow requests
            print(f"Slow request: {name} took {response_time}ms")


if __name__ == "__main__":
    import os
    os.system("locust -f pulse_load_test.py --host=http://localhost:8000")