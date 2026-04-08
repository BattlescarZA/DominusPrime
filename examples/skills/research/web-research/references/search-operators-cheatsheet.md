# Search Operators Cheatsheet

## Google Search Operators

### Basic Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `"exact match"` | `"python debugging"` | Search for exact phrase |
| `OR` | `python OR javascript` | Either term (must be uppercase) |
| `-exclude` | `python -java` | Exclude term from results |
| `*` | `python * debugging` | Wildcard placeholder |
| `()` | `(python OR javascript) tutorial` | Group terms |

### Site and Domain

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:stackoverflow.com python` | Search specific site |
| `site:.gov` | `site:.gov climate` | Search domain type |
| `related:` | `related:github.com` | Find similar sites |
| `-site:` | `python -site:w3schools.com` | Exclude specific site |

### Content Type

| Operator | Example | Description |
|----------|---------|-------------|
| `filetype:` | `filetype:pdf python guide` | Search specific file type |
| `ext:` | `ext:py flask` | Search by file extension |

### URL and Title

| Operator | Example | Description |
|----------|---------|-------------|
| `intitle:` | `intitle:debugging python` | Search in page title |
| `allintitle:` | `allintitle:python debugging guide` | All terms in title |
| `inurl:` | `inurl:docs api` | Search in URL |
| `allinurl:` | `allinurl:github python` | All terms in URL |

### Page Content

| Operator | Example | Description |
|----------|---------|-------------|
| `intext:` | `intext:"error handling"` | Search in page text |
| `allintext:` | `allintext:python error handling` | All terms in text |
| `inanchor:` | `inanchor:documentation` | Search in link anchor text |

### Time-based

| Operator | Example | Description |
|----------|---------|-------------|
| `before:YYYY-MM-DD` | `before:2024-01-01 python` | Results before date |
| `after:YYYY-MM-DD` | `after:2024-01-01 news` | Results after date |
| `daterange:` | `daterange:2024-2025 tech` | Date range (rarely used) |

### Other Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `cache:` | `cache:example.com` | View cached version |
| `info:` | `info:example.com` | Site information |
| `define:` | `define:debugging` | Dictionary definition |
| `stocks:` | `stocks:AAPL` | Stock information |
| `weather:` | `weather:London` | Weather information |
| `map:` | `map:New York` | Map results |
| `movie:` | `movie:Inception` | Movie information |
| `source:` | `news source:reuters` | News from source |

## Combining Operators

### Advanced Combinations

```
site:github.com intitle:python filetype:md
→ Find markdown Python docs on GitHub

(python OR javascript) site:stackoverflow.com after:2024-01-01
→ Recent Stack Overflow posts about Python or JavaScript

"machine learning" filetype:pdf site:.edu
→ ML PDFs from educational institutions

intitle:"api documentation" -site:w3schools.com
→ API docs excluding W3Schools

site:reddit.com intext:"python debugging" after:2024-01-01
→ Recent Reddit discussions about Python debugging
```

### Research Strategies

**Finding Documentation:**
```
site:docs.python.org debugging
site:github.com intitle:readme python
site:readthedocs.io python tutorial
```

**Academic Research:**
```
site:scholar.google.com "machine learning"
site:.edu filetype:pdf research
site:arxiv.org neural networks
```

**Technical Troubleshooting:**
```
site:stackoverflow.com [python] error
site:github.com issues python bug
intext:"TypeError" python solution
```

**Finding Code Examples:**
```
site:github.com filetype:py flask example
site:gitlab.com intitle:tutorial python
inurl:gist python script
```

## DuckDuckGo Search Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:reddit.com python` | Search specific site |
| `filetype:` | `filetype:pdf guide` | File type |
| `-` | `python -java` | Exclude term |
| `""` | `"exact phrase"` | Exact match |
| `OR` | `python OR javascript` | Either term |

### DuckDuckGo Bangs

| Bang | Example | Description |
|------|---------|-------------|
| `!g` | `!g python tutorial` | Google search |
| `!gh` | `!gh python requests` | GitHub search |
| `!so` | `!so python error` | Stack Overflow |
| `!w` | `!w python` | Wikipedia |
| `!mdn` | `!mdn javascript` | MDN Web Docs |
| `!pypi` | `!pypi requests` | Python Package Index |
| `!npm` | `!npm express` | NPM packages |

## Bing Search Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:microsoft.com` | Search specific site |
| `filetype:` | `filetype:docx` | File type |
| `intitle:` | `intitle:guide` | In title |
| `inurl:` | `inurl:blog` | In URL |
| `inanchor:` | `inanchor:link` | In anchor text |
| `ip:` | `ip:192.168.1.1` | IP address |
| `language:` | `language:en` | Language filter |
| `loc:` | `loc:US` | Location |
| `contains:` | `contains:pdf` | Contains file type |

## GitHub Search

### Repository Search

| Operator | Example | Description |
|----------|---------|-------------|
| `in:name` | `in:name python` | Search in repo name |
| `in:description` | `in:description api` | Search in description |
| `in:readme` | `in:readme tutorial` | Search in README |
| `stars:>N` | `stars:>1000` | Min star count |
| `forks:>N` | `forks:>100` | Min fork count |
| `language:` | `language:python` | Programming language |
| `created:` | `created:>2024-01-01` | Creation date |
| `pushed:` | `pushed:<2023-01-01` | Last push date |
| `topic:` | `topic:machine-learning` | Repository topic |
| `is:public` | `is:public python` | Public repos only |
| `archived:false` | `archived:false` | Not archived |

### Code Search

| Operator | Example | Description |
|----------|---------|-------------|
| `filename:` | `filename:package.json` | Filename |
| `extension:` | `extension:py` | File extension |
| `path:` | `path:src/utils` | Path contains |
| `repo:` | `repo:owner/name` | Specific repository |
| `user:` | `user:username` | User's repositories |
| `org:` | `org:organization` | Organization's repos |

### Issue Search

| Operator | Example | Description |
|----------|---------|-------------|
| `is:issue` | `is:issue bug` | Search issues |
| `is:pr` | `is:pr feature` | Search pull requests |
| `is:open` | `is:open bug` | Open items |
| `is:closed` | `is:closed` | Closed items |
| `label:` | `label:bug` | Has label |
| `author:` | `author:username` | Created by user |
| `assignee:` | `assignee:username` | Assigned to user |
| `mentions:` | `mentions:username` | Mentions user |

## Stack Overflow Search

| Operator | Example | Description |
|----------|---------|-------------|
| `[tag]` | `[python] error` | Has tag |
| `user:id` | `user:12345` | By user |
| `score:N` | `score:10` | Minimum score |
| `answers:N` | `answers:1` | Has answers |
| `isaccepted:yes` | `isaccepted:yes` | Has accepted answer |
| `inquestion:id` | `inquestion:12345` | In specific question |
| `created:date` | `created:2024` | Creation date |

## Best Practices

1. **Start broad, then narrow**: Begin with general terms, add operators
2. **Use quotes for phrases**: Exact matching for multi-word terms
3. **Combine operators**: Multiple operators for precise results
4. **Exclude noise**: Use `-` to remove irrelevant results
5. **Check multiple sources**: Different search engines, different results
6. **Save effective queries**: Document queries that work well
7. **Use site-specific search**: Often better than search engines

## Common Query Templates

**Finding tutorials:**
```
(tutorial OR guide OR "how to") [topic] -video
```

**Finding official docs:**
```
site:docs.[topic].org OR site:[topic].org/docs
```

**Finding code examples:**
```
site:github.com [language] [feature] example
```

**Finding solutions:**
```
[error message] [language] solution OR fix
```

**Research papers:**
```
site:.edu OR site:scholar.google.com [topic] filetype:pdf
```
