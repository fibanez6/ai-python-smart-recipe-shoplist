# JSONExtractor - Universal JSON Data Extraction Utility

The `JSONExtractor` is a powerful and flexible utility for extracting specific data from complex JSON structures. It supports multiple extraction patterns including basic field selection, nested object extraction, wildcard array processing, and mixed instruction sets.

**Note:** This documentation is based on comprehensive testing of the actual API behavior and includes working examples with expected outputs.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Extraction Patterns](#extraction-patterns)
- [Advanced Examples](#advanced-examples)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

## Installation

The JSONExtractor is part of the AI Recipe Shoplist project and requires the following dependencies:

```bash
pip install jmespath
```

## Quick Start

```python
from app.utils.json_extractor import JSONExtractor

# Sample data
data = {
    "name": "Cherry Tomatoes",
    "price": {"amount": 139, "currency": "AUD"},
    "categories": [{"name": "Fruits"}, {"name": "Organic"}]
}

# Define extraction rules - JSONExtractor requires rules at initialization
rules = {
    'name': True,
    'price.amount': True
}

# Initialize the extractor with rules
extractor = JSONExtractor(rules)

# Extract data
result = extractor.extract(data)
# Output: {"name": "Cherry Tomatoes", "price": {"amount": 139}}
```

## Extraction Patterns

The JSONExtractor supports four main extraction patterns:

### 1. Basic Field Extraction

Extract specific fields using a simple list of field paths.

```python
# Simple field extraction
data = {
    "id": 123,
    "name": "Product Name",
    "description": "Product description",
    "price": 29.99,
    "inStock": True
}

rules = {
    "name": True,
    "price": True,
    "inStock": True
}
extractor = JSONExtractor(rules)
result = extractor.extract(data)

# Output:
# {
#     "name": "Product Name",
#     "price": 29.99,
#     "inStock": True
# }
```

### 2. Nested Object Extraction

Access nested objects using dot notation.

```python
data = {
    "product": {
        "details": {
            "name": "Advanced Widget",
            "specifications": {
                "weight": "2.5kg",
                "dimensions": "10x10x5cm"
            }
        },
        "pricing": {
            "amount": 149.99,
            "currency": "USD"
        }
    }
}

rules = {
    "product.details.name": True,
    "product.pricing": True
}
extractor = JSONExtractor(rules)
result = extractor.extract(data)

# Output:
# {
#     "product": {
#         "details": {
#             "name": "Advanced Widget"
#         },
#         "pricing": {
#             "amount": 149.99,
#             "currency": "USD"
#         }
#     }
# }
```

### 3. Wildcard Array Extraction

Extract values from arrays using wildcard patterns. **Important:** At root level, wildcard extraction creates nested structures, not flat arrays.

```python
data = {
    "name": "Multi-Category Product",
    "categories": [
        {"name": "Electronics", "id": 1},
        {"name": "Gadgets", "id": 2},
        {"name": "Tech", "id": 3}
    ],
    "tags": [
        {"label": "popular"},
        {"label": "new"},
        {"label": "featured"}
    ]
}

rules = {
    'name': True,
    'categories[*].name': True,
    'tags[*].label': True
}
extractor = JSONExtractor(rules)
result = extractor.extract(data)

# Output (note the nested structure):
# {
#     "name": "Multi-Category Product",
#     "categories": {"name": ["Electronics", "Gadgets", "Tech"]},
#     "tags": {"label": ["popular", "new", "featured"]}
# }
```

### 4. Mixed Instructions

Combine multiple extraction patterns using a dictionary with different rule types.

```python
data = {
    "sku": "PROD-001",
    "name": "Premium Product",
    "brandName": "TechCorp",
    "price": {
        "amount": 299.99,
        "currency": "USD",
        "tax": 29.99
    },
    "categories": [
        {"name": "Premium", "type": "quality"},
        {"name": "Electronics", "type": "category"}
    ],
    "images": [
        {"url": "image1.jpg", "type": "main"},
        {"url": "image2.jpg", "type": "thumbnail"}
    ]
}

rules = {
    'sku': True,
    'name': True,
    'brandName': True,
    'price': {
        'fields': ['amount', 'currency']  # Extract subset of nested object
    },
    'categories[*].name': True,  # Wildcard extraction
    'images[*].url': True
}

extractor = JSONExtractor(rules)
result = extractor.extract(data)

# Output (note: custom key names don't work as expected):
# {
#     "sku": "PROD-001",
#     "name": "Premium Product", 
#     "brandName": "TechCorp",
#     "price": {
#         "amount": 299.99,
#         "currency": "USD"
#     },
#     "categories": {"name": ["Premium", "Electronics"]},
#     "images": {"url": ["image1.jpg", "image2.jpg"]}
# }
```

## Advanced Examples

### E-commerce Product Extraction

Extract essential product information from a complex e-commerce API response:

```python
# Complex ALDI API response
aldi_response = {
    "data": [
        {
            "sku": "000000000000457910",
            "name": "Cherry Tomatoes in Tomato Juice 400g",
            "brandName": "CASA BARELLI",
            "quantityUnit": "ea",
            "sellingSize": "0.4 kg",
            "price": {
                "amount": 139,
                "amountRelevantDisplay": "$1.39",
                "comparisonDisplay": "$3.48 per 1 kg"
            },
            "categories": [
                {"name": "Pantry", "id": "pantry"},
                {"name": "Canned Food", "id": "canned"}
            ],
            "assets": [
                {
                    "url": "https://example.com/image1.jpg",
                    "type": "image"
                }
            ],
            "availability": {
                "inStock": True,
                "store": {
                    "name": "ALDI Sydney",
                    "postcode": "2000"
                }
            }
        }
    ]
}

# Extraction rules for clean product data  
rules = {
    "data": {
        "fields": ["name", "brandName", "sku", "sellingSize"],
        "price": {
            "fields": ["amount", "amountRelevantDisplay"]
        },
        "categories[*].name": True,  # This produces flat arrays in nested context
        "assets[*].url": True,      # Key becomes 'assets_url' in nested context
        "availability.store.name": "storeName"
    }
}

extractor = JSONExtractor(rules)
result = extractor.extract(aldi_response)

# Output includes flat arrays for nested wildcards:
# {
#   "data": [
#     {
#       "name": "Cherry Tomatoes in Tomato Juice 400g",
#       "brandName": "CASA BARELLI", 
#       "sku": "000000000000457910",
#       "sellingSize": "0.4 kg",
#       "price": {"amount": 139, "amountRelevantDisplay": "$1.39"},
#       "categories": ["Pantry", "Canned Food"],  # Flat array!
#       "assets_url": ["https://example.com/image1.jpg"],  # Key name changed!
#       "availability": {"store": {"name": "ALDI Sydney"}}
#     }
#   ]
# }
```

### Multi-Level Nested Extraction

Handle deeply nested structures with multiple array levels:

```python
complex_data = {
    "restaurants": [
        {
            "name": "Italian Bistro",
            "menu": {
                "sections": [
                    {
                        "title": "Appetizers",
                        "items": [
                            {"name": "Bruschetta", "price": 12.50},
                            {"name": "Calamari", "price": 15.00}
                        ]
                    },
                    {
                        "title": "Mains", 
                        "items": [
                            {"name": "Pasta Carbonara", "price": 22.00},
                            {"name": "Risotto", "price": 24.00}
                        ]
                    }
                ]
            }
        }
    ]
}

rules = {
    "restaurants": {
        "fields": ["name"],
        "menu.sections[*].title": True,       # Becomes 'menu_sections_title' 
        "menu.sections[*].items[*].name": True # Becomes 'menu_sections_items_name'
    }
}

extractor = JSONExtractor(rules)
result = extractor.extract(complex_data)

# Output includes flattened menu items with generated key names
```

### Array Limit and Fields Extraction

Use the `fields` and `limit` options for controlled data extraction:

```python
inventory_data = {
    "products": [
        {"name": "Laptop", "price": 1200, "inStock": True, "category": "Electronics"},
        {"name": "Mouse", "price": 25, "inStock": False, "category": "Electronics"},  
        {"name": "Desk", "price": 300, "inStock": True, "category": "Furniture"},
        {"name": "Chair", "price": 150, "inStock": True, "category": "Furniture"}
    ]
}

# Extract specific fields from limited number of products
rules = {
    "products": {
        "limit": 2,
        "fields": ["name", "price"]
    }
}
extractor = JSONExtractor(rules)
result = extractor.extract(inventory_data)

# Output: 
# {
#   "products": [
#     {"name": "Laptop", "price": 1200},
#     {"name": "Mouse", "price": 25}
#   ]
# }
```

### Array Root Handling

Process data where the root is an array:

```python
# API returns array directly
products_array = [
    {"id": 1, "name": "Product A", "price": 100},
    {"id": 2, "name": "Product B", "price": 200},
    {"id": 3, "name": "Product C", "price": 150}
]

rules = {
    "name": True,
    "price": True
}
extractor = JSONExtractor(rules)
result = extractor.extract(products_array)

# Output: Array of objects with only name and price
# [
#     {"name": "Product A", "price": 100},
#     {"name": "Product B", "price": 200}, 
#     {"name": "Product C", "price": 150}
# ]
```

## Key Behavior Notes

Based on extensive testing, here are important behaviors to understand:

### Quick Reference Table

| Rule Type | Context | Input | Output | Notes |
|-----------|---------|--------|--------|-------|
| `'field': True` | Any | `{"field": "value"}` | `{"field": "value"}` | Basic extraction |
| `'obj.field': True` | Any | `{"obj": {"field": "val"}}` | `{"obj": {"field": "val"}}` | Nested extraction |
| `'arr[*].field': True` | Root level | `{"arr": [{"field": "a"}]}` | `{"arr": {"field": ["a"]}}` | Nested structure |
| `'arr[*].field': True` | Array context | `[{"arr": [{"field": "a"}]}]` | `[{"arr": ["a"]}]` | Flat array |
| `'arr[*].url': True` | Array context | `[{"arr": [{"url": "x"}]}]` | `[{"arr_url": ["x"]}]` | Key renamed |
| `None` values | Any | `{"field": None}` | `{}` | Filtered out |

### Wildcard Array Extraction Patterns

**Root Level Wildcards** (create nested structures):
```python
data = {
    "categories": [{"name": "A"}, {"name": "B"}]
}
rules = {'categories[*].name': True}
# Result: {'categories': {'name': ['A', 'B']}}
```

**Nested Context Wildcards** (create flat arrays with modified keys):
```python  
data = {
    "data": [  # The key name must match the rule key
        {
            "categories": [{"name": "A"}, {"name": "B"}],
            "assets": [{"url": "img1.jpg"}, {"url": "img2.jpg"}]
        }
    ]
}
rules = {
    'data': {  # Must match the data structure key
        'categories[*].name': True,  # Becomes: 'categories': ['A', 'B'] (flat!)
        'assets[*].url': True       # Becomes: 'assets_url': ['img1.jpg', 'img2.jpg']
    }
}
# Result: {'data': [{'categories': ['A', 'B'], 'assets_url': ['img1.jpg', 'img2.jpg']}]}
```

### Key Naming in Nested Contexts

**When rules are applied to array items (e.g., `"data": {...}` where data is an array):**
- `categories[*].name` → `categories: [...]` (flat array - special case)
- `assets[*].url` → `assets_url: [...]` (underscore-joined key name)
- `price.amount` → `price: {amount: value}` (nested structure preserved)

**At root level (no nested array context):**
- `categories[*].name` → `categories: {name: [...]}` (nested structure)
- All dot notation preserves the original structure

### Value Filtering

- **Null Values**: `None` values are completely filtered out (no key created)
- **Missing Fields**: Non-existent fields are silently ignored  
- **Empty Arrays**: `[]` arrays are preserved as empty arrays

### Rule Syntax Limitations

- Custom key names in wildcards don't work as expected
- Default values for missing fields are not supported
- Complex JMESPath filtering has limited support

## API Reference

### JSONExtractor Class

#### `__init__(self)`
Initialize a new JSONExtractor instance.

#### `extract(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]`

Extract data according to the rules specified during initialization.

**Parameters:**
- `data`: The JSON data to extract from (dict or list of dicts)

**Returns:**
- Extracted data structure with same root type as input (dict or list)

**Raises:**
- Various exceptions for invalid data or malformed rules

### Rule Formats

#### Basic Field Extraction
```python
rules = {
    'field1': True,
    'nested.field': True,
    'array[*].property': True
}
```

#### Mixed Instructions Dictionary
```python
rules = {
    'field1': True,                           # Basic field extraction
    'nested.object': {                        # Nested object subset
        'fields': ['subfield1', 'subfield2'] 
    },
    'array[*].property': True                 # Wildcard extraction
}
```

#### Nested Context Rules
```python
rules = {
    'data': {                                 # Apply rules to array items
        'fields': ['field1', 'field2'],       # Basic field extraction
        'categories[*].name': True,           # Produces flat array
        'assets[*].url': True                 # Key becomes 'assets_url'
    }
}
```

### Supported JMESPath Expressions

The extractor supports most JMESPath expressions:

- **Dot notation**: `object.property`
- **Array indexing**: `array[0]`, `array[-1]`
- **Array slicing**: `array[0:2]`, `array[1:]`
- **Wildcard**: `array[*].property`
- **Filtering**: `array[?condition]`
- **Multi-select**: `{name: name, price: price}`
- **Functions**: `length(array)`, `sort_by(array, &property)`

## Error Handling

The JSONExtractor handles various error conditions gracefully:

### Invalid Data
```python
# JSONExtractor needs rules at initialization
rules = {"name": True}
extractor = JSONExtractor(rules)

# None data will cause extraction to fail
try:
    result = extractor.extract(None)
except Exception as e:
    print(f"Error: {e}")
```

### Missing Fields
```python
data = {"name": "Product"}
rules = {
    "name": True,
    "missing_field": True,
    "also_missing": True
}
extractor = JSONExtractor(rules)
result = extractor.extract(data)
# Output: {"name": "Product"}  # Missing fields are silently ignored
```

### Null Values
```python
data = {"name": "Product", "description": None}
rules = {
    "name": True,
    "description": True  # None values are filtered out completely
}
extractor = JSONExtractor(rules)
result = extractor.extract(data)
# Output: {"name": "Product"}  # No description key since it was None
```

## Performance Tips

### 1. Use Specific Field Selection
```python
# Good - extract only needed fields
rules = {"products[*].name": True}

# Avoid - extracting everything then filtering in Python
rules = {"products": True}  # Then filter manually
```

### 2. Use Array Limits for Large Datasets
```python
# Good - limit array processing
rules = {
    "products": {
        "limit": 100,
        "fields": ["name", "price"]
    }
}

# Avoid - processing entire large arrays
rules = {"products[*].name": True}  # Could be thousands of items
```

### 3. Minimize Rule Complexity
```python
# Good - simple, focused rules
rules = {
    "name": True,
    "price.amount": True,
    "categories[*].name": True
}

# Avoid - overly complex nested structures
rules = {
    "product": {
        "details": {
            "info": {
                "fields": ["name", "description", "specs"]
            }
        }
    }
}
```

### 4. Reuse Extractor Instances When Possible
```python
# Good - reuse extractor with same rules
rules = {"name": True, "price": True}
extractor = JSONExtractor(rules)
for data_item in large_dataset:
    result = extractor.extract(data_item)

# Acceptable - new extractor for different rules
for data_item in large_dataset:
    rules = get_rules_for_item(data_item)
    extractor = JSONExtractor(rules)
    result = extractor.extract(data_item)
```

## Testing

A comprehensive test suite with 19 test cases covers all JSONExtractor functionality:

```bash
# Run all JSONExtractor tests (19 tests, all passing)
python -m pytest tests/unit/test_json_extractor.py -v

# Run specific test categories
python -m pytest tests/unit/test_json_extractor.py::TestJSONExtractor::test_wildcard_array_extraction_root_level -v

# Run with coverage
python -m pytest tests/unit/test_json_extractor.py --cov=app.utils.json_extractor
```

### Test Coverage

The test suite validates:
- ✅ Basic field extraction (simple and nested)
- ✅ Wildcard array extraction (root level and nested contexts) 
- ✅ Mixed instruction patterns with fields syntax
- ✅ Complex nested extraction with multiple patterns
- ✅ Array root data handling
- ✅ Missing field filtering behavior
- ✅ Null value filtering in arrays
- ✅ Empty array handling
- ✅ Array limits and field selection
- ✅ Regex filtering functionality
- ✅ Unicode character support
- ✅ Boolean and numeric value preservation
- ✅ Performance with large datasets
- ✅ Key naming patterns in nested contexts

## Common Use Cases

### API Response Normalization
Transform various API response formats into consistent structures.

### Data Pipeline Processing  
Extract relevant fields from complex data for downstream processing.

### Configuration Management
Extract specific configuration values from nested config files.

### Report Generation
Pull summary data from detailed datasets for reporting.

### Data Migration
Transform data structures during migration between systems.

---

For more examples and advanced usage patterns, see the test suite in `tests/unit/test_json_extractor.py`.