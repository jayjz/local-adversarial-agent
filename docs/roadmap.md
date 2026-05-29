# Roadmap - Local Adversarial Arena

## Vision
Build the premier local-first platform for adversarial AI simulation, enabling security researchers, students, and practitioners to study attacker/defender dynamics with fully private, customizable agents.

---

## Phase 1: MVP ✅ (Current - Week 1-2)

**Goal**: Functional PoC that runs end-to-end with Ollama

### Core Features
- [x] Basic network simulator (4 hosts, simple vulnerabilities)
- [x] Red team agent with creative prompting
- [x] Blue team agent with detection/response
- [x] Orchestrator for round management
- [x] LangGraph workflow with state management
- [x] CLI interface for running simulations
- [x] Streamlit dashboard for visualization
- [x] JSON export for session data
- [x] Basic test coverage

### Technical Debt
- [ ] Add proper error handling for Ollama connection failures
- [ ] Implement retry logic for LLM calls
- [ ] Add input validation for all tool parameters
- [ ] Improve type hints coverage to 100%

### Known Limitations
- Simulator is in-memory only (no persistence between runs)
- No authentication/authorization (local use only)
- Limited to 4 pre-defined hosts
- Agents don't learn across sessions
- No support for custom network topologies via config

---

## Phase 2: Dataset Integration (Week 3-4)

**Goal**: Make this useful for Georgie's annotation workflow

### Annotation Features
- [ ] CSV export format compatible with annotation tools
- [ ] Automatic labeling heuristics (e.g., "creative" if uses novel technique)
- [ ] Human annotation UI in Streamlit (thumbs up/down, tags, notes)
- [ ] Session replay functionality
- [ ] Export to Notion database integration
- [ ] Tag system for categorizing rounds (technique, effectiveness, creativity)

### Data Quality
- [ ] Add confidence scores to all agent decisions
- [ ] Track "interestingness" metrics (novelty, effectiveness, stealth)
- [ ] Implement dataset versioning
- [ ] Add data validation for exports
- [ ] Create example datasets for testing

### Integration Points
- [ ] Notion API integration for "Calculus Retake Practice Tracker" style database
- [ ] Google Sheets export option
- [ ] Webhook support for real-time annotation workflows
- [ ] Compatibility with Label Studio or other annotation platforms

---

## Phase 3: Advanced Simulation (Week 5-8)

**Goal**: More realistic, extensible simulation environment

### Network Simulation
- [ ] Configurable network topologies via YAML/JSON
- [ ] Network segmentation and VLANs
- [ ] Lateral movement simulation
- [ ] Active Directory simulation
- [ ] Cloud infrastructure (AWS/GCP/Azure) simulation
- [ ] IoT device simulation

### Attack Techniques
- [ ] MITRE ATT&CK framework mapping
- [ ] Persistence mechanisms (scheduled tasks, services, etc.)
- [ ] Privilege escalation simulation
- [ ] Data exfiltration simulation
- [ ] Command & control (C2) simulation
- [ ] Living-off-the-land techniques

### Defense Capabilities
- [ ] SIEM integration simulation
- [ ] EDR behavioral detection
- [ ] Honeypot/deception technology
- [ ] Threat hunting workflows
- [ ] Incident response playbooks
- [ ] Forensic artifact collection

### Agent Improvements
- [ ] Memory across sessions (vector DB for past experiences)
- [ ] Learning from previous simulations
- [ ] Ensemble methods (multiple models voting)
- [ ] Fine-tuned models for security tasks
- [ ] Custom tool creation by agents

---

## Phase 4: Multi-Model & Performance (Week 9-12)

**Goal**: Support diverse models and optimize for speed

### Model Support
- [ ] Support for GGUF models via llama.cpp
- [ ] Support for MLX models (Apple Silicon)
- [ ] Model comparison mode (same scenario, different models)
- [ ] Automatic model selection based on task
- [ ] Quantized model support for low-resource environments
- [ ] Model performance benchmarking suite

### Performance
- [ ] Async agent execution (red and blue in parallel where possible)
- [ ] Caching for repeated prompts
- [ ] Streaming responses for better UX
- [ ] Batch processing for multiple simulations
- [ ] Resource usage optimization (RAM, VRAM)
- [ ] Support for model parallelism

### Scalability
- [ ] Distributed simulation (multiple machines)
- [ ] Kubernetes deployment option
- [ ] Horizontal scaling for batch jobs
- [ ] Queue system for simulation requests
- [ ] Results database (PostgreSQL/SQLite)

---

## Phase 5: Advanced Features (Month 4+)

**Goal**: Production-ready features for research and education

### Research Features
- [ ] Experiment tracking (MLflow/Weights & Biases integration)
- [ ] A/B testing framework for prompt variations
- [ ] Statistical analysis of agent performance
- [ ] Reproducibility guarantees (seeds, versioning)
- [ ] Paper-ready visualization exports
- [ ] Integration with academic datasets

### Education Features
- [ ] Tutorial mode with guided scenarios
- [ ] Difficulty levels (beginner → expert)
- [ ] Interactive learning modules
- [ ] Certification/assessment mode
- [ ] Classroom management features
- [ ] LMS integration (Canvas, Moodle, etc.)

### Enterprise Features
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Compliance reporting (SOC2, etc.)
- [ ] SSO integration
- [ ] On-premise deployment guide
- [ ] Air-gapped environment support

---

## Long-Term Vision (6+ Months)

### Community & Ecosystem
- [ ] Plugin system for custom agents/tools
- [ ] Marketplace for community scenarios
- [ ] Leaderboards for agent performance
- [ ] Open dataset of simulation traces
- [ ] Annual competition (like CTF but for agents)
- [ ] Integration with real security tools (with safeguards)

### Advanced AI
- [ ] Multi-agent debate for decision making
- [ ] Adversarial training (agents improve by playing each other)
- [ ] Meta-learning (agents learn how to learn)
- [ ] Explainable AI for security decisions
- [ ] Causal reasoning about attack chains
- [ ] Integration with formal verification methods

### Real-World Connection
- [ ] Safe integration with test ranges (like Cyber Range)
- [ ] Import real network topologies (with anonymization)
- [ ] Replay real incidents (from sanitized reports)
- [ ] Generate Sigma rules from simulations
- [ ] Create detection engineering content
- [ ] Bug bounty integration (find vulnerabilities in simulation, test in real world)

---

## Non-Goals

Explicitly NOT building:
- ❌ Actual exploitation tools (this is simulation only)
- ❌ Cloud-based SaaS (staying local-first)
- ❌ Real-time APT simulation (too complex for now)
- ❌ Autonomous hacking of real systems (ethical boundaries)
- ❌ Replacement for human red teamers (augmentation, not replacement)

---

## Success Metrics

### Phase 1 (MVP)
- [ ] Runs without errors on fresh install
- [ ] Completes 10-round simulation in <5 minutes
- [ ] Exports valid JSON that can be re-imported
- [ ] At least 3 people (other than Georgie) successfully run it

### Phase 2 (Dataset)
- [ ] 100+ annotated rounds in dataset
- [ ] Export format works with at least 2 annotation tools
- [ ] Human can annotate a round in <30 seconds
- [ ] Dataset used to train/improve at least one model

### Phase 3 (Advanced Sim)
- [ ] Supports 10+ different host types
- [ ] Implements 20+ ATT&CK techniques
- [ ] Simulation runs 50 rounds without crashing
- [ ] Used in at least one educational setting

### Long Term
- [ ] 100+ GitHub stars
- [ ] 10+ external contributors
- [ ] Cited in at least 1 academic paper or blog post
- [ ] Used by at least 3 organizations for training

---

## Contributing

Want to help build this? Priority areas:

1. **Prompt Engineering**: Better creative prompts for red team
2. **Simulation Realism**: More accurate network/service behavior
3. **UI/UX**: Make Streamlit interface more intuitive
4. **Documentation**: Tutorials, examples, best practices
5. **Testing**: Increase coverage, add integration tests
6. **Performance**: Profile and optimize slow paths

See CONTRIBUTING.md for details (to be created).

---

## Questions & Decisions

### Open Questions
- Should we support non-Ollama models? (Probably yes, but maintain local-first)
- How to handle model versioning for reproducibility?
- What's the right balance between realism and simplicity?
- Should agents have "personalities" or be purely task-focused?

### Key Decisions Made
- ✅ LangGraph over manual orchestration (stateful workflows are complex)
- ✅ Streamlit over Gradio (better for dashboards, more control)
- ✅ Ollama as primary backend (local-first, easy to set up)
- ✅ Pure Python simulation (no external dependencies, easy to understand)
- ✅ JSON for exports initially (simple, human-readable, widely supported)

### Decisions Pending
- ⏳ Database choice for Phase 3 (SQLite vs PostgreSQL)
- ⏳ Vector DB for agent memory (Chroma vs FAISS vs Qdrant)
- ⏳ License for datasets (CC0 vs CC-BY vs custom)
- ⏳ Whether to add web UI beyond Streamlit (React frontend?)

---

**Last Updated**: 2026-05-29
**Current Phase**: Phase 1 - MVP Complete
**Next Milestone**: Phase 2 - Dataset Integration
