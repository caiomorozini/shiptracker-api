#!/usr/bin/env bash
# Pre-deployment checklist script

echo "🔍 ShipTracker API - Pre-Deployment Check"
echo "=========================================="
echo ""

errors=0
warnings=0

# Check 1: Build script executable
echo "1️⃣  Checking build.sh permissions..."
if [ -x "build.sh" ]; then
    echo "   ✅ build.sh is executable"
else
    echo "   ❌ build.sh is NOT executable"
    echo "   💡 Run: chmod +x build.sh"
    errors=$((errors+1))
fi

# Check 2: Required files exist
echo ""
echo "2️⃣  Checking required files..."
required_files=("Procfile" "build.sh" "render.yaml" "pyproject.toml" "alembic.ini")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file is missing"
        errors=$((errors+1))
    fi
done

# Check 3: Alembic migrations
echo ""
echo "3️⃣  Checking Alembic migrations..."
if [ -d "alembic/versions" ]; then
    migration_count=$(find alembic/versions -name "*.py" ! -name "__*" | wc -l)
    if [ "$migration_count" -gt 0 ]; then
        echo "   ✅ Found $migration_count migration(s)"
    else
        echo "   ⚠️  No migrations found"
        warnings=$((warnings+1))
    fi
else
    echo "   ❌ alembic/versions directory not found"
    errors=$((errors+1))
fi

# Check 4: Python syntax
echo ""
echo "4️⃣  Checking Python syntax..."
if python -m py_compile app/main.py 2>/dev/null; then
    echo "   ✅ app/main.py syntax OK"
else
    echo "   ❌ app/main.py has syntax errors"
    errors=$((errors+1))
fi

# Check 5: Dependencies
echo ""
echo "5️⃣  Checking dependencies..."
if [ -f "pyproject.toml" ]; then
    if grep -q "fastapi" pyproject.toml; then
        echo "   ✅ FastAPI listed in dependencies"
    else
        echo "   ❌ FastAPI not found in dependencies"
        errors=$((errors+1))
    fi
    
    if grep -q "uvicorn" pyproject.toml; then
        echo "   ✅ Uvicorn listed in dependencies"
    else
        echo "   ❌ Uvicorn not found in dependencies"
        errors=$((errors+1))
    fi
    
    if grep -q "sqlalchemy" pyproject.toml; then
        echo "   ✅ SQLAlchemy listed in dependencies"
    else
        echo "   ❌ SQLAlchemy not found in dependencies"
        errors=$((errors+1))
    fi
fi

# Check 6: Git status
echo ""
echo "6️⃣  Checking Git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    if [ -z "$(git status --porcelain)" ]; then
        echo "   ✅ Working directory clean"
    else
        echo "   ⚠️  You have uncommitted changes"
        echo "   💡 Run: git add . && git commit -m 'Prepare for deployment'"
        warnings=$((warnings+1))
    fi
    
    current_branch=$(git branch --show-current)
    echo "   📍 Current branch: $current_branch"
else
    echo "   ⚠️  Not a git repository"
    warnings=$((warnings+1))
fi

# Check 7: Environment variables template
echo ""
echo "7️⃣  Checking environment configuration..."
if [ -f ".env.example" ]; then
    echo "   ✅ .env.example exists"
    
    # Check for required variables
    required_vars=("DATABASE_URL" "SECRET_KEY" "APP_ENV")
    for var in "${required_vars[@]}"; do
        if grep -q "$var" .env.example; then
            echo "   ✅ $var documented"
        else
            echo "   ⚠️  $var not in .env.example"
            warnings=$((warnings+1))
        fi
    done
else
    echo "   ⚠️  .env.example not found"
    warnings=$((warnings+1))
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Summary:"
echo "   Errors: $errors"
echo "   Warnings: $warnings"
echo ""

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo "✅ All checks passed! Ready for deployment."
    echo ""
    echo "Next steps:"
    echo "1. Push to Git: git push origin main"
    echo "2. Follow: DEPLOY_QUICKSTART.md"
    exit 0
elif [ $errors -eq 0 ]; then
    echo "⚠️  Ready with warnings. Review issues above."
    exit 0
else
    echo "❌ Found $errors error(s). Fix them before deploying."
    exit 1
fi
