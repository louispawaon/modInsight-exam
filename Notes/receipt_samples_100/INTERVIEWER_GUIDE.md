# Receipt Intelligence Challenge - Interviewer Guide (100 Receipts)

## Dataset Overview

### What's Included: 100 Receipts

**Distribution:**
- 25 Grocery stores (Whole Foods, Trader Joe's, Safeway, Costco, Target, Walmart)
- 20 Restaurants (diverse cuisines, price points)
- 15 Coffee shops (Blue Bottle, Starbucks, Peet's, Philz, Ritual)
- 15 Fast food (Chipotle, McDonald's, Subway, Panera, Taco Bell)
- 8 Electronics (Best Buy, Apple Store, Micro Center, B&H)
- 7 Pharmacies (CVS, Walgreens, Rite Aid - some with Rx)
- 5 Retail clothing (H&M, Gap, Nike, HomeGoods, etc.)
- 3 Hardware stores (Home Depot, Lowe's, Ace)
- 2 Gas stations (Chevron, Shell, 76)

**Key Stats:**
- **Total spending**: ~$8,000-10,000
- **Date range**: November 1, 2023 - January 31, 2024 (3 months)
- **Average receipt**: ~$80-100
- **Price range**: $10.50 (coffee) to $650+ (electronics)

### Complexity Features

The dataset includes realistic variety:
- ✅ Multiple tax rates (8.5% - 9.25% based on CA location)
- ✅ Tips on 20 restaurant receipts (15-22%)
- ✅ Loyalty discounts (Target RedCard, pharmacy rewards)
- ✅ Extended warranties on electronics
- ✅ Prescription copays at pharmacies
- ✅ Different payment methods (Visa, MC, Amex, Discover, cash, Apple Pay)
- ✅ Date format consistency challenges
- ✅ Item name variations and abbreviations

## Evaluation Framework

### Primary Success Criteria (Rank by importance)

**1. Chunking Strategy & Documentation (30%)** ⭐ **MOST CRITICAL**
This is the heart of the challenge. Strong candidates will:

**Excellent Answer:**
- Clearly articulates chosen approach (receipt-level, item-level, or hybrid)
- Provides specific reasoning with trade-off analysis
- Shows understanding of context preservation
- Demonstrates they tested multiple approaches
- Example: "I chose a hybrid approach because while receipt-level chunking is simpler, I needed item-level granularity for queries like 'find chicken breast'. I preserve context by storing parent receipt metadata with each item..."

**Good Answer:**
- Chooses one approach with clear reasoning
- Understands basic trade-offs
- Shows awareness of alternative approaches
- Example: "I used receipt-level chunking for simplicity. I recognize this loses item-level search but preserved merchant and category metadata for filtering..."

**Red Flags:**
- No explanation of chunking decision
- "I just embedded each receipt" without justification
- Doesn't understand trade-offs
- Can't articulate why they chose their approach

**2. Technical Implementation (35%)**
Strong candidates will demonstrate:

**Code Quality:**
- Clean architecture with separation of concerns
- Type hints and docstrings
- Good error handling
- Reusable components
- Tests (bonus)

**Vector Search Implementation:**
- Proper embedding generation (using appropriate models)
- Correct Pinecone/vector DB setup
- Metadata schema design
- Efficient indexing strategy

**Data Processing:**
- Robust receipt parsing (handles format variations)
- Date normalization
- Amount extraction (handles subtotal vs total vs tax)
- Category assignment

**Red Flags:**
- Spaghetti code, no structure
- No error handling
- Hardcoded values everywhere
- Can't handle receipt format variations
- Poor metadata schema

**3. Query Capabilities (25%)**
Excellent systems will handle:

**Hybrid Search:**
- Knows when to use vector search vs metadata filtering
- Combines both approaches effectively
- Example: "groceries in December" → metadata filter on category + date, not just vector search

**LLM Query Understanding:**
- Parses natural language into structured filters
- Extracts temporal expressions correctly
- Handles ambiguous queries ("that coffee place" → semantic search)
- Converts relative dates ("last week") to absolute

**Aggregation Support:**
- Can sum totals across receipts
- Group by merchant/category
- Calculate averages
- Handle edge cases (no results found)

**Red Flags:**
- Only uses vector search (ignoring metadata)
- Poor temporal query handling
- Can't aggregate across receipts
- Breaks on slightly unusual queries

**4. Documentation (10%)**
- Clear setup instructions
- Architecture explanation
- Usage examples
- Design decisions documented
- Known limitations acknowledged

## Testing Scenarios

### Required Queries (System Must Handle)

**Tier 1: Basic (Must work perfectly)**
1. "How much did I spend at Whole Foods?" → Aggregate specific merchant
2. "Show me all coffee purchases" → Category filter
3. "Find receipts from December 2023" → Date range filter
4. "What's my total spending?" → Aggregate all receipts

**Tier 2: Intermediate (Should work well)**
5. "Find all receipts over $100" → Price filter
6. "Show me electronics with warranties" → Category + metadata search
7. "How much did I spend on groceries in December?" → Category + date + aggregate
8. "What restaurants did I tip over 20% at?" → Category + calculation
9. "Find all San Francisco receipts" → Location filter
10. "What's my average grocery bill?" → Category + aggregate + calculation

**Tier 3: Advanced (Bonus if working)**
11. "That expensive electronics purchase from Best Buy" → Semantic + metadata
12. "Coffee shop with the croissant" → Item-level semantic search
13. "How much do I spend on coffee per week?" → Category + date range + division
14. "Find receipts from the week before Christmas" → Relative date parsing
15. "Show me all prescriptions I picked up" → Semantic search for pharmacy items

### Challenging Test Queries for Review

During the code review, test these to see how robust the system is:

**Edge Cases:**
- "Show me receipts with warranties" (should find electronics)
- "Find all loyalty discounts" (Target RedCard, pharmacy rewards)
- "What did I buy on 11/07/2023?" (exact date)
- "Show me all returns" (there are no returns in this dataset - should handle gracefully)

**Semantic Understanding:**
- "Find health-related purchases" (should find pharmacy + vitamins/supplements from grocery)
- "Show me prepared food purchases" (restaurants + fast food + deli items)
- "Find all subscriptions" (none in dataset - should say "no results found")

**Temporal Complexity:**
- "What did I spend in Q4 2023?" (Oct-Dec, but dataset is Nov-Dec)
- "Show me receipts from Thanksgiving week" (Nov 20-26, 2023)
- "Find purchases from the first week of January" (Jan 1-7, 2024)

**Multi-Constraint:**
- "Find all grocery receipts over $50 from Target" (category + price + merchant)
- "Show me restaurant receipts from San Francisco over $50" (category + location + price)
- "Electronics from December with warranties" (category + date + metadata)

## Discussion Questions

### During Initial Review

**1. "Walk me through your chunking strategy. What approach did you take and why?"**

**What to listen for:**
- Clear articulation of approach
- Understanding of trade-offs
- Testing/iteration mentioned
- Specific examples

**Great answer includes:**
- "I chose [approach] because [reasoning]"
- "I considered [alternatives] but [trade-offs]"
- "To preserve context, I [specific technique]"
- "I tested this by [validation method]"

**2. "How do you handle a query like 'How much did I spend on groceries in December?'"**

**What to listen for:**
- Breaks down query into components
- Mentions both LLM parsing and execution
- Explains metadata filtering
- Shows understanding of aggregation

**Great answer:**
- "First, I use the LLM to extract: category='grocery', date_range='Dec 2023', operation='sum'"
- "Then I query Pinecone with metadata filters: category='grocery' AND date BETWEEN '2023-12-01' AND '2023-12-31'"
- "I aggregate the total_amount from all matching receipts"
- "Return formatted response with breakdown"

**3. "Your system returns 15 coffee receipts for 'How much did I spend on coffee?' How do you aggregate?"**

**What to listen for:**
- Extracts total from each receipt
- Handles different amounts correctly
- Mentions validation/error handling

**Red flags:**
- "I just sum the vectors" (nonsensical)
- "I return all receipts and let the user add them" (lazy)
- Can't explain aggregation logic

**4. "How would you scale this to 10,000 receipts?"**

**What to listen for:**
- Batching strategies
- Indexing considerations
- Caching opportunities
- Performance concerns

**Great answer mentions:**
- Batch embedding generation
- Incremental updates (don't re-embed everything)
- Caching common queries
- Metadata indexing in Pinecone
- Potential preprocessing/materialized views

**5. "What would you do differently with more time or in production?"**

Shows self-awareness and production thinking:
- Better error handling and validation
- OCR integration for real receipt images
- Category taxonomy (structured classification)
- User feedback loop for improving categorization
- Caching and performance optimization
- Multi-user support with privacy
- Export/reporting capabilities
- Better date parsing (recurring expenses, patterns)

### Technical Deep-Dive Questions

**6. "Why did you choose text-embedding-3-small vs text-embedding-3-large?"**
- Shows understanding of embedding models
- Cost vs performance trade-offs
- Dimension considerations

**7. "How do you handle receipts where the merchant name is abbreviated or misspelled?"**
- Semantic search capabilities
- Fuzzy matching
- LLM-based normalization

**8. "What happens if someone queries for 'sushi' but you only have 'Akiko's Sushi'?"**
- Semantic understanding
- Category inference
- Metadata enrichment

**9. "How do you prevent the LLM from hallucinating receipt data?"**
- Grounding in actual results
- Validation of filters
- Clear distinction between search and generation

## Common Pitfalls to Watch For

### Implementation Issues

**1. Poor Metadata Schema**
- Missing critical fields (date, merchant, category, amount)
- Inconsistent data types
- No parent-child relationships for items

**2. Only Vector Search**
- Using embeddings for everything, even numeric filters
- Not leveraging metadata filtering
- Example: embedding "price over $100" instead of using metadata filter

**3. Date Handling**
- Can't parse relative dates ("last week")
- Inconsistent date formats
- No timezone handling

**4. No Aggregation**
- Returns receipts but can't sum amounts
- Can't calculate averages or totals
- User has to do math manually

**5. Brittle Parsing**
- Only works on specific receipt formats
- Breaks on slight variations
- No error handling for malformed receipts

### Documentation Issues

**1. No Chunking Explanation**
- Most common mistake
- Shows lack of understanding of core challenge
- "I embedded the receipts" without explanation

**2. No Setup Instructions**
- Can't reproduce results
- Missing API key setup
- No environment configuration

**3. No Trade-Off Discussion**
- Doesn't acknowledge limitations
- No discussion of alternative approaches
- Overconfident without validation

## What Success Looks Like

### Excellent Submission ✅

**Code:**
- Clean, well-organized Python
- Clear separation: parsing, embedding, querying
- Good error handling
- Type hints and documentation
- Actually runs without issues

**Chunking:**
- **Detailed explanation** with reasoning
- Shows tested multiple approaches
- Clear trade-off analysis
- Context preservation strategy
- Validation of approach

**Query Capability:**
- Handles 15+ diverse query types
- Hybrid search (vector + metadata)
- Accurate aggregations
- Good LLM integration for query parsing
- Graceful error handling

**Documentation:**
- Clear setup (can run in 5-10 minutes)
- Architecture diagram
- Example usage
- Design decisions explained
- Known limitations

### Time Allocation for Strong Candidates

For **72 hours** (actual work: 40-50 hours):

- **Data exploration**: 2-3 hours
- **Receipt parsing**: 6-8 hours
- **Chunking implementation**: 8-10 hours
- **Vector DB setup**: 4-6 hours
- **Query system**: 10-14 hours
- **Testing & debugging**: 6-8 hours
- **Documentation**: 4-6 hours
- **Refinement**: 4-6 hours

**Red flag:** Submissions that clearly took < 20 hours or > 70 hours

## Scoring Rubric

### Chunking Strategy (30 points)
- 25-30: Excellent explanation, tested multiple approaches, clear trade-offs
- 20-24: Good explanation, reasonable approach, understands trade-offs
- 15-19: Basic explanation, working approach, limited trade-off discussion
- 10-14: Minimal explanation, working but not well justified
- 0-9: No explanation or broken implementation

### Technical Implementation (35 points)
- 30-35: Excellent code, robust parsing, proper vector DB usage
- 25-29: Good code, handles most receipts, good vector implementation
- 20-24: Working code, handles many receipts, basic vector usage
- 15-19: Basic working code, limited receipt handling
- 0-14: Broken or very poor quality code

### Query Capabilities (25 points)
- 22-25: Handles 15+ queries, hybrid search, aggregations work well
- 18-21: Handles 10-14 queries, mostly hybrid search, basic aggregations
- 14-17: Handles 7-9 queries, limited hybrid search
- 10-13: Handles 4-6 queries, mostly vector-only
- 0-9: Handles < 4 queries or very inaccurate

### Documentation (10 points)
- 9-10: Excellent docs, clear setup, good examples, trade-offs discussed
- 7-8: Good docs, setup works, examples provided
- 5-6: Basic docs, setup mostly works
- 3-4: Minimal docs, hard to run
- 0-2: No docs or broken setup

**Passing score**: 70/100
**Strong candidate**: 80/100
**Exceptional**: 90+/100

## Follow-Up Interview Questions

If the candidate does well, use these for deeper discussion:

### System Design
- "How would you handle real-time receipt ingestion from mobile app?"
- "Design an API for this system - what endpoints?"
- "How would you handle multi-user scenarios with privacy?"

### Production Concerns
- "How would you monitor this system in production?"
- "What metrics would you track?"
- "How would you handle failures in embedding generation?"
- "Cost optimization strategies?"

### Extensions
- "How would you add receipt image OCR?"
- "Design a categorization system for items"
- "How would you detect and handle duplicate receipts?"
- "Build a spending insights feature - what would you include?"

### ML/AI Considerations
- "How would you evaluate embedding quality?"
- "What if users complain about search relevance?"
- "How would you incorporate user feedback to improve results?"

---

## Quick Reference Checklist

Before scoring, verify:

- [ ] Code runs without errors
- [ ] Setup instructions are clear (< 15 min setup)
- [ ] Chunking strategy is documented
- [ ] Handles temporal queries
- [ ] Handles merchant/category queries
- [ ] Handles aggregations
- [ ] Hybrid search (vector + metadata)
- [ ] LLM integration for query parsing
- [ ] Error handling exists
- [ ] Documentation is complete

---

Good luck with the interviews! This dataset provides a realistic challenge that separates strong candidates from average ones. The chunking strategy discussion is the key differentiator.
