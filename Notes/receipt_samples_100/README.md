# Receipt Intelligence System - Take-Home Challenge

## Overview
Build an intelligent receipt processing and querying system that can ingest receipt data, vectorize it for semantic search, and answer natural language queries about spending patterns.

## Time Limit
**72 hours** from receipt of this challenge

## Receipt Dataset
You have been provided with **100 sample receipts** covering a 3-month period (November 2023 - January 2024) representing various realistic spending patterns:

**Distribution by Category:**
- **Grocery** (25 receipts): Whole Foods, Trader Joe's, Safeway, Costco, Target, Walmart
- **Restaurants** (20 receipts): Fine dining, casual dining, sushi, pizza, burgers, Thai, Vietnamese, Mediterranean
- **Coffee Shops** (15 receipts): Blue Bottle, Starbucks, Peet's, Philz, Ritual Coffee
- **Fast Food** (15 receipts): Chipotle, McDonald's, Subway, Panera, Taco Bell
- **Electronics** (8 receipts): Best Buy, Apple Store, Micro Center, B&H Photo
- **Pharmacy** (7 receipts): CVS, Walgreens, Rite Aid (some with prescriptions)
- **Retail Clothing** (5 receipts): H&M, Gap, Nike, HomeGoods, Bed Bath & Beyond
- **Hardware** (3 receipts): Home Depot, Lowe's, Ace Hardware
- **Gas Stations** (2 receipts): Chevron, Shell, 76

**Total Spending:** ~$8,000-10,000 across all receipts
**Date Range:** November 1, 2023 - January 31, 2024

## Why This Dataset is Challenging

### Format Variety
- Different date formats (MM/DD/YYYY)
- Varying receipt layouts (compact vs. detailed)
- Multiple tax rates (8.5% - 9.25% based on location)
- Different item presentation styles
- Various payment methods (Visa, Mastercard, Amex, Discover, cash, Apple Pay)

### Real-World Complexity
- Tips on restaurant receipts (15-22%)
- Delivery fees on some receipts
- Loyalty discounts (Target RedCard, pharmacy rewards)
- Extended warranties on electronics
- Prescription copays at pharmacies
- Fuel + convenience items at gas stations
- Multi-item orders with modifiers (coffee add-ons)

### Data Extraction Challenges
- Extracting merchant names from various formats
- Parsing dates consistently
- Identifying total vs. subtotal vs. tax
- Handling tips and fees
- Categorizing items automatically
- Dealing with abbreviated item names

## Core Requirements

### 1. Data Ingestion & Parsing
- Extract structured data from receipt text files
- Parse key fields: merchant, date, items, prices, totals, categories
- Handle various receipt formats gracefully
- Extract metadata (payment method, location, tax rate, discounts, etc.)
- Normalize dates to standard format

### 2. Chunking Strategy ⭐ **CRITICAL**
Design and implement a chunking strategy that balances:
- **Granularity**: Receipt-level vs. item-level vs. hybrid
- **Context preservation**: Which item belongs to which receipt?
- **Query performance**: Fast retrieval without losing accuracy
- **Searchability**: Can you find both "all grocery receipts" and "organic bananas"?

**You must document your chunking decision and reasoning clearly.**

Options to consider:
- **Receipt-level chunking**: One embedding per receipt (simpler, loses item granularity)
- **Item-level chunking**: One embedding per line item (more granular, context challenges)
- **Hybrid approach**: Both levels indexed (more complex, most powerful)

### 3. Vector Database Setup
Use **Pinecone** or **LangChain with your choice of vector store** to:
- Store embeddings with rich metadata
- Support hybrid search (vector similarity + metadata filtering)
- Enable efficient querying across 100+ receipts
- Handle proper indexing for scalability

**Metadata schema should include:**
```python
{
    "receipt_id": "receipt_001",
    "merchant": "Whole Foods Market",
    "date": "2023-11-07",
    "category": "grocery",
    "total_amount": 40.32,
    "tax": 3.24,
    "payment_method": "VISA",
    "location": "Daly City, CA",
    "items_count": 5,
    # Item-level metadata (if chunking by item):
    "item_name": "Chicken Breast",
    "item_price": 12.07,
    "parent_receipt_id": "receipt_001"
}
```

### 4. Natural Language Query Interface
Implement a system that can answer queries like:

**Temporal Queries:**
- "How much did I spend in December 2023?"
- "What did I buy in the first week of January?"
- "Show me all receipts from before Christmas"
- "Find purchases from last month"

**Merchant Queries:**
- "Find all Whole Foods receipts"
- "How much have I spent at coffee shops?"
- "What's my total spending at restaurants?"
- "Show me all Starbucks purchases"

**Category/Item Queries:**
- "Show me all electronics purchases"
- "Find receipts with warranties"
- "What pharmacy items did I buy?"
- "List all coffee purchases"
- "Find receipts with chicken"

**Price-Based Queries:**
- "Show me receipts over $100"
- "Find all purchases under $20"
- "What were my most expensive purchases?"

**Location Queries:**
- "Show me all San Francisco receipts"
- "Find purchases in Oakland"

**Complex Multi-Filter Queries:**
- "Find all grocery receipts over $50 in December"
- "What restaurant orders included tips over 20%?"
- "Show me electronics with warranties from Best Buy"
- "Find all coffee purchases in the morning (before noon)"

**Aggregation Queries:**
- "What's my total spending across all receipts?"
- "Break down my spending by category"
- "Which merchant have I spent the most at?"
- "What's my average grocery bill?"
- "How much do I spend on coffee per week?"

### 5. Query Understanding with LLM
Use an LLM to:
- Parse natural language queries into structured filters
- Extract temporal expressions ("last week", "December", "before Christmas")
- Identify categories, merchants, and price ranges
- Determine if aggregation is needed
- Handle ambiguous queries ("that coffee place" → semantic search)
- Convert relative dates to absolute dates

**Example Query Flow:**
```
User: "How much did I spend on groceries in December?"
↓
LLM extracts:
- category_filter: "grocery"
- date_range: "2023-12-01" to "2023-12-31"
- aggregation: sum(total_amount)
↓
System executes:
- Metadata filter: category="grocery" AND date between dates
- Aggregate: SUM all matching receipt totals
- Return: "$450.23 across 12 grocery receipts"
```

## Deliverables

### 1. Working Code
- Clean, well-organized Python codebase
- Clear separation of concerns:
  - Receipt parsing/ingestion
  - Embedding generation
  - Vector storage
  - Query processing
  - LLM integration
- Type hints and docstrings
- Error handling
- `requirements.txt` or `pyproject.toml` with dependencies

### 2. Documentation (README.md)
**Required sections:**
1. **Setup Instructions**
   - Installation steps
   - API key configuration
   - Database setup
   - How to ingest the receipts

2. **Architecture Overview**
   - System diagram (can be ASCII art or image)
   - Data flow explanation
   - Component descriptions

3. **Chunking Strategy Explanation** ⭐ **CRITICAL**
   - What approach did you choose and why?
   - What are the trade-offs?
   - How is context preserved?
   - Example: "I chose item-level chunking because..."

4. **Usage Guide**
   - How to run queries
   - Example commands
   - Expected output format

5. **Design Decisions**
   - Why did you choose certain technologies?
   - What trade-offs did you make?
   - What would you do differently with more time?

6. **Known Limitations**
   - What edge cases aren't handled?
   - What would break the system?
   - Performance considerations

### 3. Demo
Provide **one** of:
- **Jupyter notebook** with working examples and explanations
- **CLI tool** that accepts natural language queries
- **Simple web interface** (optional, bonus points)
- **Video demo** showing the system in action

### 4. Test Results
Show that your system can handle at least **15 diverse queries** including:
- 3+ temporal queries
- 3+ merchant/category queries
- 3+ complex multi-filter queries
- 3+ aggregation queries
- Edge cases (e.g., "find returns", "receipts with warranties")

Include actual output from your system for these queries.

## Evaluation Criteria

### Technical Implementation (35%)
- Code quality, organization, and clarity
- Proper use of LangChain/Pinecone
- Error handling and edge cases
- Embedding quality and vector search implementation
- Performance considerations

### Chunking Strategy (30%) ⭐ **MOST IMPORTANT**
- **Clear explanation of approach and reasoning**
- Justification for design decisions
- Demonstration that context is preserved
- Understanding of trade-offs
- Quality of implementation

### Query Capabilities (25%)
- Accuracy of results across different query types
- Range of query types supported
- Hybrid search implementation (vector + metadata)
- LLM integration for query understanding
- Aggregation and analytics support

### Documentation (10%)
- Setup clarity and completeness
- Architecture explanation
- Example usage
- Design decisions articulated
- Code documentation

## Bonus Points (Optional)

These are **not required** but will impress us:
- **Category auto-tagging**: Use LLM to automatically categorize items
- **Spending analytics**: Visualizations, trends, insights
- **Conversation memory**: Handle follow-up queries ("What about just Starbucks?")
- **Ambiguous query handling**: "Show me that receipt from last week with the expensive thing"
- **Multi-modal capabilities**: Search by receipt image similarity (advanced)
- **Receipt validation**: Detect potentially incorrect OCR or parsing
- **Export capabilities**: Generate spending reports, CSV exports
- **Caching**: Smart caching of embeddings and query results
- **Batch processing**: Efficient processing of all 100 receipts

## Technology Stack

### Required
- **Python 3.9+**
- **LangChain** (recommended) OR direct SDK usage
- **Pinecone** (recommended) or another vector database
- **OpenAI API** or another LLM provider for embeddings and query understanding

### Recommended Libraries
- **Embeddings**: `openai` (text-embedding-3-small or text-embedding-3-large)
- **Vector DB**: `pinecone-client` or LangChain's Pinecone integration
- **Data Models**: `pydantic` for structured data
- **Date Parsing**: `python-dateutil` or `pendulum`
- **LLM Calls**: `langchain` or `openai` SDK

### Optional Libraries
- **API Framework**: `FastAPI` (if building an API)
- **UI**: `Streamlit` or `Gradio` (for quick demo UI)
- **Data Analysis**: `pandas` (for analytics)
- **Visualization**: `matplotlib` or `plotly` (for spending charts)
- **Testing**: `pytest` (for unit tests)

## Getting Started

### API Keys You'll Need
1. **Pinecone**: Free tier available at https://www.pinecone.io/
2. **OpenAI**: Get API key at https://platform.openai.com/
   - Needed for both embeddings and LLM calls
   - Estimated cost for this project: $2-5

### Suggested Approach

**Phase 1: Data Understanding (2-4 hours)**
- Read through sample receipts
- Understand format variations
- Sketch out data model
- Plan chunking strategy

**Phase 2: Parsing & Ingestion (6-8 hours)**
- Build receipt parser
- Extract structured data
- Handle edge cases
- Test on all 100 receipts

**Phase 3: Embedding & Storage (8-10 hours)**
- Implement chunking strategy
- Generate embeddings
- Set up Pinecone/vector DB
- Index all receipts with metadata

**Phase 4: Query System (10-14 hours)**
- Build query parser with LLM
- Implement hybrid search
- Add aggregation logic
- Test with various queries

**Phase 5: Testing & Refinement (6-8 hours)**
- Test edge cases
- Improve accuracy
- Optimize performance
- Fix bugs

**Phase 6: Documentation (4-6 hours)**
- Write README
- Create examples
- Document decisions
- Clean up code

**Total: ~40-50 hours of focused work**

## Submission

Please submit:

1. **Git repository** (GitHub/GitLab) with:
   - All source code
   - README.md with complete documentation
   - Requirements file
   - Example usage (notebook, CLI, or script)

2. **Short explanation** (choose one):
   - 5-10 minute video walkthrough
   - Written explanation (2-3 pages) of your approach
   - Live demo during follow-up call

3. **Test results** showing your system handling 15+ queries

**Submission Format:**
- Email git repository link to [recruiter email]
- Include any setup notes in README
- Mention any blockers or challenges you faced

## Questions?

If you have **clarifying questions**, email [recruiter email] within the first 24 hours of receiving this challenge.

We won't answer questions about implementation details, but we're happy to clarify:
- Dataset contents
- Expected outputs
- Evaluation criteria
- Time constraints

---

## Sample Queries to Support

Your system should be able to handle queries like these:

```python
# Temporal
query("How much did I spend in December?")
query("Show me all receipts from last week of November")
query("What did I buy on Christmas week?")

# Merchant
query("Find all Starbucks receipts")
query("How much have I spent at Whole Foods?")
query("Show me all fast food purchases")

# Category/Items  
query("Find all electronics with warranties")
query("Show me receipts with chicken")
query("What coffee drinks did I order?")

# Price-based
query("Show me all receipts over $100")
query("Find my most expensive purchase")
query("What purchases were under $10?")

# Multi-filter
query("Find grocery receipts over $50 in December")
query("Show me all San Francisco restaurant orders")
query("Electronics from Best Buy with warranty")

# Aggregation
query("What's my total spending?")
query("Break down spending by category")
query("Average grocery bill?")
query("How much do I spend on coffee per week?")

# Semantic/Ambiguous
query("That expensive electronics purchase from December")
query("The sushi place with sake")
query("Coffee shop with the croissant")
```

## Expected Output Quality

Good answers should:
- ✅ Be accurate (correct amounts, dates, merchants)
- ✅ Include relevant context (receipt IDs, dates, amounts)
- ✅ Handle aggregations correctly
- ✅ Provide clear, concise responses
- ✅ Handle "not found" cases gracefully

Example good response:
```
Query: "How much did I spend at Starbucks?"

Response: 
You spent $124.67 across 8 Starbucks visits:
- 12/05/2023: $16.42 (receipt_046)
- 12/18/2023: $14.28 (receipt_056)
- 01/01/2024: $18.93 (receipt_048)
...

Average per visit: $15.58
```

---

Good luck! We're excited to see your approach to this challenge. Remember that the chunking strategy decision and documentation is the most important part—show us your thinking!
