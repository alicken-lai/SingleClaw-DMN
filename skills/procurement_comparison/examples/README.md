# procurement_comparison – Examples

## Sample Input (`examples/sample_input.json`)

```json
{
  "project_name": "Office Laptop Procurement 2024",
  "criteria": ["price_usd", "warranty_years", "delivery_days", "support_rating"],
  "vendors": [
    {
      "name": "Vendor Alpha",
      "price_usd": 1200,
      "warranty_years": 3,
      "delivery_days": 5,
      "support_rating": 4.5
    },
    {
      "name": "Vendor Beta",
      "price_usd": 1050,
      "warranty_years": 2,
      "delivery_days": 10,
      "support_rating": 3.8
    },
    {
      "name": "Vendor Gamma",
      "price_usd": 1350,
      "warranty_years": 4,
      "delivery_days": 3,
      "support_rating": 4.9
    }
  ]
}
```

## Expected Output Highlights

- Side-by-side comparison table
- Recommendation for Vendor Alpha or Gamma depending on priority weights
- Caveats about Vendor Beta's shorter warranty
