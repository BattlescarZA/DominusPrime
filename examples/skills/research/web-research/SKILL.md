---
name: web-research
description: Systematic approach to conducting effective web research using browser automation, search strategies, and information validation
platforms: [linux, macos, windows]
required_tools: [browser_use, execute_shell_command]
tags: [research, web, browser, information-gathering]
author: DominusPrime
version: 1.0.0
---

# Web Research Skill

## Overview

This skill provides a structured methodology for conducting effective web research using browser automation and search strategies.

## When to Use

- Need to gather information from online sources
- Researching technical topics or documentation
- Fact-checking and validation
- Competitive analysis
- Market research
- Academic research

## Prerequisites

- Browser automation tools available (Playwright/Chromium)
- Internet connection
- Basic understanding of search operators

## Research Process

### 1. Define Research Goals

Before starting, clarify:
- What specific information do you need?
- What format should the results be in?
- What are the time constraints?
- What sources are most reliable?

### 2. Choose Search Strategy

**Broad Exploration:**
- Use general search engines (Google, Bing, DuckDuckGo)
- Start with broad keywords
- Explore multiple result pages

**Targeted Search:**
- Use specific search operators
- Target specific websites or domains
- Use advanced search features

### 3. Search Operators

**Google Search Operators:**

```
site:example.com python debugging
  → Search only on example.com

"exact phrase"
  → Match exact phrase

filetype:pdf machine learning
  → Find specific file types

intitle:debugging python
  → Search in page titles

inurl:docs api
  → Search in URLs

related:example.com
  → Find similar websites

cache:example.com
  → View cached version

before:2024-01-01 news
  → Results before date

after:2024-01-01
  → Results after date

python OR javascript
  → Either term

python -javascript
  → Exclude term
```

### 4. Navigate and Extract Information

Use browser automation for:
- Taking screenshots of important pages
- Extracting text content
- Following links systematically
- Interacting with dynamic content

```python
# Example using browser_use tool
result = await browser_use(
    task="Navigate to Python documentation and extract debugging section",
    url="https://docs.python.org"
)
```

### 5. Validate Information

**Source Credibility Checklist:**
- [ ] Is the source authoritative?
- [ ] Is the information current?
- [ ] Is the author identifiable?
- [ ] Are references provided?
- [ ] Can the information be corroborated?

**Red Flags:**
- No author or date
- Extreme bias or emotional language
- Lack of citations
- Outdated information
- Suspicious domain names

### 6. Organize Findings

**Structure your research:**
1. Create summary document
2. Categorize by topic
3. Note sources and URLs
4. Highlight key findings
5. Identify gaps in knowledge

### 7. Synthesize and Report

**Create research deliverable:**
- Executive summary
- Detailed findings
- Source citations
- Recommendations
- Areas for further research

## Research Techniques

### Academic Research

**Resources:**
- Google Scholar: https://scholar.google.com
- PubMed: https://pubmed.ncbi.nlm.nih.gov
- arXiv: https://arxiv.org
- IEEE Xplore: https://ieeexplore.ieee.org

**Tips:**
- Use citation tracking (who cited this paper?)
- Check author credentials
- Look for peer-reviewed sources
- Note publication dates

### Technical Documentation

**Best Sources:**
- Official documentation sites
- GitHub repositories and README files
- Stack Overflow (verified answers)
- Technical blogs from credible authors

**Search Strategy:**
```
site:github.com python debugging tutorial
site:stackoverflow.com [python] debugging pdb
site:docs.python.org debugging
```

### Competitive Analysis

**Information to Gather:**
- Product features
- Pricing models
- Customer reviews
- Market positioning
- Technology stack

**Tools:**
- Company websites
- Product hunt
- G2 reviews
- Crunchbase
- LinkedIn

### News and Current Events

**Reliable News Sources:**
- Major news organizations
- Reuters, AP (wire services)
- Specialized industry publications
- Official announcements

**Verification:**
- Cross-reference multiple sources
- Check publication dates
- Look for original sources
- Be wary of aggregators

## Browser Automation Examples

### Basic Navigation

```python
# Navigate and screenshot
await browser_use(
    task="Go to example.com and take a screenshot",
    url="https://example.com"
)
```

### Data Extraction

```python
# Extract specific information
await browser_use(
    task="Find the pricing table on example.com/pricing and extract all plan details"
)
```

### Multi-step Research

```python
# Complex research task
await browser_use(
    task="Search for 'Python debugging best practices', open top 3 results, and summarize key points from each"
)
```

## Research Workflow Templates

### Quick Fact Check

1. Search for claim with quotes: `"exact claim to verify"`
2. Check multiple independent sources
3. Look for original source
4. Note date of information
5. Report findings with confidence level

### Deep Technical Research

1. Search official documentation
2. Check GitHub repos and issues
3. Read technical blog posts
4. Review Stack Overflow discussions
5. Test examples if possible
6. Compile comprehensive guide

### Market Research

1. Identify competitors
2. Visit each website
3. Document features and pricing
4. Read reviews and testimonials
5. Analyze positioning
6. Create comparison matrix

## Best Practices

1. **Keep Track of Sources**: Always note URLs and dates accessed
2. **Use Multiple Sources**: Don't rely on single source
3. **Save Important Pages**: Screenshot or save HTML for reference
4. **Respect Robots.txt**: Don't scrape sites that prohibit it
5. **Mind Copyright**: Attribute sources appropriately
6. **Stay Focused**: Avoid rabbit holes
7. **Time-box Research**: Set limits to prevent endless searching
8. **Document As You Go**: Don't wait until the end

## Common Pitfalls

- **Confirmation Bias**: Seeking only supporting evidence
- **First Result Bias**: Assuming top results are best
- **Recency Bias**: Preferring newer over more accurate
- **Source Confusion**: Mixing opinion with fact
- **Scope Creep**: Researching tangential topics

## Tool Integration

```python
# Comprehensive research workflow
async def research_topic(topic: str):
    # 1. Browser research
    results = await browser_use(
        task=f"Search for '{topic}' and summarize top 5 results"
    )
    
    # 2. Save findings
    await write_file(
        path=f"research/{topic}.md",
        content=results
    )
    
    # 3. Follow up searches
    await browser_use(
        task=f"Search site:github.com {topic} and find relevant repositories"
    )
    
    return "Research complete"
```

## References

See the `references/` directory for:
- `search-operators-cheatsheet.md`: Complete list of search operators
- `reliable-sources.md`: Curated list of credible sources by topic
- `research-templates.md`: Templates for different research types

## Related Skills

- `fact-checking`: Verifying claims and information
- `data-analysis`: Analyzing collected data
- `report-writing`: Creating research reports
