# xAI Skill Tree Generator

A Python tool to fetch job postings from xAI's careers page and generate hierarchical skill trees for interview assessment. Built for the xAI hackathon as part of the [xAI Talent Pool Project](https://github.com/vincenzopalazzo/xai-talent-pool). This component generates the skill tree data used by the [Interview Tab](https://github.com/[your-username]/xai-talent-pool-interview-ui) portion. 

## Features
- Fetch all available xAI job postings
- Search for specific job titles or keywords
- Retrieve detailed job descriptions
- Generate skill trees for interview preparation

## Usage

### Fetch all jobs
`python fetch_jobs.py`

### Search for specific jobs
`python fetch_jobs.py --search "Software Engineer"`

### Fetch with full job descriptions (slower)
`python fetch_jobs.py --details`

### Combine search and details
`python fetch_jobs.py --search "Engineer" --details`

## Integration
The generated skill trees are used by the [Interview Tab](https://github.com/[your-username]/xai-talent-pool-interview-ui) portion for interactive interview assessments with progress tracking.
