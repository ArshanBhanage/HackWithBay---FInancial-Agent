#!/bin/bash
# Activation script for the HWB project virtual environment
source venv/bin/activate
echo "Virtual environment activated. You can now run:"
echo "  python scripts/build_policy.py ./docs/contract.pdf"
echo "  python scripts/validate_fact.py '{\"type\":\"fee_post\",\"payload\":{\"subject\":\"Institution A\",\"fee_rate\":0.0200}}'"
