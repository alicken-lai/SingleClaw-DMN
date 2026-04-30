# Procurement Workflow – Example

This example shows how to use SingleClaw DMN to streamline a **vendor
procurement decision**.

## Workflow

```bash
# 1. Initialise workspace
singleclaw init

# 2. Record the procurement context
singleclaw remember "Comparing laptops for 20-person engineering team" --tag project

# 3. Check the Guardian policy before running
singleclaw guardian-check "run procurement comparison skill"

# 4. Run the skill
singleclaw run procurement_comparison --input vendor_quotes.json

# 5. Store the decision
singleclaw remember "Chose Vendor Alpha – best warranty + support" --tag decision
```

## Sample Input File (`vendor_quotes.json`)

See `../../skills/procurement_comparison/examples/README.md` for a sample
input JSON file.
