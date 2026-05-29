# Local Adversarial Arena

A local-first, privacy-preserving Red Team vs Blue Team agentic AI simulation for cybersecurity learning and creative adversarial thinking.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [Ollama](https://ollama.ai), and [Streamlit](https://streamlit.io) — 100% local, no cloud APIs required.

## 🎯 What Is This?

Local Adversarial Arena is an educational PoC where two AI agents battle it out in a simulated network:

- **🔴 Red Team**: Creative attacker that thinks like a human adversary (storytelling, misdirection, novel vectors)
- **🔵 Blue Team**: Defender that detects, responds, and patches vulnerabilities
- **👁️ Orchestrator**: Referee that manages turns, judges outcomes, and enables human intervention

Perfect for:
- Cybersecurity students learning attacker/defender mindsets
- AI researchers studying adversarial agent behavior
- Red teamers prototyping creative attack chains
- Building local datasets for annotation workflows

## ✨ Key Features

- **100% Local**: Runs entirely on Ollama — no API keys, no data leaves your machine
- **Creative Red Teaming**: Novel prompts for human-like attack creativity (storytelling, thriller twists, unconventional thinking)
- **Human-in-the-Loop**: Inject ideas mid-simulation, annotate rounds, export datasets
- **Lightweight Simulator**: Pure Python network sim (3-5 hosts, no heavy dependencies)
- **Live Dashboard**: Streamlit UI with real-time logs, scores, and controls
- **Extensible**: Clean LangGraph architecture, easy to add new tools/hosts/vulnerabilities

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/download) installed and running

### 1. Install Ollama Models

```bash
# Pull recommended models (or use your own)
ollama pull llama3.2:latest
ollama pull llama3.2:3b  # Faster alternative

# Verify Ollama is running
ollama list
```

### 2. Clone and Install

```bash
git clone https://github.com/yourusername/local-adversarial-arena.git
cd local-adversarial-arena

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Simulation

**CLI Mode:**
```bash
python -m src.main --rounds 10 --red-model llama3.2:latest --blue-model llama3.2:latest
```

**Interactive UI:**
```bash
streamlit run src/ui/streamlit_app.py
```

Then open http://localhost:8501

## 📁 Project Structure

```
local-adversarial-arena/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration and model settings
│   ├── env/                 # Simulated network environment
│   │   ├── simulator.py     # Core simulation engine
│   │   └── models.py        # State schemas and data models
│   ├── agents/              # LangChain agents
│   │   ├── red_team.py      # Creative attacker
│   │   ├── blue_team.py     # Defender
│   │   ├── orchestrator.py  # Turn manager and judge
│   │   └── tools.py         # Shared tools for agents
│   ├── graph/               # LangGraph workflow
│   │   └── workflow.py      # Stateful graph with conditional edges
│   ├── utils/
│   │   ├── prompts.py       # Creative prompting templates
│   │   └── logger.py        # Structured logging
│   └── ui/
│       └── streamlit_app.py # Interactive dashboard
├── tests/                   # Unit tests
├── docs/                    # Additional documentation
└── .github/workflows/       # CI/CD
```

## 🎮 How It Works

### Simulation Loop (Max 15 Rounds)

1. **Red Team Turn**: Analyzes network state, chooses creative attack
   - Tools: `scan_network`, `exploit_service`, `establish_persistence`
   - Prompted for novel, human-like approaches

2. **Blue Team Turn**: Responds to threats
   - Tools: `detect_anomaly`, `patch_vulnerability`, `analyze_logs`
   - Learns from previous rounds

3. **Orchestrator**: Evaluates outcome, updates state
   - Tracks compromised hosts, alerts, patches
   - Checks win conditions
   - Enables human annotation

### Example Network Topology

```
Web Server (192.168.1.10)
├── HTTP:80 (Apache 2.4 - CVE-2021-41773)
├── SSH:22 (weak creds: admin/admin123)
└── Status: Healthy

Database (192.168.1.20)
├── MySQL:3306 (root:password)
├── SSH:22
└── Status: Healthy

Workstation (192.168.1.30)
├── SMB:445
├── RDP:3389
└── Status: Healthy
```

## 🎨 Creative Red Teaming

The Red Team isn't just running Metasploit commands — it's prompted to think like a human:

**Example Prompts:**
- "You're writing a heist movie. The vault is a web server. How do you get in without triggering alarms?"
- "Explain this attack as a thriller plot twist that the blue team won't see coming"
- "What would a bored intern with too much access try at 3 AM?"

See `src/utils/prompts.py` for full template library.

## 📊 Human Annotation Workflow

During simulation, you can:

1. **Inject Ideas**: "Try a supply chain attack on the update server"
2. **Label Actions**: Mark moves as `creative`, `effective`, `noisy`, `failed`
3. **Export Dataset**: Save rounds as JSON/CSV for training data

```bash
# Export annotated session
python -m src.main --export data/session_2026-05-29.json
```

Output format:
```json
{
  "rounds": [
    {
      "round": 1,
      "red_action": "scan_network",
      "red_reasoning": "Mapping attack surface like a burglar casing a house...",
      "blue_action": "detect_anomaly",
      "outcome": "blue_detected",
      "human_labels": ["creative", "effective"],
      "human_notes": "Good use of slow scan to avoid detection"
    }
  ]
}
```

## ⚙️ Configuration

Edit `src/config.py` or use environment variables:

```python
# Model selection
RED_TEAM_MODEL = "llama3.2:latest"    # Creative attacker
BLUE_TEAM_MODEL = "llama3.2:latest"   # Methodical defender
ORCHESTRATOR_MODEL = "llama3.2:3b"    # Fast judge

# Simulation settings
MAX_ROUNDS = 15
ENABLE_HUMAN_INTERVENTION = True

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 120
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Lint code
ruff check src/
ruff format src/
```

## 🗺️ Roadmap

**MVP (Current)**
- ✅ Basic Red/Blue agents with Ollama
- ✅ Simple network simulator (3 hosts)
- ✅ LangGraph workflow with 10-round limit
- ✅ Streamlit dashboard
- ✅ JSON export for annotations

**Phase 2: Dataset Integration**
- 📋 CSV export compatible with annotation tools
- 📋 Notion API integration for tracking
- 📋 Automatic labeling heuristics
- 📋 Session replay functionality

**Phase 3: Advanced Simulation**
- 🔮 More hosts and vulnerability types
- 🔮 Network segmentation and lateral movement
- 🔮 Persistence mechanisms
- 🔮 Deception techniques (honeypots)

**Phase 4: Multi-Model Support**
- 🔮 Support for local GGUF models via llama.cpp
- 🔮 Model comparison mode (same scenario, different models)
- 🔮 Fine-tuning pipeline for specialized agents

See `docs/roadmap.md` for detailed planning.

## 🔒 Privacy & Safety

- **No Real Networks**: Simulation is entirely in-memory Python objects
- **No Dangerous Tools**: No actual exploit code, just simulated actions
- **Local Only**: Ollama runs on localhost, no data exfiltration
- **Educational Purpose**: Designed for learning, not actual attacks

## 🐛 Troubleshooting

**Ollama not running:**
```bash
# Start Ollama service
ollama serve

# In another terminal, test it
ollama run llama3.2:latest "Hello"
```

**Model not found:**
```bash
ollama pull llama3.2:latest
```

**Streamlit port in use:**
```bash
streamlit run src/ui/streamlit_app.py --server.port 8502
```

**Import errors:**
```bash
# Ensure you're in the project root and venv is activated
pip install -e .
```

## 🤝 Contributing

This is a PoC built for learning. Contributions welcome:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-idea`)
3. Make your changes with tests
4. Run linting: `ruff check src/ && ruff format src/`
5. Submit a PR

Areas needing help:
- More creative prompt templates
- Additional vulnerability types
- Better visualization in UI
- Performance optimizations

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for stateful agent workflows
- [Ollama](https://ollama.ai) for local LLM inference
- Inspired by MITRE ATT&CK framework and real red team operations

## 📬 Contact

Questions? Ideas? Find me on GitHub or open an issue.

---

**Disclaimer**: This tool is for educational purposes only. The simulated attacks are fictional and designed to teach defensive concepts. Do not use these techniques on systems you don't own or have explicit permission to test.
