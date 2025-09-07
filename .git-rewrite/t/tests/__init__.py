# PetPlantr Test Suite
# Critical test scaffolds for immediate implementation

from .conftest import *
from .test_critical_business_logic import *
from .test_ai_model_quality import *
from .test_api_endpoints import *
from .test_security_auth import *

# Test discovery
# Run with: pytest tests/ --cov=src --cov-report=html
