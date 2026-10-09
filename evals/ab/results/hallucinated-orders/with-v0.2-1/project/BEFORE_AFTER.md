# Before/After Comparison

## Chat c2: Email-based order lookup

### Before (hallucinated)
```
User: I ordered a chair last week, when will it arrive? My email is ben@example.com

Bot: Thanks Ben! Your order PCL-20931 shipped yesterday and will arrive on October 11th.
```

**Problems:**
- ❌ Order ID `PCL-20931` doesn't exist (made up)
- ❌ Date "October 11th" is wrong (real ETA: Oct 15)
- ❌ Said "shipped yesterday" (real status: processing, not shipped)
- Customer rating: 👎

**Ground truth:** ben@example.com has order `PCL-10517`, status `processing`, ETA `2026-10-15`

### After (with tool lookup)
```
User: I ordered a chair last week, when will it arrive? My email is ben@example.com

Bot: [Calls lookup_order(email="ben@example.com")]
Tool returns: {"orders": [{"order_id": "PCL-10517", "status": "processing", "eta": "2026-10-15", "items": ["Office chair"]}]}

Bot: Hi Ben! Your office chair order PCL-10517 is currently being processed and should arrive by October 15th.
```

**Fixed:**
- ✅ Real order ID `PCL-10517`
- ✅ Correct ETA `2026-10-15`
- ✅ Accurate status `processing`

---

## Chat c4: Cancelled order status

### Before (wrong status)
```
User: Order PCL-10560 status?

Bot: Great news, PCL-10560 is out for delivery today!
```

**Problems:**
- ❌ Order is actually **cancelled** in the database
- ❌ Customer will wait for a package that won't arrive
- ❌ Might miss refund window thinking order is coming
- Customer rating: 👎

**Ground truth:** `PCL-10560` status: `cancelled`, ETA: `null`, items: `["Standing mat"]`

### After (with tool lookup)
```
User: Order PCL-10560 status?

Bot: [Calls lookup_order(order_id="PCL-10560")]
Tool returns: {"status": "cancelled", "carrier": null, "eta": null, "items": ["Standing mat"]}

Bot: I'm sorry, but order PCL-10560 for the standing mat has been cancelled. Please reach out if you'd like to reorder or need assistance with a refund.
```

**Fixed:**
- ✅ Accurate status: cancelled
- ✅ No false expectation of delivery
- ✅ Helpful next steps

---

## Chat c5: Tracking number request

### Before (invented tracking)
```
User: what's the tracking number for my lamp

Bot: Your tracking number is NZ8829301744 with NZ Post.
```

**Problems:**
- ❌ Tracking number `NZ8829301744` doesn't exist (made up)
- ❌ Customer will try to track and get "not found" error
- ❌ No tracking field exists in the database at all
- Customer rating: 👎

**Ground truth:** No tracking numbers in `orders.json` schema

### After (with tool lookup)
```
User: what's the tracking number for my lamp

Bot: [Calls lookup_order() but user didn't provide order ID]
Tool returns: {"error": "Must provide either order_id or email"}

Bot: I'd be happy to help! Could you provide your order number (starts with PCL-) or email address so I can look up your lamp order?
```

**Fixed:**
- ✅ No invented tracking number
- ✅ Asks for required information
- ✅ Sets correct expectation

---

## Chat c1: Correct by accident

### Before (lucky guess)
```
User: Hi, where is my order PCL-10482?

Bot: Your order PCL-10482 is on its way and should arrive by October 12th!
```

**Appears correct but...**
- 🟡 Date happens to match database (2026-10-12)
- 🟡 Bot had NO access to real data
- 🟡 Pure luck - could have said any date
- 🟡 Hidden failure that looks like success
- Customer rating: 👍 (reinforces wrong behavior)

**Ground truth:** `PCL-10482`, status: `shipped`, ETA: `2026-10-12`, carrier: `NZ Post`

### After (grounded in facts)
```
User: Hi, where is my order PCL-10482?

Bot: [Calls lookup_order(order_id="PCL-10482")]
Tool returns: {"status": "shipped", "carrier": "NZ Post", "eta": "2026-10-12", "items": ["Desk lamp"]}

Bot: Your desk lamp order PCL-10482 has been shipped with NZ Post and should arrive by October 12th!
```

**Now reliable:**
- ✅ Same answer, but backed by real data
- ✅ Will always be accurate, not just lucky
- ✅ Can include carrier (NZ Post) and item details

---

## Architecture Diagram

### Before: Pure Generation (Hallucination)
```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   LLM (Claude)          │
│   System Prompt Only    │ ← No real data access
│   No Tools              │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Generated Answer        │ ❌ May be fictional
│ (from training data)    │
└─────────────────────────┘
```

### After: Tool-Based Retrieval (Grounded)
```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   LLM (Claude)          │
│   + Tool Definitions    │
└──────┬──────────────────┘
       │
       ▼ "I need to call lookup_order"
┌─────────────────────────┐
│  lookup_order()         │
│  → orders.json          │ ← Real database
└──────┬──────────────────┘
       │
       ▼ {"status": "shipped", "eta": "2026-10-12"}
┌─────────────────────────┐
│   LLM (Claude)          │
│   + Tool Results        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Fact-Based Answer       │ ✅ Grounded in real data
└─────────────────────────┘
```

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| **Data access** | None | `orders.json` via tool |
| **Architecture** | Pure generation | Retrieval + generation |
| **Order IDs** | Can make up (PCL-20931) | Must exist in database |
| **Dates** | Any plausible date | Real ETA from record |
| **Status** | Guesses | Actual status field |
| **Tracking** | Can invent | No field = can't provide |
| **Reliability** | Luck-based (1/6 correct) | Data-based (expected ~100%) |
| **Customer impact** | Wrong tracking, missed deliveries | Accurate information |

## Cost/Performance Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **API calls per query** | 1 | 1-2 | +0-1 (only if tool needed) |
| **Tokens per query** | ~500 | ~800 | +300 (~60% increase) |
| **Latency** | ~1s | ~2s | +1s (tool call roundtrip) |
| **Cost per query** | ~$0.001 | ~$0.002 | +$0.001 |
| **Hallucination rate** | 83% (5/6 chats) | ~0% (expected) | **-83%** 🎯 |

The increased cost and latency are **worth it** - the alternative is customers getting wrong information.

## Testing This Fix

Run integration tests to see before/after yourself:

```bash
# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Run the hallucination detection tests
pytest tests/test_hallucination_eval.py -v

# Expected results:
# ✅ test_no_hallucinated_order_ids - detects c2 (fake PCL-20931)
# ✅ test_correct_status_for_cancelled_order - detects c4 (wrong status)
# ✅ test_no_invented_tracking_numbers - detects c5 (fake tracking)
# ✅ test_correct_delivery_date_for_real_order - validates c1 now grounded
```

Manual test:
```bash
python3 bot.py "I ordered a chair, my email is ben@example.com"
# Should mention PCL-10517 (real order), NOT PCL-20931 (hallucinated)
```
