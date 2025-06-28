# ✈️ Travel Compliance Agent

An AI-powered automation solution for auditing travel booking compliance using OpenAI's Responses API and Streamlit.

## 🎯 Project Overview

This system automatically audits travel bookings against three key compliance rules:

1. **Flight Ticket Timing** - Ensures departure and arrival times fall within approved travel periods
2. **Passenger Identity** - Validates passenger name consistency between approvals and reservations
3. **Route Compliance** - Checks airline usage rules (e.g., SunExpress accounts using non-SunExpress airlines)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Custom Agents  │    │ OpenAI Responses│
│   - Data Input  │───▶│  (Native)       │───▶│ API             │
│   - Results     │    │  - Compliance   │    │   - GPT-4       │
│   - Chat        │    │  - Chat         │    │   - Direct API  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  Pydantic       │
                       │  Models         │
                       │  - Validation   │
                       │  - Type Safety  │
                       └─────────────────┘
```

## 🚀 Tech Stack

- **Backend**: Python 3.8+
- **AI Framework**: OpenAI Responses API (Direct Integration)
- **UI**: Streamlit
- **Data Validation**: Pydantic
- **Testing**: Pytest
- **Environment**: python-dotenv

### Why This Stack?

- **OpenAI Responses API**: Direct integration with state management and built-in tools
- **Streamlit**: Rapid prototyping with beautiful, interactive UI
- **Pydantic**: Type-safe data validation and parsing
- **Native Python**: Lightweight implementation without framework overhead

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
2. **Load Data**: Either paste JSON data or use sample data
3. **Schema Validation**: Validate your data structure
4. **Run Audit**: Execute compliance checking
5. **Review Results**: See detailed compliance report
6. **Ask Questions**: Use chat interface for clarifications

### Sample Data

The system comes with sample data that demonstrates both compliant and non-compliant scenarios:

```json
{
  "data": {
    "travelCity": "Frankfurt",
    "travelCountry": "Germany",
    "travelBeginDate": "2025-06-22T09:00:00",
    "travelEndDate": "2025-06-26T09:00:00",
    "travelReason": "Business",
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

## 📊 Compliance Rules Details

### 1. Flight Ticket Timing

- **Check**: Departure and arrival times within travel approval period
- **Pass**: All flight times fall within `travelBeginDate` to `travelEndDate`
- **Fail**: Any flight outside approved time window

### 2. Passenger Identity

- **Check**: Passenger names and employee IDs match between approval and tickets
- **Pass**: All passengers in tickets are in approval list with matching IDs
- **Fail**: Unknown passengers or ID mismatches

### 3. Route Compliance

- **Check**: Airline usage follows account rules
- **Pass**: SunExpress accounts use SunExpress flights (XQ)
- **Fail**: SunExpress accounts using other airlines

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Model Selection

- GPT-4 (recommended for complex reasoning)
- GPT-3.5-turbo (faster, cost-effective)

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
❌ FAILED: 2 critical violations found

❌ Flight Ticket Timing: Found 1 timing violations
✅ Passenger Identity: All passenger identities match approval
❌ Route Compliance: Found 1 route compliance violations
```

## 🎯 Key Features

- **Real-time Validation**: Instant schema and data validation
- **AI-Powered Analysis**: Intelligent compliance checking
- **Interactive Chat**: Ask questions about results
- **Detailed Reporting**: Comprehensive violation details
- **Analytics Dashboard**: Visual compliance metrics
- **Sample Data**: Built-in test scenarios

## 🚧 Design Assumptions

1. **Data Format**: JSON input following provided schema structure
2. **Date Formats**: ISO 8601 datetime strings
3. **Airline Codes**: Standard IATA airline codes
4. **Employee IDs**: Unique string identifiers
5. **SunExpress Rule**: XQ code represents SunExpress flights

## 🔮 Future Improvements

### Short Term

- [ ] Additional compliance rules (budget, class restrictions)
- [ ] Email notifications for violations
- [ ] Export reports to PDF/Excel
- [ ] Batch processing for multiple bookings

### Long Term

- [ ] Integration with travel booking APIs
- [ ] Machine learning for pattern detection
- [ ] Role-based access control
- [ ] Historical compliance trending
- [ ] Multi-language support

### Technical Enhancements

- [ ] Async processing for large datasets
- [ ] Caching for repeated validations
- [ ] Custom rule configuration
- [ ] Webhook integration
- [ ] REST API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:

1. Check the test scenarios in `tests/`
2. Review the compliance rule implementations in `src/agents.py`
3. Use the chat feature for specific compliance questions

## 📋 Development Notes

- **Testing**: Comprehensive test coverage with positive/negative scenarios
- **Error Handling**: Graceful handling of malformed data
- **Performance**: Optimized for real-time compliance checking
- **Extensibility**: Modular design for easy rule additions
