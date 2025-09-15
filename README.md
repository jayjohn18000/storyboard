# Legal Simulation Platform

A comprehensive platform for creating deterministic, court-admissible legal visualizations and storyboards.

## Architecture Overview

This platform consists of several key components:

- **Microservices Architecture**: Core services for evidence processing, storyboard creation, timeline compilation, and rendering
- **Dual Mode Operation**: Sandbox mode for experimentation and Demonstrative mode for court-admissible content
- **Deterministic Rendering**: Ensures reproducible outputs for legal proceedings
- **Evidence Chain of Custody**: Complete provenance tracking and WORM storage
- **Policy-Driven Validation**: OPA-based rules for admissibility and compliance

## Quick Start (MVP)

```bash
# Clone and setup
git clone <repository>
cd legal-sim

# Run MVP setup
make setup-mvp

# Start services
docker-compose up -d

# Access dashboard
open http://localhost:3000
```

## Development

```bash
# Install dependencies
make install-deps

# Run tests
make test

# Start development environment
make dev
```

## Key Features

- **Evidence Processing**: OCR, ASR, NLP with multiple implementation options
- **Storyboard Creation**: Visual timeline editor with evidence anchoring
- **3D Scene Generation**: OpenUSD-based scene graphs
- **Render Pipeline**: Blender integration with deterministic outputs
- **Compliance**: Built-in admissibility validation and audit trails

## Legal Compliance

This platform is designed with legal admissibility in mind:
- Deterministic rendering ensures reproducibility
- Complete audit trails for evidence handling
- Policy-driven validation for jurisdiction-specific rules
- WORM storage for evidence preservation

## License

See LICENSE file for details.
