#!/bin/bash

# Test runner script for qchat
set -e  # Exit on any error

echo "🧪 QChat Service Layer Test Suite"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📋 Running Service Layer Tests..."
echo "----------------------------------"

# Run only the service tests with detailed output
python -m pytest tests/test_services.py -v --tb=short --color=yes

echo ""
echo "📋 Running All Tests..."
echo "------------------------"

# Run all tests
python -m pytest tests/ -v --tb=short --color=yes

# echo ""
# echo "📊 Test Coverage Report..."
# echo "-------------------------"

# # Check if pytest-cov is available by trying to import it
# if python -c "import pytest_cov" 2>/dev/null; then
#     echo "📈 Generating coverage report for service layer:"
#     python -m pytest tests/ --cov=server/services --cov-report=term-missing --cov-report=html --cov-fail-under=0
#     echo ""
#     echo "📄 HTML coverage report generated in htmlcov/index.html"
# elif python -c "from pytest_cov import plugin" 2>/dev/null; then
#     echo "📈 Generating coverage report for service layer:"
#     python -m pytest tests/ --cov=server/services --cov-report=term-missing --cov-report=html --cov-fail-under=0
#     echo ""
#     echo "📄 HTML coverage report generated in htmlcov/index.html"
# elif python -m pytest --help | grep -q -- "--cov"; then
#     echo "📈 Pytest-cov is available, generating coverage report:"
#     python -m pytest tests/ --cov=server/services --cov-report=term-missing --cov-report=html --cov-fail-under=0
#     echo ""
#     echo "📄 HTML coverage report generated in htmlcov/index.html"
# else
#     echo "⚠️  pytest-cov not detected or not working properly"
#     echo "� Checking installation..."
#     pip list | grep pytest-cov || echo "❌ pytest-cov not found in pip list"
#     echo "💡 Try: pip install --force-reinstall pytest-cov"
# fi

echo ""
echo "✅ All tests completed successfully!"
echo "🎉 Service layer refactoring is working perfectly!"
