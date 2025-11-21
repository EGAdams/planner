# Category Picker Hierarchical Fix

## Problem Description

The category-picker web component was not working correctly on the Daily Expense Categorizer page. When selecting a top-level category like "Utilities", the component would immediately turn green (finalize) instead of displaying subcategories.

### Expected Behavior (from demo)
- Select "Utilities" → Shows "Utilities / " in text box
- Dropdown repopulates with subcategories: Gas Bill, Electric Bill, Water/Sewer, Trash Pickup
- Continue drilling down until reaching a leaf category

### Actual Behavior (on Daily Expense Categorizer)
- Select "Utilities" → Component immediately turns green as if complete
- No subcategories shown

## Root Cause

The category-picker web component determines if a category is a leaf node by checking if it has a `children` property:

```javascript
if (next.children && next.children.length) {
    // Show next level
} else {
    // Leaf chosen -> finalize
}
```

**The API was returning a flat list without hierarchy:**
```json
[
  {"id":5,"name":"Utilities"},
  {"id":1,"name":"Supplies"}
]
```

**The demo had hierarchical structure:**
```json
[
  {
    "id": "utilities",
    "label": "Utilities",
    "children": [
      {"id": "gas", "label": "Gas Bill", "children": [...]}
    ]
  }
]
```

## Database Structure Issues

The `categories` table was originally flat with no support for hierarchy:

```sql
CREATE TABLE categories (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  kind ENUM('EXPENSE','INCOME') NOT NULL,
  is_active TINYINT(1) DEFAULT 1
);
```

**Missing:** `parent_id` field to establish parent-child relationships.

## Solution Implementation

### 1. Added `parent_id` Column to Categories Table

```sql
ALTER TABLE categories
  ADD COLUMN parent_id BIGINT UNSIGNED NULL AFTER id;

ALTER TABLE categories
  ADD FOREIGN KEY (parent_id) REFERENCES categories(id);
```

### 2. Populated Hierarchical Category Data

Created a three-level hierarchy:

**Utilities (id=5)**
- Gas Bill (id=10)
  - Housing Gas Bill (id=16)
  - Church Gas Bill (id=17)
- Electric Bill (id=11)
  - Housing Electric Bill (id=18)
  - Church Electric Bill (id=19)
- Water/Sewer (id=12)
- Trash Pickup (id=13)

**Supplies (id=1)**
- Office Supplies (id=20)
- Kitchen Supplies (id=21)

**Travel (id=2)**
- Airfare (id=22)
- Hotel (id=23)
- Meals (id=24)
- Ground Transportation (id=25)

### 3. Updated API to Return `parent_id`

**Updated Model:**
```python
class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None  # Added this field
```

**Updated API Endpoint:**
```python
@app.get("/api/categories")
async def get_categories():
    sql = """
        SELECT id, name, parent_id
        FROM categories
        WHERE kind = 'EXPENSE' AND is_active = 1
        ORDER BY parent_id, name
    """
    rows = query_all(sql, ())
    return [{"id": row['id'], "name": row['name'], "parent_id": row.get('parent_id')}
            for row in rows]
```

**API Now Returns:**
```json
[
  {"id":5,"name":"Utilities","parent_id":null},
  {"id":10,"name":"Gas Bill","parent_id":5},
  {"id":11,"name":"Electric Bill","parent_id":5},
  {"id":16,"name":"Housing Gas Bill","parent_id":10}
]
```

### 4. Frontend Builds Tree from Flat List

The `buildCategoryTree()` function in `daily_expense_categorizer.html` (lines 238-270) converts the flat API response into a hierarchical tree structure that the web component expects:

```javascript
function buildCategoryTree(categories) {
  const map = {};
  const roots = [];

  // First pass: create map with CategoryNode format
  categories.forEach(cat => {
    map[cat.id] = {
      id: String(cat.id),
      label: cat.name,
      children: [],
      _original: cat
    };
  });

  // Second pass: build tree structure
  categories.forEach(cat => {
    const node = map[cat.id];
    if (cat.parent_id && map[cat.parent_id]) {
      map[cat.parent_id].children.push(node);
    } else {
      roots.push(node);
    }
  });

  return roots;
}
```

## Files Modified

1. **Database Schema** - Added `parent_id` column with foreign key
2. **nonprofit_finance_db/api_server.py**
   - Updated `Category` model (line 76)
   - Updated `/api/categories` endpoint (lines 155-171)
3. **Categories Data** - Inserted hierarchical subcategories

## Future Considerations

### Adding New Categories

When adding new categories with hierarchy:

1. **Insert parent category first:**
```python
execute("INSERT INTO categories (name, kind, is_active) VALUES ('New Parent', 'EXPENSE', 1)", ())
parent_id = query_one("SELECT LAST_INSERT_ID() as id", ())['id']
```

2. **Insert children with parent_id:**
```python
execute("INSERT INTO categories (name, kind, parent_id, is_active) VALUES ('Child Category', 'EXPENSE', %s, 1)", (parent_id,))
```

### Hierarchy Depth

The current implementation supports **unlimited depth**. The web component and `buildCategoryTree()` function handle any number of levels recursively.

### Category Constraints

- Categories have a unique constraint on `(name, kind)` combination
- `parent_id` can be NULL (for root categories)
- Foreign key ensures `parent_id` references a valid category
- Leaf categories (no children) are the only ones that finalize the picker

## Testing

To verify the fix works:

1. Open http://localhost:8080/
2. Click on an uncategorized transaction's category picker
3. Select "Utilities"
   - ✅ Should show "Utilities / " in status box
   - ✅ Dropdown should repopulate with: Gas Bill, Electric Bill, Water/Sewer, Trash Pickup
4. Select "Gas Bill"
   - ✅ Should show "Utilities / Gas Bill / "
   - ✅ Dropdown should show: Housing Gas Bill, Church Gas Bill
5. Select "Housing Gas Bill"
   - ✅ Component turns green (finalized)
   - ✅ Shows "Utilities / Gas Bill / Housing Gas Bill"
   - ✅ Transaction is updated with the category
