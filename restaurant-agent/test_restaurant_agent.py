"""
Test script for Restaurant Chatbot Agent
This script provides unit tests and integration tests for the restaurant chatbot functionality
"""

import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Set AWS profile for testing
os.environ['AWS_PROFILE'] = 'personal'

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our restaurant agent
from restaurant_agent import (
    process_customer_request,
    create_restaurant_chatbot,
    format_reservation_details,
    safe_extract_content,
    STRANDS_AVAILABLE
)

# Try to import pytest, but don't fail if not available
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    print("ℹ️  pytest not available, running manual tests only")

class TestRestaurantAgent:
    """Test suite for Restaurant Chatbot Agent"""

    @patch('restaurant_agent.bedrock_agent_client')
    def test_menu_search_success(self, mock_bedrock_client):
        """Test successful menu search functionality"""
        # Mock the Bedrock Knowledge Base response
        mock_bedrock_client.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'Truffle Arancini - Crispy risotto balls with truffle oil ($14.00)'},
                    'score': 0.95,
                    'location': {'s3Location': {'uri': 's3://menu-bucket/appetizers_truffle_arancini.txt'}}
                },
                {
                    'content': {'text': 'Burrata Caprese - Fresh burrata with tomatoes ($16.00)'},
                    'score': 0.88,
                    'location': {'s3Location': {'uri': 's3://menu-bucket/appetizers_burrata_caprese.txt'}}
                }
            ]
        }

        # Create the chatbot agent
        chatbot = create_restaurant_chatbot()

        # Extract the search_menu tool
        search_tool = None
        for tool in chatbot.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'search_menu':
                search_tool = tool
                break

        assert search_tool is not None, "search_menu tool not found"

        # Test the search functionality
        result = search_tool("truffle appetizer")

        assert "Menu search results:" in result
        assert "Truffle Arancini" in result
        assert "Burrata Caprese" in result
        assert "0.95" in result

    @patch('restaurant_agent.dynamodb')
    def test_make_reservation_success(self, mock_dynamodb):
        """Test successful reservation creation"""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # Create the chatbot agent
        chatbot = create_restaurant_chatbot()

        # Extract the make_reservation tool
        reservation_tool = None
        for tool in chatbot.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'make_reservation':
                reservation_tool = tool
                break

        assert reservation_tool is not None, "make_reservation tool not found"

        # Test reservation creation
        result = reservation_tool("John Doe", 4, "2024-12-15", "19:00", "555-1234", "john@example.com")

        assert "Reservation confirmed!" in result
        assert "John Doe" in result
        assert "4 people" in result
        assert "2024-12-15 at 19:00" in result
        assert mock_table.put_item.called

    @patch('restaurant_agent.dynamodb')
    def test_find_reservation_by_id(self, mock_dynamodb):
        """Test finding reservation by ID"""
        # Mock DynamoDB table and response
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        mock_reservation = {
            'reservation_id': 'RES-20241215123456',
            'customer_name': 'Jane Smith',
            'party_size': 2,
            'reservation_date': '2024-12-15',
            'reservation_time': '18:30',
            'status': 'confirmed',
            'phone': '555-5678',
            'email': 'jane@example.com'
        }

        mock_table.get_item.return_value = {'Item': mock_reservation}

        # Create the chatbot agent
        chatbot = create_restaurant_chatbot()

        # Extract the find_reservation tool
        find_tool = None
        for tool in chatbot.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'find_reservation':
                find_tool = tool
                break

        assert find_tool is not None, "find_reservation tool not found"

        # Test finding reservation
        result = find_tool(reservation_id="RES-20241215123456")

        assert "Jane Smith" in result
        assert "RES-20241215123456" in result
        assert "2024-12-15 at 18:30" in result
        assert "✅" in result  # Confirmed status emoji

    @patch('restaurant_agent.dynamodb')
    def test_modify_reservation(self, mock_dynamodb):
        """Test reservation modification"""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock existing reservation
        existing_reservation = {
            'reservation_id': 'RES-20241215123456',
            'customer_name': 'John Doe',
            'party_size': 4,
            'reservation_date': '2024-12-15',
            'reservation_time': '19:00',
            'status': 'confirmed'
        }

        # Mock updated reservation
        updated_reservation = existing_reservation.copy()
        updated_reservation['party_size'] = 6
        updated_reservation['reservation_time'] = '20:00'

        mock_table.get_item.side_effect = [
            {'Item': existing_reservation},  # First call for initial check
            {'Item': updated_reservation}    # Second call after update
        ]

        # Create the chatbot agent
        chatbot = create_restaurant_chatbot()

        # Extract the modify_reservation tool
        modify_tool = None
        for tool in chatbot.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'modify_reservation':
                modify_tool = tool
                break

        assert modify_tool is not None, "modify_reservation tool not found"

        # Test reservation modification
        result = modify_tool("RES-20241215123456", new_time="20:00", new_party_size="6")

        assert "Reservation updated successfully!" in result
        assert mock_table.update_item.called

    @patch('restaurant_agent.dynamodb')
    def test_cancel_reservation(self, mock_dynamodb):
        """Test reservation cancellation"""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock successful update response
        mock_table.update_item.return_value = {
            'Attributes': {
                'reservation_id': 'RES-20241215123456',
                'status': 'cancelled'
            }
        }

        # Create the chatbot agent
        chatbot = create_restaurant_chatbot()

        # Extract the cancel_reservation tool
        cancel_tool = None
        for tool in chatbot.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'cancel_reservation':
                cancel_tool = tool
                break

        assert cancel_tool is not None, "cancel_reservation tool not found"

        # Test reservation cancellation
        result = cancel_tool("RES-20241215123456")

        assert "cancelled successfully" in result
        assert mock_table.update_item.called

    def test_format_reservation_details(self):
        """Test reservation details formatting"""
        reservation = {
            'reservation_id': 'RES-20241215123456',
            'customer_name': 'Alice Johnson',
            'party_size': 3,
            'reservation_date': '2024-12-15',
            'reservation_time': '18:00',
            'status': 'confirmed',
            'phone': '555-9999',
            'email': 'alice@example.com'
        }

        result = format_reservation_details(reservation)

        assert "✅" in result  # Confirmed status emoji
        assert "Alice Johnson" in result
        assert "RES-20241215123456" in result
        assert "3 people" in result
        assert "2024-12-15 at 18:00" in result
        assert "555-9999" in result
        assert "alice@example.com" in result

    def test_safe_extract_content(self):
        """Test content extraction from various response formats"""
        # Test with simple string
        result = safe_extract_content("Simple text response")
        assert result == "Simple text response"

        # Test with mock object having text content
        mock_response = Mock()
        mock_response.content = [Mock(text="Agent response text")]
        result = safe_extract_content(mock_response)
        assert result == "Agent response text"

        # Test with dict format
        dict_response = {
            'role': 'assistant',
            'content': [{'text': 'Dictionary response'}]
        }
        result = safe_extract_content(dict_response)
        assert result == "Dictionary response"

    @patch('restaurant_agent.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling in various scenarios"""
        # Test with invalid reservation data
        chatbot = create_restaurant_chatbot()

        # This should not raise an exception but handle gracefully
        try:
            # Test with empty customer request
            result = process_customer_request("", "test-customer", "test-session")
            # Should still return a structured response
            assert isinstance(result, dict)
            assert 'response' in result
        except Exception as e:
            # If it does raise an exception, it should be handled gracefully
            assert "error" in str(e).lower() or "empty" in str(e).lower()

class TestIntegration:
    """Integration tests for the complete restaurant chatbot system"""

    @patch('restaurant_agent.bedrock_agent_client')
    @patch('restaurant_agent.dynamodb')
    def test_full_conversation_flow(self, mock_dynamodb, mock_bedrock_client):
        """Test a complete conversation flow from menu search to reservation"""

        # Mock Bedrock Knowledge Base response for menu search
        mock_bedrock_client.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'Dry-Aged Ribeye - 28-day aged steak with bone marrow ($48.00)'},
                    'score': 0.95,
                    'location': {'s3Location': {'uri': 's3://menu-bucket/main_ribeye.txt'}}
                }
            ]
        }

        # Mock DynamoDB table for reservations
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # Test menu inquiry followed by reservation
        menu_result = process_customer_request(
            "What steaks do you have available?",
            "customer-123",
            "session-456"
        )

        assert isinstance(menu_result, dict)
        assert 'response' in menu_result

        # The actual agent interaction would be more complex,
        # but this tests the basic structure

    def test_payload_processing(self):
        """Test payload processing for AgentCore integration"""
        from restaurant_agent import invoke

        # Test with valid payload
        payload = {
            'message': 'Hello, I would like to see your menu',
            'customer_id': 'cust-123',
            'session_id': 'sess-456'
        }

        # Mock the agent processing
        with patch('restaurant_agent.process_customer_request') as mock_process:
            mock_process.return_value = {
                'response': 'Welcome! Let me show you our menu options...',
                'customer_id': 'cust-123',
                'session_id': 'sess-456'
            }

            result = invoke(payload)

            assert result['status'] == 'success'
            assert result['customer_id'] == 'cust-123'
            assert result['session_id'] == 'sess-456'
            assert 'response' in result

        # Test with missing message
        invalid_payload = {
            'customer_id': 'cust-123'
            # Missing 'message' field
        }

        result = invoke(invalid_payload)
        assert result['status'] == 'error'
        assert 'message is required' in result['error']

def run_manual_tests():
    """Run tests manually without pytest"""
    print("🧪 Running Restaurant Chatbot Tests")
    print(f"   Strands Available: {'✅' if STRANDS_AVAILABLE else '⚠️  Mock Mode'}")
    print(f"   Pytest Available: {'✅' if PYTEST_AVAILABLE else '⚠️  Manual Only'}")

    # Create test instances
    agent_tests = TestRestaurantAgent()
    integration_tests = TestIntegration()

    # Run individual tests that work without full Strands
    test_methods = [
        agent_tests.test_format_reservation_details,
        agent_tests.test_safe_extract_content,
        agent_tests.test_error_handling,
        integration_tests.test_payload_processing,
    ]

    passed = 0
    total = len(test_methods)

    for test_method in test_methods:
        try:
            print(f"🔍 Running {test_method.__name__}...")
            test_method()
            print(f"✅ {test_method.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {str(e)}")

    # Try AWS-dependent tests if we can
    if STRANDS_AVAILABLE:
        aws_tests = [
            agent_tests.test_menu_search_success,
            agent_tests.test_make_reservation_success,
            agent_tests.test_find_reservation_by_id,
        ]

        for test_method in aws_tests:
            try:
                print(f"🔍 Running {test_method.__name__} (AWS)...")
                test_method()
                print(f"✅ {test_method.__name__} passed")
                passed += 1
            except Exception as e:
                print(f"⚠️  {test_method.__name__} failed (expected without full setup): {str(e)}")
            total += 1

    print(f"\n🎉 Manual test run completed! {passed}/{total} tests passed")

    if not STRANDS_AVAILABLE:
        print("\n💡 To run full tests:")
        print("   1. Install Strands: pip install strands")
        print("   2. Install AgentCore SDK")
        print("   3. Set up AWS Bedrock Knowledge Base")

    if PYTEST_AVAILABLE and STRANDS_AVAILABLE:
        print("\nTo run full test suite: python -m pytest test_restaurant_agent.py -v")

if __name__ == "__main__":
    run_manual_tests()