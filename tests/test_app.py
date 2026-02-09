"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        key: {
            "description": val["description"],
            "schedule": val["schedule"],
            "max_participants": val["max_participants"],
            "participants": val["participants"].copy()
        }
        for key, val in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for key in activities:
        activities[key]["participants"] = original_activities[key]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball League" in data
        assert "Volleyball Team" in data
        assert "Chess Club" in data
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
    
    def test_get_activities_participants_are_lists(self, client, reset_activities):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student(self, client, reset_activities):
        """Test signing up a new student for an activity"""
        new_email = "test@mergington.edu"
        activity_name = "Basketball League"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Test that signing up the same student twice fails"""
        email = "james@mergington.edu"  # Already signed up for Basketball League
        activity_name = "Basketball League"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for non-existent activity fails"""
        email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        email = "newstudent@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Basketball League/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        assert email in activities["Basketball League"]["participants"]
        assert email in activities["Chess Club"]["participants"]


class TestRemoveFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_remove_existing_participant(self, client, reset_activities):
        """Test removing a participant from an activity"""
        email = "james@mergington.edu"  # Already signed up for Basketball League
        activity_name = "Basketball League"
        initial_count = len(activities[activity_name]["participants"])
        
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing non-existent participant fails"""
        email = "nonexistent@mergington.edu"
        activity_name = "Basketball League"
        
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from non-existent activity fails"""
        email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_remove_and_readd_participant(self, client, reset_activities):
        """Test that a removed participant can be added back"""
        email = "james@mergington.edu"
        activity_name = "Basketball League"
        
        # Remove
        response_delete = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response_delete.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Re-add
        response_add = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response_add.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""
    
    def test_full_workflow(self, client, reset_activities):
        """Test complete workflow: get activities, sign up, check, remove"""
        # Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        initial_activities = response.json()
        
        # Sign up
        email = "fullworkflow@mergington.edu"
        activity = "Drama Club"
        initial_participants = len(initial_activities[activity]["participants"])
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup in state
        assert email in activities[activity]["participants"]
        
        # Remove
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify removal
        assert email not in activities[activity]["participants"]
