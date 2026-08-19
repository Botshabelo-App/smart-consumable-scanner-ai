# Architecture Diagrams

This folder contains the final architecture package for the Smart Consumable Scanner AI. Each diagram is provided in three formats:

- **`.mmd`** — editable Mermaid source.
- **`.svg`** — scalable vector for web/documentation.
- **`.png`** — raster for presentations and printed documents.
- **`.pdf`** — PDF for formal reports.

## Diagrams

| Diagram | Source | SVG | PNG | PDF | Description |
|---------|--------|-----|-----|-----|-------------|
| System architecture | [system_architecture.mmd](system_architecture.mmd) | [svg](system_architecture.svg) | [png](system_architecture.png) | [pdf](system_architecture.pdf) | End-to-end components: mobile, backend, AI service, data stores, and external APIs. |
| Database ER | [database_er.mmd](database_er.mmd) | [svg](database_er.svg) | [png](database_er.png) | [pdf](database_er.pdf) | SQLAlchemy entities and relationships for RC1. |
| Scan sequence | [scan_sequence.mmd](scan_sequence.mmd) | [svg](scan_sequence.svg) | [png](scan_sequence.png) | [pdf](scan_sequence.pdf) | Typical inspection flow from capture to report generation. |
| AI inference workflow | [ai_inference_workflow.mmd](ai_inference_workflow.mmd) | [svg](ai_inference_workflow.svg) | [png](ai_inference_workflow.png) | [pdf](ai_inference_workflow.pdf) | YOLO detection, classification, spoilage/packaging analysis, explainability. |
| Mobile architecture | [mobile_architecture.mmd](mobile_architecture.mmd) | [svg](mobile_architecture.svg) | [png](mobile_architecture.png) | [pdf](mobile_architecture.pdf) | React Native + Expo layers and native modules. |
| Backend architecture | [backend_architecture.mmd](backend_architecture.mmd) | [svg](backend_architecture.svg) | [png](backend_architecture.png) | [pdf](backend_architecture.pdf) | FastAPI routers, services, and persistence. |
| Deployment architecture | [deployment_architecture.mmd](deployment_architecture.mmd) | [svg](deployment_architecture.svg) | [png](deployment_architecture.png) | [pdf](deployment_architecture.pdf) | Kubernetes, Nginx, managed PostgreSQL/S3, EAS, CI/CD. |
| Security architecture | [security_architecture.mmd](security_architecture.mmd) | [svg](security_architecture.svg) | [png](security_architecture.png) | [pdf](security_architecture.pdf) | Identity, access control, transport, data protection, and validation. |

## Rendering

Install Mermaid CLI and regenerate all exports:

```bash
cd docs/diagrams
for f in *.mmd; do
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.svg"
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.png" -w 1920 -H 1080
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.pdf"
done
```

PNG and PDF outputs were generated at a 1920x1080 viewport with a white background.
