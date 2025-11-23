#!/bin/bash

# Script to clean up insa-iot repository branches
echo "🧹 Starting InSa IoT repository cleanup..."

# Branches to keep
KEEP_BRANCHES=(
    "claude/iot-platform-ai-rag-01UT4tog912F8yua1G1CE8us"
    "claude/iot-platform-blueprint-011CUXwf6fyf4dDNrAuf5Ktc"
    "claude/iot-platform-merge-01EXRaPMmTMVbtcJBiHpoaAa"
    "claude/oss-raspberry-pi-iiot-011CUoiqvPxCMEQxERWZ5A9g"
    "main"
)

# Function to delete branches in batches
delete_branches_batch() {
    local branches=("$@")
    local batch_size=50
    local total=${#branches[@]}
    local deleted=0

    for ((i=0; i<$total; i+=batch_size)); do
        batch=("${branches[@]:$i:$batch_size}")
        if [ ${#batch[@]} -gt 0 ]; then
            echo "Deleting batch of ${#batch[@]} branches..."
            for branch in "${batch[@]}"; do
                # Remove the remote prefix for the delete command
                branch_name=${branch#insa-iot/}
                git push insa-iot --delete "$branch_name" 2>/dev/null && ((deleted++)) || echo "Already deleted or error: $branch_name"
            done
            echo "Progress: $((i + ${#batch[@]}))/$total branches processed"
        fi
    done
    echo "✅ Deleted $deleted branches"
}

# Step 1: Delete all auto-fix branches
echo "📋 Step 1: Collecting auto-fix branches..."
AUTO_FIX_BRANCHES=($(git branch -r | grep "insa-iot/auto-fix" | sed 's/^[[:space:]]*//' | tr '\n' ' '))
echo "Found ${#AUTO_FIX_BRANCHES[@]} auto-fix branches to delete"

if [ ${#AUTO_FIX_BRANCHES[@]} -gt 0 ]; then
    echo "🗑️ Deleting auto-fix branches..."
    delete_branches_batch "${AUTO_FIX_BRANCHES[@]}"
fi

# Step 2: Check for other branches to clean up
echo "📋 Step 2: Checking for other branches to clean..."
OTHER_BRANCHES=($(git branch -r | grep "insa-iot/" | grep -v "insa-iot/main" | sed 's/^[[:space:]]*//' | tr '\n' ' '))

# Filter out branches we want to keep
BRANCHES_TO_DELETE=()
for branch in "${OTHER_BRANCHES[@]}"; do
    should_keep=false
    branch_name=${branch#insa-iot/}

    for keep in "${KEEP_BRANCHES[@]}"; do
        if [ "$branch_name" == "$keep" ]; then
            should_keep=true
            break
        fi
    done

    if [ "$should_keep" = false ] && [ ! -z "$branch_name" ]; then
        BRANCHES_TO_DELETE+=("$branch")
    fi
done

echo "Found ${#BRANCHES_TO_DELETE[@]} additional branches to delete"
if [ ${#BRANCHES_TO_DELETE[@]} -gt 0 ]; then
    echo "Branches to delete:"
    for branch in "${BRANCHES_TO_DELETE[@]}"; do
        echo "  - $branch"
    done

    read -p "Delete these branches? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        delete_branches_batch "${BRANCHES_TO_DELETE[@]}"
    fi
fi

# Step 3: Final cleanup
echo "🧹 Running git garbage collection..."
git gc --prune=now --aggressive

# Step 4: Show final branch list
echo "📊 Final branch structure:"
git branch -r | grep "insa-iot/" | sort

echo "✅ Cleanup complete!"