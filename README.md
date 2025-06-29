# ✈️ Travel Compliance Agent

> **Version 0.3**

An AI-agent powered automation solution for auditing travel booking compliance.

## 🌐 Live Demo

**Try it now:** [https://travel-compliance-agent-dzk3dyc3ecappn5vr4hsxpo.streamlit.app/](https://travel-compliance-agent-dzk3dyc3ecappn5vr4hsxpo.streamlit.app/)

_Note: You'll need your own OpenAI API key to use the live demo._

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
