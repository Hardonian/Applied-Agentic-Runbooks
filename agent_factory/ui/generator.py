"""
Generate UI from agent schemas - Complete implementation with React templates.
"""

from pathlib import Path
from typing import Any

from agent_factory.agents.agent import Agent
from agent_factory.ui.schema_inference import infer_ui_schema


def generate_ui(
    agent_id: str,
    output_dir: str,
    template: str = "react",
) -> None:
    """
    Generate UI for an agent.

    Args:
        agent_id: Agent ID
        output_dir: Output directory
        template: Template type ("react" or "html")

    Returns:
        None (writes files to output_dir)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load agent from registry
    from agent_factory.registry.local_registry import LocalRegistry

    registry = LocalRegistry()
    agent = registry.get_agent(agent_id)

    if not agent:
        raise ValueError(f"Agent not found: {agent_id}")

    schema = infer_ui_schema(agent)

    if template == "html":
        _generate_html_ui(output_path, agent, schema)
    elif template == "react":
        _generate_react_ui(output_path, agent, schema)
    else:
        raise ValueError(f"Unsupported template: {template}")


def _generate_html_ui(output_path: Path, agent: Agent, schema: dict[str, Any]) -> None:
    """Generate simple HTML UI."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agent.name} - Agent Interface</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin-top: 0;
            color: #333;
        }}
        .input-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
        }}
        input[type="text"], textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }}
        textarea {{
            min-height: 100px;
            resize: vertical;
        }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        button:hover {{
            background: #0056b3;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        #output {{
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            min-height: 50px;
            white-space: pre-wrap;
        }}
        .loading {{
            display: none;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{agent.name}</h1>
        <form id="agent-form">
            <div class="input-group">
                <label for="input">Your Message:</label>
                <textarea id="input" name="input" placeholder="Enter your message here..." required></textarea>
            </div>
            <button type="submit" id="submit-btn">Send</button>
            <div class="loading" id="loading">Processing...</div>
        </form>
        <div id="output"></div>
    </div>
    <script>
        const form = document.getElementById('agent-form');
        const input = document.getElementById('input');
        const output = document.getElementById('output');
        const submitBtn = document.getElementById('submit-btn');
        const loading = document.getElementById('loading');
        
        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const inputText = input.value.trim();
            if (!inputText) return;
            
            submitBtn.disabled = true;
            loading.style.display = 'block';
            output.textContent = '';
            
            try {{
                const response = await fetch('/api/v1/agents/{agent.id}/run', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        input: inputText
                    }})
                }});
                
                const data = await response.json();
                output.textContent = data.output || data.error || 'No response';
            }} catch (error) {{
                output.textContent = 'Error: ' + error.message;
            }} finally {{
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }}
        }});
    </script>
</body>
</html>
"""
    (output_path / "index.html").write_text(html_content)


def _generate_react_ui(output_path: Path, agent: Agent, schema: dict[str, Any]) -> None:
    """Generate React UI."""
    # Create package.json
    package_json = """{
  "name": "agent-ui",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
"""
    (output_path / "package.json").write_text(package_json)

    # Create public/index.html
    public_dir = output_path / "public"
    public_dir.mkdir(exist_ok=True)

    public_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Agent Interface</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""
    (public_dir / "index.html").write_text(public_html)

    # Create src/App.js
    src_dir = output_path / "src"
    src_dir.mkdir(exist_ok=True)

    app_js = f"""import React, {{ useState }} from 'react';
import './App.css';

function App() {{
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {{
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError(null);
    setOutput('');

    try {{
      const response = await fetch('/api/v1/agents/{agent.id}/run', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
        }},
        body: JSON.stringify({{ input }}),
      }});

      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}

      const data = await response.json();
      setOutput(data.output || data.error || 'No response');
    }} catch (err) {{
      setError(err.message);
      setOutput('Error: ' + err.message);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="App">
      <div className="container">
        <h1>{agent.name}</h1>
        <form onSubmit={{handleSubmit}}>
          <div className="input-group">
            <label htmlFor="input">Your Message:</label>
            <textarea
              id="input"
              value={{input}}
              onChange={{e => setInput(e.target.value)}}
              placeholder="Enter your message here..."
              required
            />
          </div>
          <button type="submit" disabled={{loading}}>
            {{loading ? 'Processing...' : 'Send'}}
          </button>
        </form>
        {{error && <div className="error">{{error}}</div>}}
        {{output && (
          <div className="output">
            <h2>Response:</h2>
            <pre>{{output}}</pre>
          </div>
        )}}
      </div>
    </div>
  );
}}

export default App;
"""
    (src_dir / "App.js").write_text(app_js)

    # Create src/App.css
    app_css = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f5f5;
}

.App {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  max-width: 800px;
  width: 100%;
}

h1 {
  margin-top: 0;
  color: #333;
}

.input-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-height: 100px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #dc3545;
  margin-top: 10px;
  padding: 10px;
  background: #f8d7da;
  border-radius: 4px;
}

.output {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.output h2 {
  margin-top: 0;
  font-size: 18px;
  color: #333;
}

.output pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}
"""
    (src_dir / "App.css").write_text(app_css)

    # Create src/index.js
    index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
    (src_dir / "index.js").write_text(index_js)

    # Create src/index.css
    index_css = """* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}
"""
    (src_dir / "index.css").write_text(index_css)

    # Create README.md
    readme = f"""# {agent.name} UI

React-based UI for {agent.name} agent.

## Setup

```bash
npm install
npm start
```

## Build

```bash
npm run build
```

## Configuration

Update the API endpoint in `src/App.js` if needed.
"""
    (output_path / "README.md").write_text(readme)
