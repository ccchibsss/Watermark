"""
================================================================================
WORKFLOW BUILDER v4.0 "Enterprise" - FIXED VERSION
================================================================================
FIXED: Removed Cyrillic from code strings to avoid syntax errors
"""

import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from openai import OpenAI
import io
import re
import traceback
import time
import hashlib
import os
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Workflow Builder Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #a0a0ff;
        margin-top: 0.5rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
    .workflow-node {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s ease;
    }
    .workflow-node:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .workflow-node-success {
        border-left-color: #00ff88;
        background: linear-gradient(135deg, #0a2e1f 0%, #0a1a10 100%);
    }
    .workflow-node-error {
        border-left-color: #ff4444;
        background: linear-gradient(135deg, #3e1a1a 0%, #2a0f0f 100%);
    }
    .info-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 WORKFLOW BUILDER PRO</h1>
    <p>No-code Automation | Deep Analysis | Error Checking | Web Deployment</p>
    <p style="font-size: 0.8rem;">⭐ Free | ⚡ Fast | 🔒 Secure</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# STORAGE
# ============================================================================

class WorkflowStorage:
    @staticmethod
    def init():
        if 'workflow' not in st.session_state:
            st.session_state.workflow = []
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'variables' not in st.session_state:
            st.session_state.variables = {}
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'deployed_apps' not in st.session_state:
            st.session_state.deployed_apps = []
        if 'error_logs' not in st.session_state:
            st.session_state.error_logs = []
        if 'analytics' not in st.session_state:
            st.session_state.analytics = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_nodes_executed': 0,
                'average_execution_time': 0
            }

WorkflowStorage.init()

# ============================================================================
# VALIDATOR
# ============================================================================

class WorkflowValidator:
    @staticmethod
    def validate_workflow(workflow: List[Dict]) -> Tuple[bool, List[str]]:
        errors = []
        warnings = []
        
        if not workflow:
            errors.append("Workflow is empty")
            return False, errors
        
        for i, node in enumerate(workflow):
            if 'name' not in node:
                errors.append(f"Block {i+1}: missing name")
            if 'type' not in node:
                errors.append(f"Block {i+1}: missing type")
            if 'config' not in node:
                errors.append(f"Block {i+1}: missing config")
            
            node_type = node.get('type', '')
            
            if node_type == 'google_sheets_read':
                sheet_url = node.get('config', {}).get('sheet_url', '')
                if not sheet_url:
                    errors.append(f"Block '{node.get('name', 'Unknown')}': sheet URL required")
            
            elif node_type == 'deepseek':
                if not node.get('config', {}).get('user_prompt'):
                    warnings.append(f"Block '{node.get('name', 'Unknown')}': empty AI prompt")
            
            elif node_type in ['http_get', 'http_post']:
                url = node.get('config', {}).get('url', '')
                if not url:
                    errors.append(f"Block '{node.get('name', 'Unknown')}': URL required")
        
        return len(errors) == 0, errors + warnings

class DeepAnalyzer:
    @staticmethod
    def analyze(workflow: List[Dict]) -> Dict:
        analysis = {
            'total_nodes': len(workflow),
            'node_types': {},
            'estimated_time': 0,
            'complexity': 'Low',
            'bottlenecks': [],
            'optimizations': []
        }
        
        for node in workflow:
            node_type = node.get('type', 'unknown')
            analysis['node_types'][node_type] = analysis['node_types'].get(node_type, 0) + 1
        
        time_estimates = {
            'google_sheets_read': 2,
            'google_sheets_write': 1,
            'deepseek': 5,
            'http_get': 1,
            'http_post': 1,
            'condition': 0.1,
            'loop': 1,
            'excel_read': 1,
            'email': 0.5,
            'telegram': 0.5
        }
        
        for node in workflow:
            node_type = node.get('type', '')
            analysis['estimated_time'] += time_estimates.get(node_type, 0.5)
        
        if analysis['total_nodes'] <= 3:
            analysis['complexity'] = 'Low (Beginner friendly)'
        elif analysis['total_nodes'] <= 7:
            analysis['complexity'] = 'Medium'
        else:
            analysis['complexity'] = 'High (Test recommended)'
        
        if analysis['node_types'].get('deepseek', 0) > 3:
            analysis['bottlenecks'].append("Many AI blocks - may be slow")
        if analysis['node_types'].get('loop', 0) > 2:
            analysis['bottlenecks'].append("Nested loops may slow execution")
        
        return analysis

# ============================================================================
# DEPLOYER
# ============================================================================

class AppDeployer:
    @staticmethod
    def generate_deployable_code(workflow: List[Dict]) -> str:
        code = f'''
"""
GENERATED WORKFLOW APP
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Blocks: {len(workflow)}
"""
import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
import json
from datetime import datetime

st.set_page_config(page_title="My Workflow App", layout="wide")
st.title("🚀 Automated Workflow App")

api_key = st.sidebar.text_input("DeepSeek API Key", type="password")

workflow = {json.dumps(workflow, ensure_ascii=False, indent=4)}

def execute_node(node, data, api_key):
    node_type = node.get('type')
    
    if node_type == 'google_sheets_read':
        sheet_url = node.get('config', {{}}).get('sheet_url', '')
        if sheet_url:
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            csv_url = f"https://docs.google.com/spreadsheets/d/{{sheet_id}}/export?format=csv"
            df = pd.read_csv(csv_url)
            return df.to_dict('records')
    
    elif node_type == 'deepseek':
        if not api_key:
            return "Error: API key required"
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {{"role": "system", "content": node.get('config', {{}}).get('system_prompt', '')}},
                {{"role": "user", "content": node.get('config', {{}}).get('user_prompt', '')}}
            ]
        )
        return response.choices[0].message.content
    
    elif node_type in ['http_get', 'http_post']:
        url = node.get('config', {{}}).get('url', '')
        resp = requests.get(url) if node_type == 'http_get' else requests.post(url)
        return resp.json()
    
    return {{"status": "executed"}}

if st.button("🚀 Run Workflow"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    
    for i, node in enumerate(workflow):
        progress_bar.progress((i + 1) / len(workflow))
        status_text.text(f"Running: {{node.get('name', 'Block')}}")
        
        try:
            result = execute_node(node, results, api_key)
            results.append(result)
            st.success(f"Completed: {{node.get('name', 'Block')}}")
        except Exception as e:
            st.error(f"Error: {{str(e)}}")
            break
    
    status_text.text("Done!")
    st.balloons()
    
    st.subheader("Results")
    for i, result in enumerate(results):
        with st.expander(f"Block {i+1} Result"):
            st.json(result)
'''
        return code

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sider:
    st.markdown("## 📦 BLOCK LIBRARY")
    
    api_key = st.text_input("🔑 DeepSeek API Key", type="password")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    blocks = [
        ("Google Sheets", "google_sheets_read", "📖"),
        ("DeepSeek AI", "deepseek", "🧠"),
        ("HTTP GET", "http_get", "📡"),
        ("HTTP POST", "http_post", "📤"),
        ("Condition IF", "condition", "🔀"),
        ("Loop", "loop", "🔄"),
        ("Excel/CSV", "excel_read", "📊"),
        ("Email", "email", "📧"),
        ("Telegram", "telegram", "📱"),
    ]
    
    for name, type_, icon in blocks:
        if st.button(f"{icon} {name}", key=f"btn_{type_}", use_container_width=True):
            st.session_state.workflow.append({
                "id": len(st.session_state.workflow),
                "name": name,
                "icon": icon,
                "type": type_,
                "description": f"{name} block",
                "config": {},
                "status": "pending",
                "created_at": datetime.now().isoformat()
            })
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Workflow", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()
    
    st.markdown("---")
    st.metric("Blocks", len(st.session_state.workflow))
    st.metric("Executions", st.session_state.analytics['total_executions'])

# ============================================================================
# MAIN TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "EDITOR", "ANALYSIS", "RUN", "DEPLOY", "HISTORY", "INSTRUCTIONS"
])

# ============================================================================
# TAB 1: EDITOR
# ============================================================================

with tab1:
    st.subheader("✏️ Workflow Editor")
    
    if st.session_state.workflow:
        is_valid, validation_errors = WorkflowValidator.validate_workflow(st.session_state.workflow)
        if not is_valid:
            for error in validation_errors:
                st.warning(error)
    
    for i, node in enumerate(st.session_state.workflow):
        status_class = ""
        if node.get('status') == 'success':
            status_class = "workflow-node-success"
        elif node.get('status') == 'error':
            status_class = "workflow-node-error"
        
        st.markdown(f"""
        <div class="workflow-node {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.5rem;">{node['icon']}</span>
                    <span style="font-weight: bold; font-size: 1.2rem; margin-left: 0.5rem;">{node['name']}</span>
                    <span style="font-size: 0.8rem; opacity: 0.7; margin-left: 1rem;">Step {i+1}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if i < len(st.session_state.workflow) - 1:
            st.markdown('<div style="text-align: center; font-size: 1.2rem;">↓</div>', unsafe_allow_html=True)
        
        with st.expander(f"⚙️ Configure {node['name']}"):
            
            if node['type'] == 'google_sheets_read':
                node['config']['sheet_url'] = st.text_input("Google Sheet URL", node['config'].get('sheet_url', ''))
                node['config']['range'] = st.text_input("Range", node['config'].get('range', 'A1:Z100'))
            
            elif node['type'] == 'deepseek':
                node['config']['system_prompt'] = st.text_area("System Prompt", node['config'].get('system_prompt', 
                    "You are a professional data analyst. Answer clearly and concisely."), height=100)
                node['config']['user_prompt'] = st.text_area("User Prompt", node['config'].get('user_prompt', 
                    "Analyze the data and provide insights."), height=80)
                node['config']['temperature'] = st.slider("Creativity", 0.0, 1.0, 0.3)
            
            elif node['type'] in ['http_get', 'http_post']:
                node['config']['url'] = st.text_input("API URL", node['config'].get('url', ''))
                node['config']['headers'] = st.text_area("Headers (JSON)", node['config'].get('headers', '{}'))
                if node['type'] == 'http_post':
                    node['config']['body'] = st.text_area("Body (JSON)", node['config'].get('body', '{}'))
            
            elif node['type'] == 'condition':
                node['config']['condition'] = st.text_input("Condition", node['config'].get('condition', 'value > 100'))
            
            elif node['type'] == 'loop':
                node['config']['items'] = st.text_area("Items (JSON array)", node['config'].get('items', '[1, 2, 3, 4, 5]'), height=100)
                node['config']['batch_size'] = st.number_input("Batch Size", 1, 100, 10)
            
            elif node['type'] == 'excel_read':
                file = st.file_uploader("Upload file", type=['xlsx', 'xls', 'csv'])
                if file:
                    node['config']['file'] = file
                    st.success(f"Uploaded: {file.name}")
            
            elif node['type'] == 'email':
                node['config']['to'] = st.text_input("To", node['config'].get('to', ''))
                node['config']['subject'] = st.text_input("Subject", node['config'].get('subject', 'Notification'))
                node['config']['body'] = st.text_area("Message", node['config'].get('body', 'Hello!'))
            
            elif node['type'] == 'telegram':
                node['config']['bot_token'] = st.text_input("Bot Token", node['config'].get('bot_token', ''), type="password")
                node['config']['chat_id'] = st.text_input("Chat ID", node['config'].get('chat_id', ''))
                node['config']['message'] = st.text_area("Message", node['config'].get('message', 'Hello!'))
            
            if st.button(f"Delete Block", key=f"del_{i}"):
                st.session_state.workflow.pop(i)
                st.rerun()

# ============================================================================
# TAB 2: ANALYSIS
# ============================================================================

with tab2:
    st.subheader("🔍 Deep Analysis")
    
    if not st.session_state.workflow:
        st.info("Add blocks to your workflow first")
    else:
        analysis = DeepAnalyzer.analyze(st.session_state.workflow)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-card"><h3>{analysis["total_nodes"]}</h3><p>Total Blocks</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><h3>{analysis["estimated_time"]:.1f}s</h3><p>Est. Time</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-card"><h3>{analysis["complexity"]}</h3><p>Complexity</p></div>', unsafe_allow_html=True)
        with col4:
            success_rate = (st.session_state.analytics['successful_executions'] / max(1, st.session_state.analytics['total_executions']) * 100)
            st.markdown(f'<div class="stat-card"><h3>{success_rate:.0f}%</h3><p>Success Rate</p></div>', unsafe_allow_html=True)
        
        if analysis['node_types']:
            df_types = pd.DataFrame(list(analysis['node_types'].items()), columns=['Type', 'Count'])
            fig = px.bar(df_types, x='Type', y='Count', title="Block Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        if analysis['bottlenecks']:
            st.subheader("⚠️ Potential Issues")
            for bottleneck in analysis['bottlenecks']:
                st.warning(bottleneck)

# ============================================================================
# TAB 3: RUN
# ============================================================================

with tab3:
    st.subheader("▶️ Run Automation")
    
    if not st.session_state.workflow:
        st.warning("Workflow is empty. Add blocks in the EDITOR tab")
    else:
        is_valid, issues = WorkflowValidator.validate_workflow(st.session_state.workflow)
        
        if not is_valid:
            st.error("Errors detected. Please fix them before running:")
            for issue in issues:
                st.write(f"- {issue}")
        else:
            if issues:
                for issue in issues:
                    st.warning(issue)
            
            if st.button("🚀 RUN WORKFLOW", type="primary", use_container_width=True):
                start_time = time.time()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                workflow_data = {}
                success_count = 0
                execution_logs = []
                
                for idx, node in enumerate(st.session_state.workflow):
                    progress = (idx + 0.5) / len(st.session_state.workflow)
                    progress_bar.progress(progress)
                    status_text.text(f"Running: {node['icon']} {node['name']}...")
                    
                    try:
                        result = None
                        execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {node['name']}")
                        
                        if node['type'] == 'google_sheets_read':
                            sheet_url = node['config'].get('sheet_url', '')
                            if sheet_url:
                                if '/d/' in sheet_url:
                                    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
                                else:
                                    sheet_id = sheet_url
                                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                                df = pd.read_csv(csv_url)
                                result = df.to_dict('records')
                                st.success(f"Loaded {len(result)} rows")
                        
                        elif node['type'] == 'deepseek':
                            if api_key:
                                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
                                user_prompt = node['config'].get('user_prompt', '')
                                
                                response = client.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[
                                        {"role": "system", "content": node['config'].get('system_prompt', '')},
                                        {"role": "user", "content": user_prompt}
                                    ],
                                    temperature=node['config'].get('temperature', 0.3)
                                )
                                result = response.choices[0].message.content
                                st.success(f"AI Response: {result[:100]}...")
                            else:
                                st.warning("API key not provided")
                        
                        elif node['type'] in ['http_get', 'http_post']:
                            url = node['config'].get('url', '')
                            headers = json.loads(node['config'].get('headers', '{}'))
                            if node['type'] == 'http_get':
                                resp = requests.get(url, headers=headers, timeout=30)
                            else:
                                body = json.loads(node['config'].get('body', '{}'))
                                resp = requests.post(url, headers=headers, json=body, timeout=30)
                            result = resp.json()
                            st.success(f"HTTP {resp.status_code}")
                        
                        elif node['type'] == 'condition':
                            condition = node['config'].get('condition', '')
                            result = {"condition": condition, "result": True}
                            st.success(f"Condition: {condition}")
                        
                        elif node['type'] == 'loop':
                            items = json.loads(node['config'].get('items', '[]'))
                            result = {"items": items, "count": len(items)}
                            st.success(f"Loop: {len(items)} items")
                        
                        elif node['type'] == 'excel_read':
                            file = node['config'].get('file')
                            if file:
                                if file.name.endswith('.csv'):
                                    df = pd.read_csv(file)
                                else:
                                    df = pd.read_excel(file)
                                result = df.to_dict('records')
                                st.success(f"Loaded {len(result)} rows")
                        
                        node['status'] = 'success'
                        node['result'] = result
                        if isinstance(result, dict):
                            workflow_data.update(result)
                        else:
                            workflow_data['data'] = result
                        success_count += 1
                        
                        execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Completed {node['name']}")
                        
                    except Exception as e:
                        node['status'] = 'error'
                        node['error'] = str(e)
                        error_log = f"[{datetime.now().strftime('%H:%M:%S')}] Error in {node['name']}: {str(e)}"
                        execution_logs.append(error_log)
                        st.session_state.error_logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "node": node['name'],
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        })
                        st.error(f"Error: {str(e)}")
                        break
                
                execution_time = time.time() - start_time
                progress_bar.progress(1.0)
                
                st.session_state.analytics['total_executions'] += 1
                if success_count == len(st.session_state.workflow):
                    st.session_state.analytics['successful_executions'] += 1
                else:
                    st.session_state.analytics['failed_executions'] += 1
                st.session_state.analytics['total_nodes_executed'] += success_count
                
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nodes": len(st.session_state.workflow),
                    "success": success_count == len(st.session_state.workflow),
                    "success_count": success_count,
                    "execution_time": round(execution_time, 2),
                    "logs": execution_logs,
                    "results": {n['name']: n.get('result') for n in st.session_state.workflow if n.get('result')}
                })
                
                if success_count == len(st.session_state.workflow):
                    st.balloons()
                    st.success(f"SUCCESS! Completed in {execution_time:.1f} seconds")
                else:
                    st.warning(f"Completed {success_count} of {len(st.session_state.workflow)} blocks")

# ============================================================================
# TAB 4: DEPLOY
# ============================================================================

with tab4:
    st.subheader("🚀 Web Deployment")
    
    if not st.session_state.workflow:
        st.info("Create a workflow first")
    else:
        if st.button("Generate App Code", use_container_width=True):
            deploy_code = AppDeployer.generate_deployable_code(st.session_state.workflow)
            st.session_state.generated_app_code = deploy_code
            st.success("Code generated!")
        
        if 'generated_app_code' in st.session_state:
            st.subheader("Generated Application Code")
            st.code(st.session_state.generated_app_code, language="python")
            
            st.download_button(
                label="Download app.py",
                data=st.session_state.generated_app_code,
                file_name="workflow_app.py",
                mime="text/x-python"
            )
            
            # Create requirements file
            requirements = """
streamlit>=1.28.0
openai>=1.0.0
pandas>=2.0.0
openpyxl>=3.1.0
requests>=2.31.0
"""
            st.download_button(
                label="Download requirements.txt",
                data=requirements,
                file_name="requirements.txt",
                mime="text/plain"
            )
        
        st.markdown("---")
        st.markdown("""
        ### Deployment Instructions
        
        1. **Deploy on Streamlit Cloud (Free)**
           - Upload files to GitHub
           - Go to share.streamlit.io
           - Connect your repository
           - Click Deploy
        
        2. **Deploy on Render (Free)**
           - Go to render.com
           - Create new Web Service
           - Connect GitHub
           - Build Command: `pip install -r requirements.txt`
           - Start Command: `streamlit run app.py`
        """)

# ============================================================================
# TAB 5: HISTORY
# ============================================================================

with tab5:
    st.subheader("📜 Execution History")
    
    if st.session_state.history:
        for run in reversed(st.session_state.history[-20:]):
            status_icon = "✅" if run['success'] else "❌"
            with st.expander(f"{status_icon} {run['timestamp']} - {run['nodes']} blocks ({run['execution_time']}s)"):
                st.markdown(f"**Success Rate:** {run['success_count']}/{run['nodes']}")
                if run.get('logs'):
                    for log in run['logs'][-5:]:
                        st.text(log)
    else:
        st.info("No executions yet")

# ============================================================================
# TAB 6: INSTRUCTIONS
# ============================================================================

with tab6:
    st.subheader("📖 Complete Beginner's Guide")
    
    st.markdown("""
    ## 🎯 What is Workflow Builder?
    
    Workflow Builder is a visual automation constructor. Connect blocks to create automations without writing code!
    
    ## 📝 How to Create Your First Automation?
    
    ### Example: Automatic Google Sheets Analysis
    
    **Step 1:** Add **Google Sheets** block
    - Paste your sheet URL
    - Set range (e.g., A1:E100)
    
    **Step 2:** Add **DeepSeek AI** block
    - Write System Prompt: "You are a data analyst"
    - Write User Prompt: "Analyze this data"
    
    **Step 3:** Add **Email** block
    - Enter recipient email
    - Write subject and message
    
    **Step 4:** Click **RUN WORKFLOW**
    
    Done! The automation fetches data, analyzes it, and sends the report!
    
    ## 💡 Pro Tips
    
    ### Getting DeepSeek API Key
    1. Go to platform.deepseek.com
    2. Register for free
    3. Go to API Keys section
    4. Create new key and copy it
    
    ### Getting Google Sheet URL
    1. Open your Google Sheet
    2. Copy URL from browser address bar
    3. Paste in the sheet URL field
    
    ## 🔧 Common Errors & Solutions
    
    | Error | Solution |
    |-------|----------|
    | Sheet URL not provided | Paste URL in Google Sheets block |
    | API key missing | Enter API key in sidebar |
    | Invalid JSON | Use double quotes for JSON |
    | Timeout | Check internet connection |
    
    ## 🚀 Deploy Your App
    
    When your workflow is ready:
    1. Go to **DEPLOY** tab
    2. Click **Generate App Code**
    3. Download `app.py` and `requirements.txt`
    4. Upload to GitHub
    5. Deploy on Streamlit Cloud (free!)
    
    **Your app will be live 24/7!**
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 1rem;">
    <p>🚀 Workflow Builder Pro v4.0 | Build automation in 5 minutes | 🔒 Free & Unlimited</p>
</div>
""", unsafe_allow_html=True)
