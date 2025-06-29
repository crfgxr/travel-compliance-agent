# ✈️ Travel Compliance Agent

> **Version 0.3**

![An AI-agent powered automation solution for auditing travel booking compliance](images/bot.png)

## 🎯 Project Overview

This system automatically audits travel bookings against three key compliance rules:

1. **Flight Ticket Timing** - Ensures departure and arrival times fall within approved travel periods
2. **Passenger Identity** - Validates passenger name consistency between approvals and reservations
3. **Route Compliance** - Checks prefered airline's routes from json database

### Application Flow Diagram

![Travel Compliance Agent Architecture Diagram](images/flow-diagram.png)

The system follows a clear sequential flow from API key validation through compliance checking to report generation, with proper error handling at each stage.

## 🚀 Tech Stack

- **AI Model**: OpenAI reasoning models - Complex compliance rule interpretation
- **AI Framework**: LangChain - Mature ecosystem for simplified LLM integration and prompt management
- **Backend**: Python 3.9+ - Native AI/ML ecosystem enabling rapid prototyping and maintainable code
- **UI**: Streamlit - Rapid web development with rich UI components and seamless Python integration
- **Testing**: Pytest - Standard testing framework with comprehensive coverage
- **Environment**: python-dotenv - Secure environment variable management

## 🖥️ Work Examples

The application provides an intuitive web interface for compliance auditing:

**Input Interface:**
![Input Example](images/input_example.png)

**Output Results:**
![Output Example](images/output_example.png)

_The interface shows real-time compliance checking with detailed violation reports and technical details for transparency._

## 📦 Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd travel-compliance-agent
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Run the application**

```bash
streamlit run app.py
```

## 🧪 Testing

The project includes a comprehensive test suite covering all compliance rules with both PASS and FAIL scenarios.

### **Prerequisites**

```bash
# Install pytest (included in requirements.txt)
pip install pytest

# Optional: Set OpenAI API key for AI-dependent tests
export OPENAI_API_KEY="your-api-key-here"
```

### **Running Tests**

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test categories
pytest tests/test_compliance.py::TestTimingCompliance -v
pytest tests/test_compliance.py::TestRouteCompliance -v

# Run without API key (skips AI-dependent tests)
pytest tests/ -v  # Will automatically skip LLM tests if no API key
```

### **Test Coverage**

| Test Category           | Purpose                           |
| ----------------------- | --------------------------------- |
| **Structured Output**   | Validates AI agent configuration  |
| **Timing Compliance**   | Tests flight timing rules         |
| **Identity Compliance** | Tests passenger name matching     |
| **Route Compliance**    | Tests airline route violations    |
| **Integration Tests**   | Full compliance report generation |
| **Data Validation**     | JSON structure compatibility      |

### **Test Scenarios**

- ✅ **PASS Scenarios**: Valid compliance cases
- ❌ **FAIL Scenarios**: Violation detection
- ⚠️ **Edge Cases**: System error handling
- 🔧 **Integration**: End-to-end workflow testing

### **Example Test Output**

```bash
$ pytest tests/ -v

tests/test_compliance.py::TestTimingCompliance::test_valid_timing_compliance PASSED
tests/test_compliance.py::TestTimingCompliance::test_departure_before_travel_period PASSED
tests/test_compliance.py::TestRouteCompliance::test_invalid_route_compliance_sunexpress PASSED
tests/test_compliance.py::TestDataStructures::test_data_structure_compatibility PASSED

====== 12 passed, 3 skipped in 2.34s ======
```

_Tests automatically skip AI-dependent checks when OpenAI API key is not configured._

## 🔮 Possible Iterations

The following improvements are planned to enhance the system's capabilities and production readiness:

### 🏗️ Architecture & Infrastructure

- **Frontend Migration to React** - Transition from Streamlit to React-based frontend for improved state management, enhanced user experience, and better scalability
- **Serverless Architecture** - Refactor to serverless deployment with automated alert mechanisms for cost-effective, event-driven processing
- **Retry Mechanisms** - Implement robust retry logic with exponential backoff for improved reliability and fault tolerance across all external API calls

### 🤖 AI & Model Enhancements

- **Improve Model Support** - Integrate additional AI model providers (Anthropic Claude, Google Gemini, DeepSeek or Grok) for enhanced flexibility and cost comparison
- **Dynamic Schema Understanding** - Enable agents to dynamically parse and understand JSON field structures through integrated API documentation uploads
- **LLM Monitoring & Observability** - Implement comprehensive monitoring for model performance, token usage, response quality, and error tracking

### 📊 Data & Integration

- **Real-time Data Fetching** - Replace static JSON databases with live API integrations for airline routes, approval workflows, and ticket reservations
- **Cost Tracking & Analytics** - Implement detailed cost monitoring for API usage, processing time, and operational expenses with automated reporting

### 💰 Enhanced Compliance Rules

- **Cost Compliance** - Check if ticket prices stay within company budget limits. Set max spending amounts for different employee levels. Make sure people book the right cabin class

### 💬 Chat with Data Features

- **Ask Questions** - Let users chat with their travel data. Ask things like "Show me all trips over $5000" or "Which flights were booked late?"
- **Smart Search** - Find travel records by talking in plain English. No need to know database terms or write complex searches
- **Data Insights** - Get quick answers about travel patterns, spending trends, and policy violations by just asking
- **Export Chat Results** - Save chat answers as reports for managers and finance teams

### 🔧 Operations & Monitoring

- **Performance Metrics** - Add comprehensive dashboards for system health, processing times, and compliance audit success rates
- **Automated Alerting** - Configure intelligent notification systems for compliance violations, system errors, and operational anomalies
