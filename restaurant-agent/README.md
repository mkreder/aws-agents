# Restaurant Chatbot Agent

A production-ready restaurant chatbot built with AWS Bedrock AgentCore and Strands AI framework. The agent handles menu inquiries, reservation management, and customer service interactions using natural language processing.

## 🎯 Features

- **Menu Search**: AI-powered menu search using AWS Bedrock Knowledge Base with S3 Vectors
- **Reservation Management**: Make, find, modify, and cancel reservations
- **Natural Conversation**: Context-aware responses powered by Claude 3.5 Sonnet
- **DynamoDB Storage**: Persistent reservation data with GSI indexes
- **Production-Ready**: Deployed on AWS Bedrock AgentCore with full observability

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         AWS Bedrock AgentCore               │
│  ┌───────────────────────────────────────┐  │
│  │     Restaurant Agent (Strands)        │  │
│  │  - Claude 3.5 Sonnet                  │  │
│  │  - Multi-tool orchestration           │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
           │           │           │
           ▼           ▼           ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Bedrock  │  │   S3     │  │ DynamoDB │
    │Knowledge │  │ Vectors  │  │Reserva-  │
    │   Base   │  │ Storage  │  │  tions   │
    └──────────┘  └──────────┘  └──────────┘
```

## 📁 Project Structure

```
strands-agent/
├── restaurant_agent.py                    # Main agent implementation (AgentCore entrypoint)
├── infrastructure.yaml                    # CloudFormation template for AWS resources
├── requirements.txt                       # Python dependencies
│
├── demo_restaurant_system.py             # Comprehensive system demo
├── test_restaurant_agent.py              # Unit and integration tests
├── test_live_functionality.py            # Live functionality tests
├── test_working_functionality.py         # Working functionality tests
├── test_aws_integration.py               # AWS integration tests
├── test_s3vectors.py                     # S3 Vectors tests
│
├── create_kb_complete.py                 # Knowledge Base setup script
├── create_kb_simple.py                   # Simple KB setup
├── create_knowledge_base.py              # KB creation utilities
├── menu_processor.py                     # Menu document processing
│
├── kb-config.json                        # Knowledge Base configuration
├── s3vectors_config.json                 # S3 Vectors configuration
├── restaurant-chatbot-infrastructure.yaml # Alternative infrastructure template
└── restaurant-chatbot-basic.yaml         # Basic infrastructure template
```

## 🚀 Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.11+
- `bedrock-agentcore` CLI installed
- AWS Bedrock AgentCore enabled in your account

### Infrastructure Setup

1. **Deploy AWS Infrastructure**:
```bash
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name restaurant-chatbot-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ProjectName=restaurant-chatbot
```

2. **Set up Knowledge Base** (S3 Vectors):
```bash
# Create Knowledge Base with menu documents
python create_kb_complete.py
```

3. **Upload Menu Documents**:
```bash
aws s3 cp menu-documents/ s3://restaurant-chatbot-menu-documents-prod/ --recursive
```

### Deploy Agent to AgentCore

Deploy the agent to AWS Bedrock AgentCore:

```bash
bedrock-agentcore deploy \
  --name restaurant_agent \
  --file restaurant_agent.py \
  --runtime python3.11 \
  --region us-east-1
```

The agent will be automatically deployed and available at the endpoint shown in the output.

## 💬 Invoking the Agent

### Using AgentCore CLI

```bash
agentcore invoke '{
  "message": "I would like to make a reservation for 2 people tomorrow at 7pm. My name is John Smith.",
  "customer_id": "customer-12345",
  "session_id": "session-abc"
}'
```

### Request Payload Format

```json
{
  "message": "Customer's message text",
  "customer_id": "unique-customer-id",
  "session_id": "session-identifier"
}
```

**Parameters:**
- `message` (required): The customer's message or request
- `customer_id` (optional): Unique customer identifier (defaults to "anonymous")
- `session_id` (optional): Session identifier for conversation tracking (defaults to "default-session")

### Response Format

```json
{
  "status": "success",
  "response": "Agent's response text",
  "customer_id": "customer-12345",
  "session_id": "session-abc",
  "message": "Customer request processed successfully"
}
```

### Example Interactions

**Menu Search:**
```bash
agentcore invoke '{"message": "What pasta dishes do you have?"}'
```

Response:
```
We have three delicious pasta dishes on our menu:

1. 🍝 Cacio e Pepe ($22) - A classic Roman pasta dish featuring spaghetti
   with aged pecorino romano and freshly cracked black pepper. This is a
   vegetarian option.

2. 🍝 Pork Bolognese ($26) - A hearty pappardelle pasta with slow-braised
   pork and veal ragu, garnished with fresh herbs. This is our rich,
   meat-based pasta option.

3. 🦞 Lobster Ravioli ($34) - Our house-made ravioli filled with Maine lobster,
   served in a delicate saffron cream sauce. This is a pescatarian option
   and one of our specialty dishes.

All of our pasta dishes are made with high-quality ingredients. Would you like
any specific information about any of these dishes, such as ingredients or
dietary restrictions?
```

**Make Reservation:**
```bash
agentcore invoke '{
  "message": "I need a reservation for 4 people on 2025-12-25 at 19:30. My name is Jane Doe, phone 555-1234, email jane@example.com",
  "customer_id": "jane-doe-001"
}'
```

Response:
```
Excellent! I've successfully made your Christmas dinner reservation.
Here's a summary of your confirmed reservation:

🎄 Reservation Details:
- Reservation ID: RES-20250930142316
- Name: Jane Doe
- Party Size: 4 people
- Date: December 25, 2025
- Time: 7:30 PM
- Phone: 555-1234
- Email: jane@example.com

A few important notes:
- Please arrive 15 minutes before your reservation time
- Keep your reservation ID (RES-20250930142316) handy in case you need to
  make any changes
- If you need to modify or cancel your reservation, just let me know and
  provide the reservation ID
```

**Find Reservation:**
```bash
agentcore invoke '{
  "message": "Can you find my reservation? My name is Jane Doe",
  "customer_id": "jane-doe-001"
}'
```

**Modify Reservation:**
```bash
agentcore invoke '{
  "message": "I need to change my reservation RES-20250930142316 to 8 PM instead",
  "customer_id": "jane-doe-001"
}'
```

**Cancel Reservation:**
```bash
agentcore invoke '{
  "message": "Please cancel reservation RES-20250930142316",
  "customer_id": "jane-doe-001"
}'
```

## 🔧 Configuration

### Environment Variables

The agent uses the following environment variables (configured in restaurant_agent.py):

```python
MODEL_ID = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
KNOWLEDGE_BASE_ID = 'B1SFIGE9V1'  # Your Knowledge Base ID
RESERVATIONS_TABLE = 'restaurant-chatbot-reservations-prod'
MENU_BUCKET = 'restaurant-chatbot-menu-documents-prod'
```

Update these in the agent code before deployment or set them in the AgentCore runtime configuration.

## 🛠️ Available Tools

The agent has access to 5 specialized tools:

1. **search_menu**: Search menu items using Bedrock Knowledge Base
2. **make_reservation**: Create new reservations with customer details
3. **find_reservation**: Look up reservations by ID, name, or phone
4. **modify_reservation**: Update existing reservation details
5. **cancel_reservation**: Cancel reservations by ID

## 🧪 Testing

### Run Local Tests

```bash
# Test agent locally (without AgentCore)
python test_restaurant_agent.py

# Test live functionality
python test_live_functionality.py

# Run comprehensive demo
python demo_restaurant_system.py

# Test AWS integration
python test_aws_integration.py
```

### Check AgentCore Status

```bash
agentcore status
```

### View CloudWatch Logs

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_agent-IlKzk57uxO-DEFAULT \
  --log-stream-name-prefix "2025/09/30/[runtime-logs]" \
  --follow
```

## 📊 Monitoring

### Agent Status
```bash
agentcore status
```

### Knowledge Base Status
```bash
# Check KB ingestion status
aws bedrock-agent list-data-sources --knowledge-base-id B1SFIGE9V1
```

### DynamoDB Metrics
```bash
# Check reservation count
aws dynamodb scan --table-name restaurant-chatbot-reservations-prod --select COUNT
```

## 🗄️ Database Schema

### Reservations Table (DynamoDB)

**Primary Key**: `reservation_id` (String)

**Global Secondary Indexes**:
- `CustomerNameIndex`: Search by customer name
- `ReservationDateIndex`: Search by reservation date

**Attributes**:
```json
{
  "reservation_id": "RES-20251225193000",
  "customer_name": "John Smith",
  "party_size": 4,
  "reservation_date": "2025-12-25",
  "reservation_time": "19:30",
  "reservation_datetime": "2025-12-25T19:30:00",
  "phone": "555-1234",
  "email": "john@example.com",
  "status": "confirmed",
  "created_at": "2025-09-30T10:00:00",
  "modified_at": "2025-09-30T10:00:00"
}
```

## 🔐 IAM Permissions

The agent requires the following AWS permissions:
- Bedrock: `InvokeModel`, `Retrieve`, `RetrieveAndGenerate`
- S3: Read/Write to menu documents and vector storage buckets
- DynamoDB: Full CRUD on reservations table
- CloudWatch Logs: Write access

See `infrastructure.yaml` for complete IAM policy definitions.

## 📦 Dependencies

```
strands-agents
bedrock-agentcore
boto3
python-dateutil
```

## 🌐 AWS Resources

### Deployed Resources

| Resource | Name | ID/ARN |
|----------|------|--------|
| Knowledge Base | Restaurant Menu KB | B1SFIGE9V1 |
| S3 Bucket (Menu) | restaurant-chatbot-menu-documents-prod | - |
| S3 Vector Bucket | restaurant-chatbot-vectors-prod | - |
| DynamoDB Table | restaurant-chatbot-reservations-prod | - |
| AgentCore Runtime | restaurant_agent | arn:aws:bedrock-agentcore:us-east-1:479047237979:runtime/restaurant_agent-IlKzk57uxO |

## 🐛 Troubleshooting

### Agent Not Responding
```bash
# Check agent status
agentcore status

# Check CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_agent-IlKzk57uxO-DEFAULT \
  --log-stream-name-prefix "2025/09/30/[runtime-logs]" --since 1h
```

### Menu Search Not Working
```bash
# Verify Knowledge Base status
aws bedrock-agent get-knowledge-base --knowledge-base-id B1SFIGE9V1

# Check data source ingestion
aws bedrock-agent list-data-sources --knowledge-base-id B1SFIGE9V1
```

### Reservations Failing
```bash
# Verify DynamoDB table
aws dynamodb describe-table --table-name restaurant-chatbot-reservations-prod

# Check IAM permissions
aws iam get-role-policy --role-name restaurant-chatbot-agentcore-execution-role --policy-name RestaurantChatbotAgentPolicy
```

## 🚀 Next Steps

1. **Production Hardening**:
   - Add input validation and sanitization
   - Implement rate limiting
   - Add authentication/authorization
   - Set up alerts and monitoring

2. **Feature Enhancements**:
   - Add availability checking
   - Integrate payment processing
   - Add SMS/email notifications
   - Multi-language support

3. **Scaling**:
   - Configure auto-scaling policies
   - Add caching layer (ElastiCache)
   - Implement connection pooling
   - Set up multi-region deployment

## 📄 License

This project is provided as-is for demonstration purposes.

## 🤝 Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review AWS Bedrock AgentCore documentation
3. Verify all AWS resources are properly configured