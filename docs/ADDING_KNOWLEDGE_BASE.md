# Adding to the Knowledge Base

The knowledge base powers RAG recommendations. Add markdown files with medical guidelines.

1. Create a markdown file in `data/knowledge_base/<category>/`
2. Structure with clear headers (`##`, `###`) and reference ranges
3. Include source attribution at the bottom
4. Run: `make ingest-rag`

## File Format

```markdown
# Guideline Title

## Biomarker Name
- Normal: < X units
- Abnormal: > Y units

## Recommendations
- Evidence-based recommendation 1
- Evidence-based recommendation 2

*Source: Organization Name, Year*
```
