# GCP Digital Twin Agent System

An intelligent agent system leveraging a digital twin of a GCP environment (Neo4j) for proactive monitoring, predictive alerts, and task automation.

## Quick Start

### Prerequisites
- Node.js 16+ (for taskmaster)
- Python 3.9+ (for agent implementation)
- Neo4j 5.x (for digital twin)
- GCP account with API access
- API Keys: Anthropic (Claude) and Perplexity

### Setup

1. **Install Taskmaster** (if not already installed):
   ```bash
   npm install -g task-master-ai
   ```

2. **Configure API Keys**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Generate Project Tasks**:
   ```bash
   task-master parse-prd .taskmaster/docs/prd.txt --num-tasks=12
   task-master analyze-complexity --research
   task-master expand --all --research
   ```

4. **Start Development**:
   ```bash
   task-master next  # Get first task to work on
   ```

## Project Architecture

### Core Components

1. **Digital Twin Environment (Neo4j)**
   - Graph structure: GCP resources as nodes, relationships as edges
   - Real-time synchronization with live GCP environment
   - Historical data storage for RL training
   - "What-if" simulation capability

2. **Agent System**
   - **LLM Engine**: Local Qwen3 model
   - **Training**: Offline RL via OAT algorithm
   - **Multi-Agent Setup**:
     - Assistant/Planner: User interaction orchestration
     - Query Agent: Neo4j information retrieval
     - Executor Agent: Simulation and action execution

3. **Communication Layer**
   - MCP (Multi-Agent Communication Protocol)
   - GCP API integration
   - Natural language user interface

## Implementation Phases

### Phase I: Foundation (Months 1-3)
- ✅ Project initialization and planning
- ✅ Neo4j schema design for GCP resources
- ✅ Data ingestion pipeline (integrated and tested)
- ⏱️ Basic graph visualization

### Phase II: Agent Training (Months 4-6)
- ⏱️ Training environment API (GEM-compliant)
- ⏱️ Historical data collection
- ⏱️ OAT algorithm implementation
- ⏱️ Qwen3 model training

### Phase III: Deployment (Months 7-12)
- ⏱️ Multi-agent framework
- ⏱️ User interface development
- ⏱️ Predictive alerting
- ⏱️ Continuous learning

## Technology Stack

- **Graph Database**: Neo4j 5.x
- **LLM**: Qwen3 (local deployment)
- **RL Framework**: OAT (Offline RL), GEM (environment)
- **Communication**: MCP, A2A protocols
- **Cloud**: Google Cloud Platform
- **Languages**: Python, JavaScript/Node.js
- **Task Management**: Taskmaster AI

## Development Workflow

1. **Check current tasks**: `task-master list`
2. **Get next task**: `task-master next`
3. **View task details**: `task-master show <id>`
4. **Start work**: `task-master set-status --id=<id> --status=in-progress`
5. **Log progress**: `task-master update-subtask --id=<id> --prompt="implementation notes"`
6. **Complete task**: `task-master set-status --id=<id> --status=done`

## Documentation

- **Product Requirements**: `.taskmaster/docs/prd.txt`
- **Implementation Guide**: `.taskmaster/docs/Implementation GCP-RL-LLM-NEO4J.md`
- **RL Theory**: `.taskmaster/docs/LLM Reinforcement Learning in Network Di.md`
- **Training Methods**: `.taskmaster/docs/llm_training.md`
- **Claude Instructions**: `CLAUDE.md`

## Data Ingestion Pipeline

The GCP Digital Twin ingestion pipeline is now fully integrated and operational. It consists of 5 major components:

### Pipeline Components

1. **GCP API Client** (`src/ingestion_pipeline/api_client/`)
   - Service account authentication
   - Rate limiting and retry logic
   - Resource fetching from GCP APIs
   - Pagination support

2. **Event Subscription System** (`src/ingestion_pipeline/event_system/`)
   - Pub/Sub integration for real-time events
   - Asynchronous message processing
   - Callback registry for resource types
   - Health monitoring

3. **Data Transformation Layer** (`src/ingestion_pipeline/transformation/`)
   - Pydantic schemas for validation
   - Resource transformation to Neo4j format
   - Relationship extraction
   - Data integrity validation

4. **Neo4j Batch Operations** (`src/ingestion_pipeline/neo4j_ops/`)
   - Connection pooling
   - Batch write operations
   - MERGE query generation
   - Retry logic and metrics

5. **Monitoring & Logging** (`src/ingestion_pipeline/monitoring/`)
   - Structured logging (structlog)
   - Prometheus metrics collection
   - Health checks for all components
   - Rule-based alerting system

### Pipeline Orchestrator

The `src/ingestion_pipeline/pipeline.py` module integrates all components:

```python
from ingestion_pipeline.pipeline import GCPIngestionPipeline, PipelineConfig

# Create and configure pipeline
pipeline = GCPIngestionPipeline(
    gcp_project_id="your-project",
    gcp_service_account_path="key.json",
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password",
)

# Run pipeline
await pipeline.initialize()
await pipeline.start()
```

### Running the Pipeline

1. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your GCP and Neo4j credentials
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the full pipeline**:
   ```bash
   python examples/full_pipeline_example.py
   ```

4. **Run tests**:
   ```bash
   pytest tests/test_pipeline_integration.py -v
   ```

### Pipeline Features

- **Automatic initialization** of all components in dependency order
- **Event-driven architecture** with Pub/Sub integration
- **Comprehensive monitoring** with metrics, health checks, and alerts
- **Graceful shutdown** with proper resource cleanup
- **Configuration management** via environment variables or code
- **Error handling** with retries and circuit breakers
- **Production-ready** with logging, metrics, and health checks

See `src/ingestion_pipeline/monitoring/README.md` for detailed monitoring documentation.

## Project Structure

```
agent-seomax/
├── .taskmaster/          # Task management
│   ├── tasks/           # Generated task files
│   ├── docs/            # Reference documentation
│   ├── reports/         # Complexity analysis
│   └── config.json      # Configuration
├── .cline/              # Cline rules
│   └── rules/           # Development guidelines
├── src/                 # Source code
│   └── ingestion_pipeline/  # Data ingestion components
│       ├── pipeline.py      # Main orchestrator
│       ├── api_client/      # GCP API integration
│       ├── event_system/    # Pub/Sub event handling
│       ├── transformation/  # Data transformation
│       ├── neo4j_ops/      # Neo4j operations
│       └── monitoring/     # Logging and metrics
├── tests/               # Test suite
│   ├── test_pipeline_integration.py  # Pipeline tests
│   └── test_monitoring_smoke.py      # Monitoring tests
├── examples/            # Usage examples
│   ├── full_pipeline_example.py      # Complete pipeline demo
│   └── neo4j_batch_write_example.py  # Neo4j usage
├── docs/                # Documentation
│   └── neo4j-schema/    # Graph database schema
├── CLAUDE.md           # AI assistant instructions
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── .env.example        # Environment template
```

## Key Concepts

### Network Digital Twin (NDT)
A virtual representation that accurately mirrors the real-time state, configuration, and behavior of your GCP environment, enabling:
- Risk-free testing and simulation
- Historical analysis for RL training
- Predictive modeling
- Impact assessment before changes

### Offline Reinforcement Learning
Training methodology where:
- Agent learns from historical data
- No live environment interaction during training
- OAT algorithm optimizes Qwen3 model parameters
- Experience sampling from digital twin history

### Multi-Agent Orchestration
Specialized agents working together:
- Natural language user interface
- Graph query optimization
- Safe test execution
- Coordinated decision-making

## Contributing

This project follows taskmaster-driven development. All tasks are tracked in `.taskmaster/tasks/`.

## License

[Add your license here]

## Contact

[Add contact information]
