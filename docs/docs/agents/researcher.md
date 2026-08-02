---
sidebar_position: 12
---

# Researcher Agent

The Researcher Agent conducts web research on specified topics and provides comprehensive summaries of findings, supporting the writing process with accurate information.

## Overview

This agent performs targeted research to gather information, verify facts, and provide context for your book's content. It combines AI-generated summaries with web scraping capabilities to deliver comprehensive research results.

## Features

### Research Capabilities
- Web content analysis
- Search result processing
- Content summarization
- Source verification
- Data compilation

### Data Collection
- Web scraping
- Search optimization
- Content filtering
- Source ranking
- Result aggregation

### Output Generation
- Detailed summaries
- Source citations
- Key findings
- Relevant quotes
- Research context

## Research Process

1. **Query Processing**
   - Analyze research needs
   - Optimize search terms
   - Define scope
   - Identify key areas

2. **Data Collection**
   - Web scraping
   - Content gathering
   - Source verification
   - Information filtering

3. **Analysis & Synthesis**
   - Content summarization
   - Data organization
   - Finding compilation
   - Report generation

## Output Format

Research results are provided in Markdown format:

```markdown
# Research Report: [Topic]

## AI-Generated Summary
[Comprehensive overview of findings]

## Web Search Results
### [Source Title]
- URL: [Source URL]
- Key Points:
  - [Relevant information]
  - [Supporting details]

### [Additional Sources...]
```

## Usage

```bash
# Through Project Manager
libriscribe research "research query"

# Direct usage
researcher.execute(query, output_path)
```

## Best Practices

1. **Query Optimization**
   - Use specific terms
   - Define scope clearly
   - Include context
   - Specify requirements

2. **Source Management**
   - Verify reliability
   - Track citations
   - Document sources
   - Rate credibility

3. **Content Processing**
   - Filter relevance
   - Organize findings
   - Summarize effectively
   - Maintain context

## Integration

Works with:
- Fact Checker for verification
- Content Reviewer for context
- Editor Agent for integration
- Project Manager for coordination

## Error Handling

Manages:
- Failed searches
- Invalid sources
- Processing errors
- Connection issues

## Configuration

Customizable for:
- Search depth
- Source requirements
- Result filtering
- Output format

## Security & Ethics

- Respects robots.txt
- Implements rate limiting
- Follows scraping ethics
- Maintains attribution

## Downstream Usage in Chapter Writing

The `research_results.md` file produced by this agent is automatically read by the **Chapter Writer Agent** when generating each scene. The first 1 200 characters are injected as a `RESEARCH CONTEXT` block in the scene prompt, providing the LLM with factual grounding from your research.

Run the Researcher before or during chapter writing for best results:

```bash
libriscribe research "your research topic here"
```

The research file persists across sessions — re-run to update it with new findings. See [Chapter Writer Agent](chapter-writer.md) for details on how it is used.