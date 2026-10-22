"""
Research Assistant App - Full Example Application

A complete FastAPI application demonstrating Agent Factory integration.
"""

import os
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="Research Assistant App",
    description="AI-powered research assistant built with Agent Factory",
    version="1.0.0"
)

# Mount static files (for auto-generated UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Request/Response Models
class ResearchRequest(BaseModel):
    query: str
    max_results: int | None = 5
    include_citations: bool = True


class ResearchResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    summary: str
    citations: list[str] | None = None
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# In-memory storage (use database in production)
research_history: list[ResearchResponse] = []


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the auto-generated UI."""
    ui_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Research Assistant App</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            header h1 { font-size: 2.5em; margin-bottom: 10px; }
            header p { opacity: 0.9; }
            .content {
                padding: 40px;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
            }
            input[type="text"], textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus, textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                min-height: 120px;
                resize: vertical;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .results {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                display: none;
            }
            .results.show {
                display: block;
            }
            .result-item {
                background: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .result-item h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .summary {
                background: #e8f4f8;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }
            .summary h3 {
                color: #333;
                margin-bottom: 10px;
            }
            .loading {
                text-align: center;
                padding: 20px;
                display: none;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .error {
                background: #fee;
                color: #c33;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                display: none;
            }
            .error.show {
                display: block;
            }
            footer {
                text-align: center;
                padding: 20px;
                color: #666;
                border-top: 1px solid #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔬 Research Assistant</h1>
                <p>AI-powered research assistant built with Agent Factory</p>
            </header>
            <div class="content">
                <form id="researchForm">
                    <div class="form-group">
                        <label for="query">Research Query</label>
                        <textarea id="query" name="query" placeholder="Enter your research question..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="maxResults">Max Results</label>
                        <input type="text" id="maxResults" name="maxResults" value="5" />
                    </div>
                    <button type="submit">🔍 Research</button>
                </form>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Researching...</p>
                </div>
                
                <div class="error" id="error"></div>
                
                <div class="results" id="results">
                    <h2>Research Results</h2>
                    <div id="resultsContent"></div>
                </div>
            </div>
            <footer>
                <p>Powered by Agent Factory Platform | <a href="/docs">API Docs</a> | <a href="/health">Health</a></p>
            </footer>
        </div>
        
        <script>
            document.getElementById('researchForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const query = document.getElementById('query').value;
                const maxResults = parseInt(document.getElementById('maxResults').value) || 5;
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                const error = document.getElementById('error');
                const resultsContent = document.getElementById('resultsContent');
                
                loading.classList.add('show');
                results.classList.remove('show');
                error.classList.remove('show');
                
                try {
                    const response = await fetch('/api/v1/research', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, max_results: maxResults })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Research failed');
                    }
                    
                    const data = await response.json();
                    
                    let html = '';
                    if (data.results && data.results.length > 0) {
                        data.results.forEach((result, idx) => {
                            html += `
                                <div class="result-item">
                                    <h3>Result ${idx + 1}</h3>
                                    <p>${result.content || result.title || JSON.stringify(result)}</p>
                                </div>
                            `;
                        });
                    }
                    
                    if (data.summary) {
                        html += `
                            <div class="summary">
                                <h3>Summary</h3>
                                <p>${data.summary}</p>
                            </div>
                        `;
                    }
                    
                    resultsContent.innerHTML = html;
                    results.classList.add('show');
                } catch (err) {
                    error.textContent = 'Error: ' + err.message;
                    error.classList.add('show');
                } finally {
                    loading.classList.remove('show');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=ui_html)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Perform research using Agent Factory."""
    try:
        # Import Agent Factory components
        from agent_factory.agents.agent import Agent
        from agent_factory.integrations.tools.web_search import WebSearchTool
        
        # Create research agent
        agent = Agent(
            id="research-assistant",
            name="Research Assistant",
            instructions="""You are a research assistant. Analyze the query and provide:
1. A comprehensive summary
2. Key findings
3. Relevant citations if available
Be thorough and cite sources when possible.""",
            tools=[WebSearchTool()] if hasattr(__import__('agent_factory.integrations.tools.web_search', fromlist=['WebSearchTool']), 'WebSearchTool') else []
        )
        
        # Run research
        result = agent.run(request.query)
        
        # Format response
        response = ResearchResponse(
            query=request.query,
            results=[
                {"content": result.output if hasattr(result, 'output') else str(result), "rank": i+1}
                for i in range(min(request.max_results, 1))
            ],
            summary=result.output if hasattr(result, 'output') else str(result),
            citations=[],
            timestamp=datetime.now().isoformat()
        )
        
        # Store in history
        research_history.append(response)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.get("/api/v1/history", response_model=list[ResearchResponse])
async def get_history():
    """Get research history."""
    return research_history[-10:]  # Return last 10


@app.get("/docs")
async def docs():
    """Redirect to API documentation."""
    return {"message": "API documentation available at /docs (FastAPI auto-generated)"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
