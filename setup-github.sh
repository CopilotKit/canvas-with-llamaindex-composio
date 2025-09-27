#!/bin/bash

# GitHub repository setup script
# Replace YOUR_USERNAME and YOUR_REPO_NAME with your actual values

echo "Setting up GitHub repository..."

# Remove existing origin
git remote remove origin

# Add your new repository as origin
# Replace with your actual GitHub username and repository name
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Verify the new remote
echo "New remote configuration:"
git remote -v

# Push all branches and tags
echo "Pushing to GitHub..."
git push -u origin feat/pitch-platform

# If you want to make this the main branch
# git branch -M main
# git push -u origin main

echo "Done! Your code is now on GitHub."
