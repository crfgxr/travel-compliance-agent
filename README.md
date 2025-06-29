# ✈️ Travel Compliance Agent

An AI-powered automation solution for auditing travel booking compliance using OpenAI GPT-4 and Streamlit.

## 🌐 Live Demo

**Try it now:** [https://travel-compliance-agent-dzk3dyc3ecappn5vr4hsxpo.streamlit.app/](https://travel-compliance-agent-dzk3dyc3ecappn5vr4hsxpo.streamlit.app/)

_Note: You'll need your own OpenAI API key to use the live demo._

## 🎯 Project Overview

This system automatically audits travel bookings against three key compliance rules:

1. **Flight Ticket Timing** - Ensures departure and arrival times fall within approved travel periods
2. **Passenger Identity** - Validates passenger name consistency between approvals and reservations
3. **Route Compliance** - Checks airline usage rules (e.g., SunExpress accounts using non-SunExpress airlines)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │ Compliance      │    │ OpenAI Response │
│   - Data Input  │───▶│ Agent           │───▶│ API             │
│   - Progress    │    │ - Timing Check  │    │   - LangChain   │
│   - Results     │    │ - Identity Check│    │                 │
└─────────────────┘    │ - Route Check   │    └─────────────────┘
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  Rules Engine   │
                       │  - Centralized  │
                       │  - Extensible   │
                       │  - Prompt Gen   │
                       └─────────────────┘
```

## 🔧 Technical Design Details

### Context Window Management

Each compliance agent operates with **independent context windows** - they do **NOT** share the same context:

```python
# Shared LLM Instance (orchestrator.py)
self.llm = ChatOpenAI(model=model, openai_api_key=openai_api_key)
self.timing_agent = TimingAgent(self.llm)      # Gets LLM reference
self.identity_agent = IdentityAgent(self.llm)  # Gets LLM reference
self.route_agent = RouteAgent(self.llm)        # Gets LLM reference
```

**How Each Agent Works:**

1. **TimingAgent**: Opens fresh context → System message + User prompt → API call → Response
2. **IdentityAgent**: Opens fresh context → System message + User prompt → API call → Response
3. **RouteAgent**: Opens fresh context → System message + User prompt → API call → Response

**Key Characteristics:**

- ✅ **Stateless Calls**: Each `llm.invoke()` is completely independent
- ✅ **Clean Context**: No cross-contamination between compliance checks
- ✅ **Focused Analysis**: Each agent sees only relevant data for its specific task
- ❌ **No Shared Memory**: Agents cannot reference previous agent results
- ❌ **Higher Token Usage**: System messages repeated for each call

**API Call Pattern:**

```python
# Each agent makes separate HTTP requests
system_message = SystemMessage(content="You are a travel compliance expert...")
human_message = HumanMessage(content=user_prompt)
response = self.llm.invoke([system_message, human_message])  # New context window
```

**Observable in Logs:**

```
⏰ Running Flight Ticket Timing check (1/3)
HTTP Request: POST https://api.openai.com/v1/chat/completions    # Fresh context
👤 Running Passenger Identity check (2/3)
HTTP Request: POST https://api.openai.com/v1/chat/completions    # Fresh context
✈️ Running SunExpress Route Compliance check (3/3)
HTTP Request: POST https://api.openai.com/v1/chat/completions    # Fresh context
```

This design ensures predictable behavior and prevents context pollution between different compliance domains.

## 🚀 Tech Stack

- **Backend**: Python 3.9+
- **AI Framework**: OpenAI via LangChain
- **UI**: Streamlit
- **Testing**: Pytest
- **Environment**: python-dotenv

### Why This Stack?

- **LLM**: Advanced reasoning models selected for complex compliance scenarios
- **LangChain**: Simplified LLM integration and prompt management
- **Streamlit**: Rapid prototyping with beautiful, interactive UI
- **Native Python**: Lightweight implementation without framework overhead

used those models
latest powerful: gpt-4.1-2025-04-14 https://platform.openai.com/docs/models/gpt-4.1
price senstive reasoning model: o4-mini-2025-04-16 https://platform.openai.com/docs/models/o4-mini

used amadeus airlines for checking airline routes for XQ (Sun Express) recent routes

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

## 🎮 Usage

### Web Interface

1. **Configure API Key**: Enter your OpenAI API key in the sidebar
2. **Load Data**: Either paste JSON data or use sample data button
3. **Run Audit**: Execute compliance checking with real-time progress
4. **Review Results**: See detailed compliance report with expandable violations
5. **Reset**: Clear data and start over

### Sample Data

The system comes with sample data that demonstrates both compliant and non-compliant scenarios:

**Travel Approval Format:**

```json
{
  "data": {
    "travelCity": "Frankfurt",
    "travelCountry": "Germany",
    "travelBeginDate": "2025-06-22T09:00:00",
    "travelEndDate": "2025-06-26T09:00:00",
    "travelReason": "Business",
    "accountName": "SunExpress",
    "passengerList": [
      {
        "name": "Mr. Jhon",
        "surname": "Doe",
        "gender": "Male",
        "emailAddress": "jhon.doe@sunexpress.com",
        "employeeId": "00000001",
        "userType": "user"
      }
    ],
    "Status": "Approved"
  }
}
```

**Flight Ticket Format:**

```json
{
  "data": {
    "flights": [
      {
        "bookingId": "TIC-457855",
        "flights": [
          {
            "flightNumber": "XQ141",
            "airline": "XQ",
            "departureAirport": "AYT",
            "arrivalAirport": "FRA",
            "departureDate": "2025-06-24T07:30:00",
            "arrivalDate": "2025-06-24T09:00:00"
          }
        ],
        "passengers": [
          {
            "name": "Mr. Jhon",
            "surname": "Doe",
            "employeeId": "00000001"
          }
        ]
      }
    ]
  }
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/test_compliance.py::TestTimingCompliance -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Scenarios

- ✅ **PASS Scenarios**: Valid compliance across all rules
- ❌ **FAIL Scenarios**: Various violation types
- ⚠️ **EDGE Cases**: Boundary conditions and data variations
- 🔧 **SYSTEM Errors**: LLM failures and recovery

## 📊 Compliance Rules Details

### 1. Flight Ticket Timing

- **Check**: Departure and arrival times within travel approval period
- **Pass**: All flight times fall within `travelBeginDate` to `travelEndDate` (inclusive)
- **Fail**: Any flight outside approved time window
- **Details**: Boundary dates are inclusive for both departure and arrival times

### 2. Passenger Identity

- **Check**: Passenger names and employee IDs match between approval and tickets
- **Pass**: All passengers in tickets are in approval list with matching IDs
- **Fail**: Unknown passengers, name mismatches, or ID mismatches

### 3. Route Compliance

- **Check**: Airline usage follows account rules
- **Pass**: SunExpress accounts use SunExpress flights (XQ code)
- **Fail**: SunExpress accounts using other airlines
- **Note**: Non-SunExpress accounts can use any airline

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Model Selection

- **GPT-4o** (default, recommended for complex reasoning)
- Available models can be selected in the sidebar

### Progress Tracking

The system provides real-time progress updates during compliance audits:

- Progress bar showing completion percentage
- Current check being performed
- Detailed status messages

## 📈 Example Results

### Compliant Scenario

```
✅ PASSED: All compliance rules satisfied

✅ Flight Ticket Timing: All flights fall within approved travel period
✅ Passenger Identity: All passenger identities match approval
✅ Route Compliance: All routes follow airline compliance rules
```

### Non-Compliant Scenario

```
❌ VIOLATION: 2 critical violations found

❌ Flight Ticket Timing: Found 1 timing violations
  • Flight XQ141: Departure too early (outside approved period)
✅ Passenger Identity: All passenger identities match approval
❌ Route Compliance: Found 1 route compliance violations
  • Flight TK123: SunExpress account using Turkish Airlines instead of SunExpress
```

### System Error Scenario

```
⚠️ SYSTEM ERROR: 1 system errors occurred

⚠️ Flight Ticket Timing: Unable to complete compliance check due to technical issues
✅ Passenger Identity: All passenger identities match approval
✅ Route Compliance: All routes follow airline compliance rules
```

## 🎯 Key Features

- **Real-time Progress**: Live progress tracking during compliance audits
- **AI-Powered Analysis**: Intelligent compliance checking with GPT-4
- **Detailed Reporting**: Comprehensive violation details with recommendations
- **Sample Data**: Built-in test scenarios with load/reset functionality
- **Error Handling**: Robust error handling with graceful degradation
- **Session Persistence**: Audit results persist until reset
- **Responsive UI**: Modern interface with expandable violation details

## 🚧 System Requirements & Assumptions

1. **Data Format**: JSON input following provided schema structure
2. **Date Formats**: ISO 8601 datetime strings (YYYY-MM-DDTHH:MM:SS)
3. **Airline Codes**: Standard IATA airline codes (e.g., XQ for SunExpress)
4. **Employee IDs**: Unique string identifiers
5. **API Key**: Valid OpenAI API key with GPT-4 access
6. **Network**: Internet connection for OpenAI API calls

## 🔮 Future Improvements

### Short Term

- [ ] Additional compliance rules (budget, class restrictions)
- [ ] Export reports to PDF/Excel
- [ ] Batch processing for multiple bookings
- [ ] Email notifications for violations

### Long Term

- [ ] Integration with travel booking APIs
- [ ] Machine learning for pattern detection
- [ ] Role-based access control
- [ ] Historical compliance trending
- [ ] Multi-language support

### Technical Enhancements

- [ ] Async processing for large datasets
- [ ] Caching for repeated validations
- [ ] Custom rule configuration UI
- [ ] Webhook integration
- [ ] REST API endpoints
- [ ] Database integration for audit history

## 🛠️ Development

### Adding New Compliance Rules

The system supports easy rule extension through the `rules.py` module:

```python
# Example: Adding a new rule type
BUDGET_COMPLIANCE_RULES = [
    "Flight costs must not exceed approved budget limits",
    "Currency conversion rates must be current",
]

def get_budget_compliance_prompt(travel_approval, flight_reservations):
    # Generate prompt for budget checking
    pass

# Register new rule type
add_new_rule_type(
    rule_key="budget_compliance",
    config=BUDGET_RULE_CONFIG,
    rules=BUDGET_COMPLIANCE_RULES,
    prompt_function=get_budget_compliance_prompt
)
```

### File Structure

```
travel-compliance-agent/
├── app.py                 # Main Streamlit application
├── agents.py              # ComplianceAgent implementation
├── rules.py               # Centralized compliance rules
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_compliance.py
└── sample_data/           # Sample JSON files
    ├── TravelApproval.json
    └── Ticket.json
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support & Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your OpenAI API key is valid and has GPT-4 access
2. **JSON Parse Errors**: Verify your JSON format matches the expected schema
3. **System Errors**: Check your internet connection and API key permissions

### Getting Help

- Check the sample data format in `sample_data/` directory
- Review the compliance rule implementations in `agents.py`
- Run the test suite to verify system functionality
- Try the live demo to see expected behavior

## 📋 Development Notes

- **Testing**: Comprehensive test coverage with positive/negative scenarios
- **Error Handling**: Multi-layered error handling with graceful degradation
- **Performance**: Optimized for real-time compliance checking
- **Extensibility**: Modular design for easy rule additions
- **Logging**: Comprehensive logging to terminal for debugging
- **Session Management**: Streamlit session state for data persistence
