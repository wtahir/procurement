# Agents

Each agent owns one narrow responsibility and either:

- reasons over ambiguous inputs with an LLM, or
- calls deterministic tools and writes validated state.

No agent should combine both financial arithmetic and free-form reasoning in the same code path.
