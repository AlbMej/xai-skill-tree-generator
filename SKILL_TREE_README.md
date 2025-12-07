# Skill Tree Generator - Split Architecture

The skill tree generator has been split into separate modules for better organization:

## Module Structure

### 1. `skill_tree_common.py`
Shared functionality used by both resume and job skill tree generators:
- `build_skill_tree()` - Builds hierarchical skill tree structure
- `generate_html_visualization()` - Creates interactive HTML visualizations

### 2. `resume_skill_tree.py`
Generates skill trees from candidate resumes (PDF files).

**Usage:**
```bash
python resume_skill_tree.py [resume.pdf]
```

**Output:**
- `resume_skill_tree.json` - Structured skill data
- `resume_skill_tree.html` - Interactive visualization

### 3. `job_skill_tree.py`
Generates skill trees from job postings, showing required skills for each position.

**Usage:**
```bash
# Generate skill trees for all jobs
python job_skill_tree.py

# Limit number of jobs processed
python job_skill_tree.py --limit 10

# Specify custom jobs file
python job_skill_tree.py --jobs-file xai_jobs.json

# Specify output directory
python job_skill_tree.py --output-dir job_skill_trees
```

**Output:**
- `job_skill_trees/job_{id}_{title}_skill_tree.json` - Skill tree for each job
- `job_skill_trees/job_{id}_{title}_skill_tree.html` - Visualization for each job
- `job_skill_trees/job_skill_trees_summary.json` - Summary of all processed jobs

## Workflow

### Step 1: Fetch Jobs with Descriptions
First, fetch job listings with full descriptions:
```bash
python fetch_jobs.py --details
```

This creates `xai_jobs.json` with job descriptions (HTML entities are automatically decoded).

### Step 2: Generate Candidate Skill Tree
Generate skill tree from your resume:
```bash
python resume_skill_tree.py AlbertoMejiaResume.pdf
```

### Step 3: Generate Job Skill Trees
Generate skill trees for all job postings:
```bash
python job_skill_tree.py
```

Or process a limited number:
```bash
python job_skill_tree.py --limit 5
```

## Features

### Resume Skill Trees
- Extracts skills from PDF resumes
- Uses xAI API for intelligent skill extraction
- Fallback keyword matching if API unavailable
- Categorizes: Technical Skills, Soft Skills, Domains, Certifications

### Job Skill Trees
- Analyzes job descriptions to identify required skills
- Extracts: Technical skills, Soft skills, Education requirements, Experience requirements, Certifications
- Cleans HTML from job descriptions automatically
- Generates individual skill trees for each position

## API Key Setup

Set your xAI API key for enhanced analysis:
```bash
export XAI_API_KEY="your_api_key_here"
```

Both generators work without API keys using fallback keyword matching, but API analysis provides much better results.

## Output Format

Both generators create:
1. **JSON files** - Structured skill data in hierarchical format
2. **HTML files** - Interactive D3.js visualizations with:
   - Zoom controls
   - Expand/collapse functionality
   - Color-coded skill categories
   - Hover tooltips

## Example: Comparing Candidate vs Job Requirements

1. Generate your resume skill tree:
   ```bash
   python resume_skill_tree.py
   ```

2. Generate skill trees for jobs you're interested in:
   ```bash
   python job_skill_tree.py --limit 5
   ```

3. Compare the JSON files or HTML visualizations to see:
   - Which skills you have that match job requirements
   - Which skills you need to develop
   - Missing certifications or qualifications

## Notes

- The original `skill_tree_generator.py` is still available but deprecated. Use `resume_skill_tree.py` instead.
- Job descriptions must be fetched with `--details` flag to include full descriptions
- HTML entities in job descriptions are automatically decoded
- Processing many jobs may take time due to API rate limits (0.5s delay between requests)

