import json
import logging
import os
from typing import Dict, Any, List
import boto3
from datetime import datetime, timedelta

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_agent_client = boto3.client('bedrock-agent-runtime')

# Environment variables - Updated with deployed infrastructure
MODEL_ID = os.environ.get('MODEL_ID', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'B1SFIGE9V1')  # S3 Vectors Knowledge Base ID
RESERVATIONS_TABLE = os.environ.get('RESERVATIONS_TABLE', 'restaurant-chatbot-reservations-prod')
MENU_BUCKET = os.environ.get('MENU_BUCKET', 'restaurant-chatbot-menu-documents-prod')

# Initialize AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """AgentCore entrypoint for Restaurant Chatbot"""
    try:
        logger.info(f"🍽️ Restaurant Chatbot - Processing payload: {payload}")

        # Extract parameters from payload (support both 'message' and 'prompt' for compatibility)
        customer_message = payload.get('message', '') or payload.get('prompt', '')
        customer_id = payload.get('customer_id', 'anonymous')
        session_id = payload.get('session_id', 'default-session')

        if not customer_message:
            raise ValueError("message or prompt is required in payload")

        # Process the customer message using Strands restaurant agent
        result = process_customer_request(customer_message, customer_id, session_id)

        return {
            "status": "success",
            "response": result.get('response'),
            "customer_id": customer_id,
            "session_id": session_id,
            "message": "Customer request processed successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error in Restaurant Chatbot processing: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "response": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
            "message": "Customer request processing failed"
        }

def process_customer_request(message: str, customer_id: str, session_id: str) -> Dict[str, Any]:
    """Process customer request using restaurant chatbot agents"""
    try:
        # Create the Restaurant Chatbot supervisor agent
        chatbot_agent = create_restaurant_chatbot()

        # Create context for the request
        request_context = f"""
        Customer Message: {message}
        Customer ID: {customer_id}
        Session ID: {session_id}
        Timestamp: {datetime.utcnow().isoformat()}

        Please help this customer with their restaurant request. You can:
        1. Answer questions about our menu items
        2. Help make, modify, or cancel reservations
        3. Provide restaurant information
        4. Assist with any other restaurant-related inquiries

        Use your specialized tools to provide helpful and accurate responses.
        """

        # Process the customer request
        logger.info("🍽️ Processing customer request with restaurant chatbot...")
        chatbot_response = chatbot_agent(request_context)
        logger.info("✅ Restaurant chatbot response generated")

        # Extract and format the response
        response_text = safe_extract_content(chatbot_response)

        return {
            "response": response_text,
            "customer_id": customer_id,
            "session_id": session_id,
            "processed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in customer request processing: {str(e)}")
        raise

def create_restaurant_chatbot():
    """Create the Restaurant Chatbot supervisor agent with specialized tools"""

    @tool
    def search_menu(query: str) -> str:
        """Search menu items using AWS Bedrock Knowledge Base"""
        try:
            logger.info(f"🔍 Searching menu for: {query}")

            # Use Bedrock Knowledge Base to search menu
            response = bedrock_agent_client.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10
                    }
                }
            )

            # Process search results
            menu_items = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0)
                location = result.get('location', {})

                menu_items.append({
                    'content': content,
                    'relevance_score': score,
                    'source': location.get('s3Location', {}).get('uri', 'Unknown')
                })

            # Format results for agent consumption
            if menu_items:
                formatted_results = "Menu search results:\n\n"
                for i, item in enumerate(menu_items[:5]):  # Top 5 results
                    formatted_results += f"{i+1}. {item['content']}\n"
                    formatted_results += f"   (Relevance: {item['relevance_score']:.2f})\n\n"
                return formatted_results
            else:
                return f"No menu items found matching '{query}'. Please try a different search term."

        except Exception as e:
            logger.error(f"❌ Error searching menu: {str(e)}")
            return f"I'm having trouble searching our menu right now. Please try again later or ask our staff directly."

    @tool
    def make_reservation(customer_name: str, party_size: int, date: str, time: str, phone: str = "", email: str = "") -> str:
        """Make a new restaurant reservation"""
        try:
            logger.info(f"📅 Making reservation for {customer_name}, party of {party_size} on {date} at {time}")

            # Generate reservation ID
            reservation_id = f"RES-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # Parse date and time
            reservation_datetime = datetime.fromisoformat(f"{date}T{time}")

            # Create reservation record
            reservation_data = {
                'reservation_id': reservation_id,
                'customer_name': customer_name,
                'party_size': party_size,
                'reservation_date': date,
                'reservation_time': time,
                'reservation_datetime': reservation_datetime.isoformat(),
                'phone': phone,
                'email': email,
                'status': 'confirmed',
                'created_at': datetime.utcnow().isoformat(),
                'modified_at': datetime.utcnow().isoformat()
            }

            # Store in DynamoDB
            reservations_table = dynamodb.Table(RESERVATIONS_TABLE)
            reservations_table.put_item(Item=reservation_data)

            logger.info(f"✅ Reservation created: {reservation_id}")

            return f"""
Reservation confirmed! Here are your details:

Reservation ID: {reservation_id}
Name: {customer_name}
Party Size: {party_size} people
Date & Time: {date} at {time}
Status: Confirmed

Please arrive 15 minutes early. If you need to modify or cancel your reservation,
please provide your reservation ID: {reservation_id}
            """.strip()

        except Exception as e:
            logger.error(f"❌ Error making reservation: {str(e)}")
            return f"I'm sorry, I couldn't complete your reservation. Please try again or call us directly."

    @tool
    def find_reservation(reservation_id: str = "", customer_name: str = "", phone: str = "") -> str:
        """Find existing reservations by ID, name, or phone"""
        try:
            logger.info(f"🔍 Finding reservation - ID: {reservation_id}, Name: {customer_name}, Phone: {phone}")

            reservations_table = dynamodb.Table(RESERVATIONS_TABLE)

            if reservation_id:
                # Search by reservation ID
                response = reservations_table.get_item(Key={'reservation_id': reservation_id})
                if 'Item' in response:
                    reservation = response['Item']
                    return format_reservation_details(reservation)
                else:
                    return f"No reservation found with ID: {reservation_id}"

            else:
                # Search by name or phone using scan (in production, consider using GSI)
                filter_conditions = []
                expression_values = {}

                if customer_name:
                    filter_conditions.append("contains(customer_name, :name)")
                    expression_values[':name'] = customer_name

                if phone:
                    filter_conditions.append("phone = :phone")
                    expression_values[':phone'] = phone

                if not filter_conditions:
                    return "Please provide either a reservation ID, customer name, or phone number to search."

                # Scan with filter
                response = reservations_table.scan(
                    FilterExpression=' OR '.join(filter_conditions),
                    ExpressionAttributeValues=expression_values
                )

                reservations = response.get('Items', [])
                if reservations:
                    # Return details for found reservations
                    results = []
                    for reservation in reservations[:5]:  # Limit to 5 results
                        results.append(format_reservation_details(reservation))
                    return "\n\n".join(results)
                else:
                    search_terms = []
                    if customer_name: search_terms.append(f"name '{customer_name}'")
                    if phone: search_terms.append(f"phone '{phone}'")
                    return f"No reservations found for {' or '.join(search_terms)}."

        except Exception as e:
            logger.error(f"❌ Error finding reservation: {str(e)}")
            return "I'm having trouble accessing reservation information right now. Please try again later."

    @tool
    def modify_reservation(reservation_id: str, new_date: str = "", new_time: str = "", new_party_size: str = "") -> str:
        """Modify an existing reservation"""
        try:
            logger.info(f"✏️ Modifying reservation {reservation_id}")

            reservations_table = dynamodb.Table(RESERVATIONS_TABLE)

            # First, get the existing reservation
            response = reservations_table.get_item(Key={'reservation_id': reservation_id})
            if 'Item' not in response:
                return f"No reservation found with ID: {reservation_id}"

            reservation = response['Item']
            updates = {}
            update_expression_parts = []
            expression_values = {}

            # Build update expression
            if new_date:
                updates['reservation_date'] = new_date
                update_expression_parts.append("reservation_date = :date")
                expression_values[':date'] = new_date

            if new_time:
                updates['reservation_time'] = new_time
                update_expression_parts.append("reservation_time = :time")
                expression_values[':time'] = new_time

            if new_party_size:
                party_size_int = int(new_party_size)
                updates['party_size'] = party_size_int
                update_expression_parts.append("party_size = :size")
                expression_values[':size'] = party_size_int

            if not updates:
                return "No changes specified. Please provide new date, time, or party size."

            # Update modified timestamp
            update_expression_parts.append("modified_at = :modified")
            expression_values[':modified'] = datetime.utcnow().isoformat()

            # Update reservation datetime if date or time changed
            if new_date or new_time:
                final_date = new_date if new_date else reservation['reservation_date']
                final_time = new_time if new_time else reservation['reservation_time']
                final_datetime = datetime.fromisoformat(f"{final_date}T{final_time}")
                update_expression_parts.append("reservation_datetime = :datetime")
                expression_values[':datetime'] = final_datetime.isoformat()

            # Perform the update
            reservations_table.update_item(
                Key={'reservation_id': reservation_id},
                UpdateExpression="SET " + ", ".join(update_expression_parts),
                ExpressionAttributeValues=expression_values
            )

            logger.info(f"✅ Reservation {reservation_id} updated successfully")

            # Get updated reservation details
            updated_response = reservations_table.get_item(Key={'reservation_id': reservation_id})
            updated_reservation = updated_response['Item']

            return f"Reservation updated successfully!\n\n{format_reservation_details(updated_reservation)}"

        except Exception as e:
            logger.error(f"❌ Error modifying reservation: {str(e)}")
            return f"I couldn't update your reservation. Please try again or call us directly."

    @tool
    def cancel_reservation(reservation_id: str) -> str:
        """Cancel an existing reservation"""
        try:
            logger.info(f"❌ Canceling reservation {reservation_id}")

            reservations_table = dynamodb.Table(RESERVATIONS_TABLE)

            # Update reservation status to cancelled
            response = reservations_table.update_item(
                Key={'reservation_id': reservation_id},
                UpdateExpression="SET #status = :cancelled, modified_at = :modified",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':cancelled': 'cancelled',
                    ':modified': datetime.utcnow().isoformat()
                },
                ReturnValues="ALL_NEW"
            )

            if 'Attributes' in response:
                logger.info(f"✅ Reservation {reservation_id} cancelled")
                return f"Reservation {reservation_id} has been cancelled successfully. We hope to see you again soon!"
            else:
                return f"No reservation found with ID: {reservation_id}"

        except Exception as e:
            logger.error(f"❌ Error canceling reservation: {str(e)}")
            return f"I couldn't cancel your reservation. Please try again or call us directly."

    # Create the main Restaurant Chatbot Agent
    chatbot_agent = Agent(
        model=MODEL_ID,
        tools=[
            search_menu,
            make_reservation,
            find_reservation,
            modify_reservation,
            cancel_reservation
        ],
        system_prompt="""You are a friendly and helpful Restaurant Chatbot Assistant powered by Amazon Bedrock AgentCore.

Your role is to help customers with:
1. 🍽️ Menu inquiries - Search and recommend dishes, explain ingredients, dietary options
2. 📅 Reservations - Make, find, modify, or cancel reservations
3. ℹ️ Restaurant information - Hours, location, policies, special events

GUIDELINES:
- Be warm, welcoming, and professional
- Use your tools to provide accurate, up-to-date information
- For menu searches, always use the search_menu tool to get current menu items
- For reservations, collect all necessary information (name, party size, date, time)
- Always confirm reservation details before finalizing
- If you can't find specific information, offer to connect them with restaurant staff
- Be proactive in suggesting related items or alternatives

RESERVATION FORMAT:
- Date: YYYY-MM-DD format
- Time: HH:MM format (24-hour)
- Always confirm availability (assume available unless system indicates otherwise)

CONVERSATION STYLE:
- Start with a warm greeting if it's the beginning of a conversation
- Use food emojis appropriately but not excessively
- Ask clarifying questions when needed
- Summarize important information clearly
- End interactions by offering additional assistance

Remember: You represent our restaurant's hospitality and service standards. Make every interaction memorable and positive!"""
    )

    return chatbot_agent

def format_reservation_details(reservation: Dict[str, Any]) -> str:
    """Format reservation details for display"""
    status_emoji = "✅" if reservation.get('status') == 'confirmed' else "❌"

    details = f"""
{status_emoji} Reservation Details:
Reservation ID: {reservation.get('reservation_id', 'N/A')}
Name: {reservation.get('customer_name', 'N/A')}
Party Size: {reservation.get('party_size', 'N/A')} people
Date & Time: {reservation.get('reservation_date', 'N/A')} at {reservation.get('reservation_time', 'N/A')}
Status: {reservation.get('status', 'unknown').title()}
    """.strip()

    if reservation.get('phone'):
        details += f"\nPhone: {reservation['phone']}"
    if reservation.get('email'):
        details += f"\nEmail: {reservation['email']}"

    return details

def safe_extract_content(result) -> str:
    """Extract text content from Strands agent response"""
    try:
        # Handle different response formats (same as HR agent)
        if hasattr(result, 'content') and isinstance(result.content, list):
            text_parts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                else:
                    text_parts.append(str(item))
            return '\n'.join(text_parts)
        elif hasattr(result, 'content'):
            return str(result.content)
        elif hasattr(result, 'message'):
            return str(result.message)
        elif isinstance(result, dict):
            if 'role' in result and 'content' in result:
                content = result['content']
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        else:
                            text_parts.append(str(item))
                    return '\n'.join(text_parts)
                else:
                    return str(content)
            elif 'message' in result:
                message = result['message']
                if isinstance(message, dict) and 'content' in message:
                    content = message['content']
                    if isinstance(content, list):
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                text_parts.append(item['text'])
                            else:
                                text_parts.append(str(item))
                        return '\n'.join(text_parts)
                    else:
                        return str(content)
                else:
                    return str(message)
            return str(result)
        else:
            return str(result)
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return str(result)

if __name__ == "__main__":
    app.run()