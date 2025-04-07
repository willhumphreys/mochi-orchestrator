#!/bin/bash

# Get list of stacks and store in array
mapfile -t stacks < <(cdk list)

# Display stacks with numbers
echo "Available stacks:"
for i in "${!stacks[@]}"; do
  echo "  $((i+1)). ${stacks[$i]}"
done

echo ""
read -p "Enter stack number to deploy: " stack_number

# Validate input is a number
if ! [[ "$stack_number" =~ ^[0-9]+$ ]]; then
  echo "Error: Please enter a valid number"
  exit 1
fi

# Adjust for zero-based indexing and check bounds
index=$((stack_number-1))
if [ "$index" -lt 0 ] || [ "$index" -ge "${#stacks[@]}" ]; then
  echo "Error: Please select a number between 1 and ${#stacks[@]}"
  exit 1
fi

# Get the selected stack name
selected_stack="${stacks[$index]}"

echo "Deploying stack: $selected_stack"
cdk deploy "$selected_stack"