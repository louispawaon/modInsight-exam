# Receipt Intelligence Challenge - Complete Package (100 Receipts)

## 📦 What You're Getting

### **100 Realistic Receipt Samples**
Programmatically generated with realistic variety and complexity.

**Total Spending Represented:** ~$8,000-10,000
**Date Range:** November 1, 2023 - January 31, 2024 (3 months)
**Average Receipt:** ~$80-100

### **Distribution by Category**

| Category | Count | Examples | Price Range |
|----------|-------|----------|-------------|
| **Grocery** | 25 | Whole Foods, Trader Joe's, Costco, Safeway, Target, Walmart | $30-$300 |
| **Restaurants** | 20 | Fine dining, casual, sushi, pizza, burgers, Thai, Vietnamese | $25-$200 |
| **Coffee Shops** | 15 | Blue Bottle, Starbucks, Peet's, Philz, Ritual Coffee | $8-$25 |
| **Fast Food** | 15 | Chipotle, McDonald's, Subway, Panera, Taco Bell | $10-$35 |
| **Electronics** | 8 | Best Buy, Apple Store, Micro Center, B&H Photo | $100-$650 |
| **Pharmacy** | 7 | CVS, Walgreens, Rite Aid (some with Rx) | $40-$150 |
| **Retail Clothing** | 5 | H&M, Gap, Nike, HomeGoods, Bed Bath & Beyond | $50-$200 |
| **Hardware** | 3 | Home Depot, Lowe's, Ace Hardware | $80-$550 |
| **Gas Stations** | 2 | Chevron, Shell, 76 | $50-$85 |

### **Realistic Complexity Features**

The receipts include:
- ✅ Multiple tax rates (8.5%-9.25% based on California location)
- ✅ Tips on restaurant receipts (15-22%)
- ✅ Loyalty discounts (Target RedCard, pharmacy rewards, member savings)
- ✅ Extended warranties on electronics
- ✅ Prescription copays at pharmacies
- ✅ Various payment methods (Visa, Mastercard, Amex, Discover, cash, Apple Pay)
- ✅ Item modifiers (coffee add-ons like oat milk, extra shots)
- ✅ Different receipt formats and layouts
- ✅ Realistic item name variations

### **Key Files**

1. **README.md** - Complete challenge description for candidates
   - Full requirements
   - 72-hour timeline
   - Deliverables and evaluation criteria
   - 30+ example queries to support
   - Suggested tech stack

2. **INTERVIEWER_GUIDE.md** - Your evaluation guide
   - Scoring rubric (out of 100 points)
   - Discussion questions
   - Common pitfalls
   - What success looks like
   - Testing scenarios

3. **PACKAGE_SUMMARY.md** - This file (quick reference)

4. **100 receipt .txt files** - Named like `receipt_001_grocery_20231107.txt`
   - Organized by number, category, and date
   - Ready to use immediately

## 🎯 What Makes This a Strong Challenge

### **The Core Difficulty: Chunking Strategy**
This is intentionally the hardest and most important part (30% of score):

**Candidates must decide:**
- Embed entire receipts? (Simpler, loses granularity)
- Embed individual items? (More powerful, context challenges)  
- Hybrid approach? (Most complex, best results)

**Strong candidates will:**
- Test multiple approaches
- Clearly document their reasoning
- Understand trade-offs
- Preserve context properly

### **Other Key Challenges**

1. **Hybrid Search Implementation**
   - When to use vector similarity vs metadata filtering?
   - Combining both approaches effectively
   - Example: "groceries over $50 in December" needs metadata filters, not just embeddings

2. **Temporal Understanding**
   - Parse "last week", "December", "before Christmas"
   - Convert relative dates to absolute
   - Handle various date formats

3. **Query Intelligence with LLM**
   - Natural language → structured filters
   - Extract categories, merchants, price ranges
   - Determine aggregation needs

4. **Aggregation Capabilities**
   - Sum totals across receipts
   - Calculate averages
   - Group by category/merchant
   - Spending trends

## ⏱️ Time Expectations (72 Hours)

**Realistic work breakdown for strong candidates:**
- Data exploration: 2-3 hours
- Receipt parsing: 6-8 hours
- Chunking implementation: 8-10 hours
- Vector DB setup: 4-6 hours
- Query system: 10-14 hours
- Testing & debugging: 6-8 hours
- Documentation: 4-6 hours
- Refinement: 4-6 hours

**Total actual work: 40-50 hours**

This leaves time for:
- Learning tools (if needed)
- Sleep and breaks
- Multiple iterations

## 📊 Evaluation Criteria

### Scoring Breakdown (100 points total)

**Chunking Strategy (30 points)** ⭐ Most Important
- Must include clear explanation and reasoning
- Document trade-offs
- Show context preservation strategy

**Technical Implementation (35 points)**
- Code quality and organization
- Proper vector DB usage
- Receipt parsing robustness
- Error handling

**Query Capabilities (25 points)**
- Handles 15+ diverse queries
- Hybrid search working
- Aggregations accurate
- LLM integration for parsing

**Documentation (10 points)**
- Clear setup instructions
- Architecture explanation
- Example usage
- Design decisions

**Passing Score:** 70/100
**Strong Candidate:** 80/100  
**Exceptional:** 90+/100

## 🚀 How to Use This Package

### For Sending to Candidates

Simply share the entire folder. They should:
1. Read **README.md** first (complete instructions)
2. Review the receipt samples to understand format variety
3. Plan their approach before coding
4. Submit within 72 hours

### For Evaluation

1. **Initial Review** (30 min):
   - Does it run? (try setup instructions)
   - Is chunking strategy documented?
   - Code quality check

2. **Testing** (60 min):
   - Run 15+ test queries from INTERVIEWER_GUIDE
   - Check accuracy of results
   - Test edge cases

3. **Code Review** (45 min):
   - Architecture quality
   - Error handling
   - Vector DB implementation
   - LLM integration

4. **Discussion** (60 min):
   - Chunking decision reasoning
   - System design questions
   - Trade-offs and limitations
   - Production considerations

**Total evaluation time: ~3 hours**

## 🎓 What Success Looks Like

### Excellent Submissions Will Have

✅ **Clear chunking strategy with reasoning**
- "I chose item-level chunking because..." with trade-off analysis
- Context preservation explained
- Alternative approaches considered

✅ **Working end-to-end system**
- Runs with < 15 min setup
- Handles temporal, merchant, category, price queries
- Accurate aggregations

✅ **Hybrid search implementation**
- Knows when to use vector vs metadata
- Combines approaches effectively
- Fast query performance

✅ **Good documentation**
- Clear setup instructions
- Architecture diagram
- Usage examples
- Design decisions explained
- Limitations acknowledged

✅ **Production thinking**
- Error handling
- Scalability considerations
- Performance optimization
- Testing approach

## ⚠️ Red Flags to Watch For

❌ No chunking strategy explanation
❌ Only uses vector search (ignores metadata)
❌ Can't handle temporal queries
❌ No aggregation support
❌ Poor code organization
❌ Missing documentation
❌ Can't explain trade-offs
❌ Submission took < 20 hours (rushed) or > 70 hours (struggled)

## 💡 Candidate Support

**They can ask clarifying questions within 24 hours about:**
- Dataset contents
- Expected outputs
- Evaluation criteria
- Time constraints

**You should NOT answer:**
- Implementation approaches
- Which technologies to use
- How to solve specific technical problems
- Debugging help

## 🔍 Example Test Queries

Use these during evaluation:

**Basic (must work):**
- "How much did I spend at Whole Foods?"
- "Show me all coffee purchases"
- "Find receipts from December"

**Intermediate:**
- "Grocery receipts over $50 in December"
- "What restaurants did I tip over 20% at?"
- "Find all electronics with warranties"

**Advanced:**
- "That expensive electronics purchase from Best Buy"
- "Coffee shop with the croissant"
- "How much do I spend per week on groceries?"

## 📝 Quick Stats

- **Files:** 103 total (100 receipts + 3 documentation files)
- **Dataset size:** ~150 KB text
- **Date range:** 3 months (Nov 2023 - Jan 2024)
- **Total value:** ~$8,000-10,000 in purchases
- **Categories:** 9 distinct types
- **Merchants:** 25+ different stores/restaurants
- **Locations:** 6 Bay Area cities

---

## Next Steps

1. **Review** the README.md to ensure it matches your requirements
2. **Send** the entire folder to candidates
3. **Use** INTERVIEWER_GUIDE.md for consistent evaluation
4. **Schedule** ~3 hours for thorough review of submissions

This challenge effectively tests:
- System design thinking
- Vector DB understanding
- LLM integration
- Data engineering skills
- Documentation abilities

Good luck with your interviews! The 100-receipt dataset provides enough complexity to differentiate strong candidates while being completable in 72 hours.
