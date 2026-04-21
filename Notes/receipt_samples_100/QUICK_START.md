# Quick Start Guide

## What You Have

**103 files total:**
- 100 receipt text files (simulating OCR output)
- 3 documentation files

## To Send to Candidate

Simply send them the entire `receipt_samples_100/` folder.

**They should read first:**
1. `README.md` - Complete challenge requirements
2. Browse a few receipt samples to see format variety

## Files Included

### Documentation
- `README.md` - Complete challenge for candidates
- `INTERVIEWER_GUIDE.md` - Your evaluation rubric and testing guide
- `PACKAGE_SUMMARY.md` - Overview of the dataset
- `QUICK_START.md` - This file

### Receipts (100 files)
Named format: `receipt_XXX_category_YYYYMMDD.txt`

**By Category:**
- receipt_001 to receipt_025: Grocery (25 receipts)
- receipt_026 to receipt_045: Restaurant (20 receipts)
- receipt_046 to receipt_060: Coffee (15 receipts)
- receipt_061 to receipt_075: Fast Food (15 receipts)
- receipt_076 to receipt_083: Electronics (8 receipts)
- receipt_084 to receipt_090: Pharmacy (7 receipts)
- receipt_091 to receipt_095: Retail (5 receipts)
- receipt_096 to receipt_098: Hardware (3 receipts)
- receipt_099 to receipt_100: Gas (2 receipts)

## Sample Receipt Preview

### Grocery Example (receipt_001)
```
Walmart Supercenter
684 Market Street
Daly City, CA
Phone: (510)-555-1882

Date: 11/07/2023  Time: 19:22
Cashier: Sarah M.

Pasta                          $  4.21
Chicken Breast                 $ 12.07
Avocados (4)                   $  7.75
Apples (6)                     $  6.46
Orange Juice                   $  6.59

SUBTOTAL:                     $  37.08
TAX (8.8%):                    $   3.24
TOTAL:                        $  40.32

VISA ****8651            $  40.32
```

## Candidate Instructions (Summary)

**Timeline:** 72 hours

**Core Task:** Build a receipt intelligence system that:
1. Parses and ingests 100 receipt files
2. Implements a chunking strategy (receipt-level vs item-level)
3. Embeds and stores in vector database (Pinecone recommended)
4. Supports natural language queries with LLM
5. Handles aggregations and analytics

**Most Important:** Document chunking strategy with clear reasoning (30% of score)

**Must Support Queries Like:**
- "How much did I spend at Whole Foods?"
- "Find all grocery receipts from December"
- "Show me receipts over $100"
- "What's my total spending on restaurants?"

**Deliverables:**
- Working code (Python)
- README with setup, architecture, chunking explanation
- Demo (notebook, CLI, or video)
- Test results for 15+ queries

## Evaluation Quick Reference

**Scoring (100 points):**
- Chunking Strategy: 30 pts (MOST IMPORTANT)
- Technical Implementation: 35 pts
- Query Capabilities: 25 pts
- Documentation: 10 pts

**Passing:** 70/100
**Strong:** 80/100
**Exceptional:** 90+/100

**Evaluation Time:** ~3 hours
- Initial review: 30 min
- Testing: 60 min
- Code review: 45 min
- Discussion: 60 min

## Key Evaluation Points

✅ **Look For:**
- Clear chunking explanation with trade-offs
- Hybrid search (vector + metadata)
- Handles temporal queries
- Accurate aggregations
- Clean code with error handling

❌ **Red Flags:**
- No chunking justification
- Only vector search (no metadata filtering)
- Poor date handling
- Can't aggregate
- Sloppy code

---

**Ready to send!** Just share the `receipt_samples_100/` folder with candidates.
