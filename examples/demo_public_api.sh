#!/bin/bash
# Demo script using JSONPlaceholder public API (no auth required)

echo "=== API ETL Demo ==="
echo ""

# Demo 1: Basic extraction
echo "1. Basic extraction (2 pages)"
python ../api_etl.py \
  --url "https://jsonplaceholder.typicode.com/posts" \
  --output posts.csv \
  --max-pages 2

echo ""
echo "✓ Created: posts.csv (20 posts)"
echo ""

# Demo 2: Field filtering
echo "2. With field filtering"
python ../api_etl.py \
  --url "https://jsonplaceholder.typicode.com/users" \
  --output users.xlsx \
  --fields "id,name,email,company" \
  --max-pages 1

echo ""
echo "✓ Created: users.xlsx (10 users, 4 columns)"
echo ""

# Demo 3: With query parameters
echo "3. With query parameters"
python ../api_etl.py \
  --url "https://jsonplaceholder.typicode.com/posts" \
  --output filtered_posts.csv \
  --params '{"userId":1}' \
  --fields "id,title" \
  --max-pages 1

echo ""
echo "✓ Created: filtered_posts.csv (posts from user 1)"
echo ""

echo "Demo complete! Check the generated files."