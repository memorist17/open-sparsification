#!/bin/bash
# OpenSparsity Demo & Dashboard Launcher

echo "=================================================="
echo "OpenSparsity Metrics - Demo & Dashboard"
echo "=================================================="
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python not found! Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $PYTHON"
echo ""

# Check if demo_output exists
if [ ! -d "demo_output" ]; then
    echo "📊 Running demo to generate data..."
    echo "=================================================="
    $PYTHON main.py demo
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Demo failed. Installing dependencies..."
        $PYTHON -m pip install -r requirements.txt
        echo ""
        echo "Retrying demo..."
        $PYTHON main.py demo
    fi
    echo ""
else
    echo "✓ Demo data found in demo_output/"
    echo ""
fi

# Launch dashboard
echo "=================================================="
echo "🚀 Launching Interactive Dashboard..."
echo "=================================================="
echo ""
echo "Dashboard will open at: http://127.0.0.1:8050"
echo "Press Ctrl+C to stop"
echo ""

$PYTHON dashboard.py --data demo_output

# If dashboard fails
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Dashboard failed. Installing Dash..."
    $PYTHON -m pip install dash plotly
    echo ""
    echo "Retrying dashboard..."
    $PYTHON dashboard.py --data demo_output
fi

