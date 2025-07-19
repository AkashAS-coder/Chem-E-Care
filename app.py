import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import random
from io import BytesIO
import base64
import requests
import os

# --- Event Persistence Utilities ---
EVENTS_FILE = "events.json"

def load_events():
    try:
        with open(EVENTS_FILE, "r") as f:
            events = json.load(f)
            # Convert 'time' field back to datetime
            for e in events:
                if isinstance(e.get('time'), str):
                    e['time'] = datetime.fromisoformat(e['time'])
            return events
    except Exception:
        return []

def save_events(events):
    # Convert datetime to isoformat for JSON serialization
    serializable = []
    for e in events:
        e_copy = e.copy()
        if isinstance(e_copy.get('time'), datetime):
            e_copy['time'] = e_copy['time'].isoformat()
        serializable.append(e_copy)
    with open(EVENTS_FILE, "w") as f:
        json.dump(serializable, f, indent=2)

# --- End Event Persistence Utilities ---

# --- Todo Persistence Utilities ---
TODOS_FILE = "todos.json"

def load_todos():
    try:
        with open(TODOS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_todos(todos):
    with open(TODOS_FILE, "w") as f:
        json.dump(todos, f, indent=2)
# --- End Todo Persistence Utilities ---

# --- AI Todo List Utilities ---
def extract_todos_from_ai(ai_analysis_text):
    """Extract todo/action items from AI analysis text (expects bullet points or numbered list)"""
    todos = []
    for line in ai_analysis_text.splitlines():
        line = line.strip('-•* 1234567890.').strip()
        if line:
            todos.append(line)
    return todos
# --- End AI Todo List Utilities ---

# Page configuration
st.set_page_config(
    page_title="Chem-E-Care",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-critical { background-color: #ffebee; border-left-color: #f44336; }
    .alert-compliance { background-color: #fff3e0; border-left-color: #ff9800; }
    .alert-asset { background-color: #e8f5e8; border-left-color: #4caf50; }
    .alert-rounding { background-color: #f3e5f5; border-left-color: #9c27b0; }
    .alert-training { background-color: #e3f2fd; border-left-color: #2196f3; }
    .event-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .orchestrator-entry {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin-bottom: 0.5rem;
    }
    .ai-status-ready {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    .ai-status-error {
        background-color: #ffebee;
        color: #c62828;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# Gemini API Configuration
def get_gemini_api_key():
    """Get Gemini API key from Streamlit secrets"""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("❌ GEMINI_API_KEY not found in Streamlit secrets. Please add it to your .streamlit/secrets.toml file.")
        return None

def call_gemini_api(prompt, api_key):
    """Call Kimi K2 Instruct via Together.ai API with the given prompt"""
    if not api_key:
        return None

    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "kimi-k2-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "No response generated"
        else:
            return f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Request Error: {str(e)}"

# Initialize session state
if 'events' not in st.session_state:
    st.session_state.events = load_events()
if 'orchestrator_log' not in st.session_state:
    st.session_state.orchestrator_log = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'monthly_reviews' not in st.session_state:
    st.session_state.monthly_reviews = []
if 'todos' not in st.session_state:
    st.session_state.todos = load_todos()

# Sample data
assets = [
    {'id': 1, 'name': 'Turbine #1', 'status': 'Healthy', 'risk': 'Low', 'trend': '+2%'},
    {'id': 2, 'name': 'Pipeline A', 'status': 'At Risk', 'risk': 'Medium', 'trend': '-1%'},
    {'id': 3, 'name': 'Turbine #3', 'status': 'Critical', 'risk': 'High', 'trend': '-5%'}
]

compliance = 92
cost = 1.23
cost_unit = 'M'

training = [
    {'name': 'Alice', 'status': 'Complete', 'expires': '2025-01-10'},
    {'name': 'Bob', 'status': 'Expiring', 'expires': '2024-07-01'},
    {'name': 'Carlos', 'status': 'Expired', 'expires': '2024-04-01'}
]

ai_insights = [
    'Optimize turbine #3 maintenance schedule',
    'Reduce inspection cycle for pipeline A',
    'Update training for new EPA rule',
    'Consolidate vendor onboarding',
    'Review asset tag rounding policy'
]

benefits_info = {
    'Dashboards': 'Legacy: Multiple dashboards in different systems. New: All-in-one view.',
    'Decision Gates': 'Legacy: Many manual gates. New: One AI-powered gate.',
    'Average Alert Routing': 'Legacy: Slow, manual routing. New: Instant, AI-driven.',
    'Report Prep Time': 'Legacy: Manual, slow. New: Automated, fast.',
    'Data Silos': 'Legacy: Data scattered. New: Unified cloud hub.'
}

alert_types = {
    'Critical Safety': {'class': 'alert-critical', 'timing': 0, 'auto': 'Shutdown command issued', 'urgency': 60},
    'Compliance Drift': {'class': 'alert-compliance', 'timing': 3600, 'auto': 'Draft gap report generated', 'urgency': 3600},
    'Asset Failure Risk': {'class': 'alert-asset', 'timing': 900, 'auto': 'Maintenance task scheduled', 'urgency': 900},
    'Rounding': {'class': 'alert-rounding', 'timing': 14400, 'auto': 'Small alert & data adjust', 'urgency': 14400},
    'Training Lapse': {'class': 'alert-training', 'timing': 86400, 'auto': 'Auto-assign micro-course', 'urgency': 86400}
}

# Map AI risk to urgency and style
risk_to_alert = {
    'High':    {'class': 'alert-critical',    'urgency': 60},
    'Medium':  {'class': 'alert-asset',      'urgency': 900},
    'Low':     {'class': 'alert-rounding',   'urgency': 14400},
    'Training':{'class': 'alert-training',   'urgency': 86400},
    'Compliance': {'class': 'alert-compliance', 'urgency': 3600},
}

def time_ago(date):
    """Convert datetime to relative time string"""
    now = datetime.now()
    diff = now - date
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minutes ago"
    else:
        return "Just now"

def format_urgency(alert):
    """Format urgency time for alerts"""
    if alert['urgency'] < 3600:
        return f"{alert['urgency'] // 60}m"
    elif alert['urgency'] < 86400:
        return f"{alert['urgency'] // 3600}h"
    else:
        return f"{alert['urgency'] // 86400}d"

def create_gauge_chart(value, title, color='blue'):
    """Create a gauge chart using plotly"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def create_cost_dial():
    """Create cost vs budget dial"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cost,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Cost vs Budget ({cost_unit})"},
        gauge={
            'axis': {'range': [None, 2]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 1], 'color': "lightgreen"},
                {'range': [1, 1.5], 'color': "yellow"},
                {'range': [1.5, 2], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 1.8
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def add_alert_dynamic(event, risk_level, auto_action=None):
    """Add a new alert with dynamic risk/urgency/class"""
    alert_def = risk_to_alert.get(risk_level, risk_to_alert['Low'])
    alert = {
        'id': time.time() + random.random(),
        'type': risk_level,
        'class': alert_def['class'],
        'auto': auto_action or '',
        'event': event,
        'created': datetime.now(),
        'urgency': alert_def['urgency'],
        'dismissed': False
    }
    st.session_state.alerts.insert(0, alert)

def process_orchestrator_decision(event, answers):
    """Process orchestrator decision and determine outcome"""
    outcome, color, alert_type = None, None, None
    
    if answers[0]:  # Safety impact
        outcome = 'Escalate'
        color = '#ff4d4f'
        alert_type = 'Critical Safety'
    elif answers[1] or answers[2]:  # Compliance deviation or Asset health risk
        outcome = 'Schedule Task'
        color = '#faad14'
        alert_type = 'Asset Failure Risk' if answers[2] else 'Compliance Drift'
    else:
        outcome = 'Auto-Resolve'
        color = '#52c41a'
        alert_type = 'Rounding'
    
    orchestrator_entry = {
        'event': event,
        'answers': answers,
        'outcome': outcome,
        'color': color,
        'timestamp': datetime.now()
    }
    
    st.session_state.orchestrator_log.insert(0, orchestrator_entry)
    event['status'] = outcome
    add_alert_dynamic(event, alert_type) # Changed to add_alert_dynamic
    
    return outcome, color

# Setup Gemini API
api_key = get_gemini_api_key()
st.write("API Key loaded:", bool(api_key), api_key[:6] if api_key else None)

# Sidebar navigation
st.sidebar.title("Chem-E-Care")
page = st.sidebar.selectbox(
    "Navigation",
    ["Home", "Entry Points", "Orchestrator", "Alert Matrix", "Dashboard", "Documentation", "AI Analysis", "Benefits"]
)

# Main content based on selected page
if page == "Home":
    st.markdown('<h1 class="main-header">Chem-E-Care</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("logo.png", width=200)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2>Welcome to Chem-E-Care!</h2>
            <p>Manage your chemical energy facility with unified insights and AI-powered tools.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Started", type="primary"):
            st.switch_page("Entry Points")

elif page == "Entry Points":
    st.title("Unified Entry Points")
    
    # Event form
    with st.form("event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_type = st.selectbox(
                "Type:",
                ["Autonomous Asset Ping", "Scheduled Cycle", "Regulatory Update", "Contractor Event", "Incident Flag"]
            )
        
        with col2:
            event_details = st.text_input("Details:", placeholder="Enter event details")
        
        submitted = st.form_submit_button("Add Event")
        
        if submitted and event_details:
            event = {
                'id': time.time(),
                'type': event_type,
                'details': event_details,
                'time': datetime.now(),
                'status': 'Pending'
            }
            st.session_state.events.insert(0, event)
            save_events(st.session_state.events)
            st.success("Event added successfully!")
            st.rerun()
    
    # Event log
    st.subheader("Recent Events")
    if not st.session_state.events:
        st.info("No events yet.")
    else:
        for event in st.session_state.events[:10]:
            with st.container():
                st.markdown(f"""
                <div class="event-card">
                    <strong>{event['type']}</strong> - {event['details']}<br>
                    <span style="color:#888;font-size:0.9em;">({time_ago(event['time'])})</span><br>
                    <span>Status: {event['status']}</span>
                </div>
                """, unsafe_allow_html=True)

elif page == "Orchestrator":
    st.title("Smart Orchestrator")
    
    # Orchestrator log
    st.subheader("Orchestrator Decisions")
    if not st.session_state.orchestrator_log:
        st.info("No orchestrator decisions yet.")
    else:
        for entry in st.session_state.orchestrator_log[:10]:
            with st.container():
                st.markdown(f"""
                <div class="orchestrator-entry">
                    <strong>{entry['event']['type']}</strong> - {entry['event']['details']}<br>
                    <span>Answers: {', '.join(['Yes' if a else 'No' for a in entry['answers']])}</span><br>
                    <span>Outcome: <span style="color:{entry['color']}">{entry['outcome']}</span></span>
                </div>
                """, unsafe_allow_html=True)

elif page == "Alert Matrix":
    st.title("Alert Matrix")
    
    # Alert list
    if not st.session_state.alerts:
        st.info("No alerts yet.")
    else:
        for alert in st.session_state.alerts:
            if not alert['dismissed']:
                with st.container():
                    st.markdown(f"""
                    <div class="{alert['class']} metric-card">
                        <h4>{alert['type']}</h4>
                        <p><strong>Event:</strong> {alert['event']['type']} - {alert['event']['details']}</p>
                        <p><strong>Auto Action:</strong> {alert['auto']}</p>
                        <p><strong>Urgency:</strong> {format_urgency(alert)}</p>
                        <p><strong>Created:</strong> {time_ago(alert['created'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button(f"Dismiss", key=f"dismiss_{alert['id']}"):
                            alert['dismissed'] = True
                            st.rerun()

elif page == "Dashboard":
    st.title("ONE Dashboard")
    
    # Dashboard panels
    col1, col2 = st.columns(2)
    
    with col1:
        # Asset Map
        st.subheader("Asset Map")
        asset_df = pd.DataFrame(assets)
        st.dataframe(asset_df, use_container_width=True)
        
        # Compliance Gauge
        st.subheader("Compliance Gauge")
        compliance_fig = create_gauge_chart(compliance, "Compliance %", "green")
        st.plotly_chart(compliance_fig, use_container_width=True)
    
    with col2:
        # Cost Dial
        st.subheader("Cost vs Budget")
        cost_fig = create_cost_dial()
        st.plotly_chart(cost_fig, use_container_width=True)
        
        # Training Status
        st.subheader("Training Status")
        training_df = pd.DataFrame(training)
        st.dataframe(training_df, use_container_width=True)
    
    # AI Insights
    st.subheader("AI Insights")
    for insight in ai_insights:
        st.markdown(f"• {insight}")

    # AI-Generated Todo List (interactive)
    st.subheader("AI-Generated Todo List")
    ai_todos = st.session_state.todos
    if api_key and st.session_state.events:
        # Use the same prompt as in AI Analysis, but ask for prioritized action items and risk for each event
        events_text = "\n".join([f"{e['type']}: {e['details']} (Status: {e['status']})" for e in st.session_state.events[:10]])
        todo_prompt = f"""Analyze these chemical facility events and for each event, provide:\n- A risk level (High, Medium, Low)\n- A recommended action item\nFormat as: Event: <event details> | Risk: <risk> | Action: <todo>\n\nRecent Events:\n{events_text}\n"""
        with st.spinner("Generating AI todo list and risk assessment from events..."):
            ai_todo_text = call_gemini_api(todo_prompt, api_key)
            if ai_todo_text:
                # Parse AI response for todos and risk
                new_todos = []
                for line in ai_todo_text.splitlines():
                    if '| Risk:' in line and '| Action:' in line:
                        parts = line.split('|')
                        event_part = parts[0].replace('Event:', '').strip()
                        risk_part = parts[1].replace('Risk:', '').strip()
                        action_part = parts[2].replace('Action:', '').strip()
                        new_todos.append({
                            'event': event_part,
                            'risk': risk_part,
                            'action': action_part,
                            'done': False
                        })
                        # Also create/update alert for this event
                        matching_event = next((e for e in st.session_state.events if event_part in e['details']), None)
                        if matching_event:
                            add_alert_dynamic(matching_event, risk_part, auto_action=action_part)
                if new_todos:
                    st.session_state.todos = new_todos
                    save_todos(new_todos)
                    ai_todos = new_todos
            # else: keep previous todos
    # Display interactive todo list
    if ai_todos:
        for idx, todo in enumerate(ai_todos):
            checked = st.checkbox(f"{todo['action']} (Event: {todo['event']}, Risk: {todo['risk']})", value=todo.get('done', False), key=f"todo_{idx}")
            if checked != todo.get('done', False):
                st.session_state.todos[idx]['done'] = checked
                save_todos(st.session_state.todos)
    else:
        st.info("No AI-generated todos available.")

elif page == "Documentation":
    st.title("Automated Documentation & Reporting")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Inspection Photo:", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.success("Image uploaded successfully!")
    
    # Generate report button
    if st.button("Generate Compliance Report"):
        st.info("Generating compliance report...")
        time.sleep(2)
        st.success("Report generated successfully!")
    
    # Documentation panel
    st.subheader("Documentation Panel")
    st.info("Documentation features will be displayed here.")

elif page == "AI Analysis":
    st.title("AI-Powered Analysis")
    
    # AI Status
    if api_key:
        st.markdown('<div class="ai-status-ready">AI Analysis: Ready (Gemini API from secrets)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ai-status-error">AI Analysis: Not available (Add GEMINI_API_KEY to .streamlit/secrets.toml)</div>', unsafe_allow_html=True)
    
    # AI Analysis Panel
    st.subheader("AI Analysis Tools")
    
    # Auto-generate insights based on events
    if api_key and st.session_state.events:
        st.subheader("🤖 AI-Generated Insights")
        
        # Analyze recent events for patterns and insights
        events_text = "\n".join([f"{e['type']}: {e['details']} (Status: {e['status']})" for e in st.session_state.events[:10]])
        
        analysis_prompt = f"""Analyze these chemical facility events and provide actionable insights:

Recent Events:
{events_text}

Provide a concise analysis with:
1. Key patterns identified
2. Risk assessment
3. Immediate action items
4. Compliance implications
5. Recommended preventive measures

Format as bullet points for easy reading."""
        
        with st.spinner("Generating AI insights from events..."):
            ai_analysis = call_gemini_api(analysis_prompt, api_key)
            if ai_analysis:
                st.markdown("### 📊 Event Analysis")
                st.write(ai_analysis)
            else:
                st.error("Failed to generate AI analysis")
    
    # Manual analysis tools
    st.subheader("Manual Analysis Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Analyze Recent Events", disabled=not api_key):
            if st.session_state.events:
                events_text = "\n".join([f"{e['type']}: {e['details']}" for e in st.session_state.events[:5]])
                prompt = f"""Analyze these recent chemical facility events and provide insights on patterns, risks, and recommendations:

Events:
{events_text}

Please provide a detailed analysis including:
1. Risk assessment
2. Pattern identification
3. Recommended actions
4. Compliance implications"""
                
                with st.spinner("Analyzing events with Gemini AI..."):
                    result = call_gemini_api(prompt, api_key)
                    if result:
                        st.text_area("Analysis Results:", value=result, height=300)
                    else:
                        st.error("Failed to get AI analysis")
            else:
                st.warning("No events to analyze")
    
    with col2:
        if st.button("Generate AI Report", disabled=not api_key):
            # Include events data in the report
            events_summary = ""
            if st.session_state.events:
                events_summary = f"\nRecent Events Summary:\n" + "\n".join([f"- {e['type']}: {e['details']}" for e in st.session_state.events[:5]])
            
            prompt = f"""Generate a comprehensive AI report for a chemical energy facility with the following data:

Compliance Rate: {compliance}%
Cost: ${cost}{cost_unit}
Recent Events: {len(st.session_state.events)} events{events_summary}
Assets: {len(assets)} assets monitored

Please provide:
1. Executive Summary
2. Key Performance Indicators
3. Risk Assessment
4. Recommendations
5. Next Steps"""
            
            with st.spinner("Generating AI report with Gemini..."):
                result = call_gemini_api(prompt, api_key)
                if result:
                    st.text_area("AI Report:", value=result, height=300)
                else:
                    st.error("Failed to generate AI report")
    
    with col3:
        if st.button("Predict Maintenance Needs", disabled=not api_key):
            assets_text = "\n".join([f"{a['name']}: {a['status']} ({a['risk']} risk)" for a in assets])
            prompt = f"""Based on the following asset data, predict maintenance needs and provide recommendations:

Assets:
{assets_text}

Please provide:
1. Maintenance predictions for each asset
2. Priority recommendations
3. Timeline suggestions
4. Cost implications
5. Risk mitigation strategies"""
            
            with st.spinner("Predicting maintenance with Gemini AI..."):
                result = call_gemini_api(prompt, api_key)
                if result:
                    st.text_area("Maintenance Predictions:", value=result, height=300)
                else:
                    st.error("Failed to predict maintenance needs")

elif page == "Benefits":
    st.title("Benefits Comparison")
    
    # Benefits table
    st.subheader("Legacy vs New System Benefits")
    
    benefits_df = pd.DataFrame([
        {"Feature": feature, "Description": description}
        for feature, description in benefits_info.items()
    ])
    
    st.dataframe(benefits_df, use_container_width=True)
    
    # Additional benefits visualization
    st.subheader("Key Benefits Summary")
    
    benefits_data = {
        'Feature': list(benefits_info.keys()),
        'Benefit_Score': [95, 90, 85, 80, 75]  # Example scores
    }
    
    benefits_chart_df = pd.DataFrame(benefits_data)
    fig = px.bar(benefits_chart_df, x='Feature', y='Benefit_Score', 
                 title="Benefit Impact Scores",
                 color='Benefit_Score',
                 color_continuous_scale='viridis')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>&copy; 2025 Chem-E-Care</p>", unsafe_allow_html=True)
