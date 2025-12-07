"""
Add application URLs to existing skill tree JSON files.
Matches job IDs with xai_jobs.json to add application_url without re-analyzing.
"""

import os
import json
import re
from typing import Dict, Any, List


def extract_job_id_from_filename(filename: str) -> int:
    """Extract job ID from filename like 'job_4922802007_AI_Economics_Tutor_skill_tree.json'."""
    match = re.search(r'job_(\d+)_', filename)
    if match:
        return int(match.group(1))
    return None


def load_jobs_mapping(jobs_file: str = "xai_jobs.json") -> Dict[int, Dict[str, Any]]:
    """Load jobs from xai_jobs.json and create a mapping by job ID."""
    if not os.path.exists(jobs_file):
        print(f"[ERROR] Jobs file not found: {jobs_file}")
        return {}
    
    print(f"[*] Loading jobs from {jobs_file}...")
    with open(jobs_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = data.get('jobs', [])
    jobs_map = {}
    
    for job in jobs:
        job_id = job.get('id')
        if job_id:
            jobs_map[job_id] = {
                'application_url': job.get('application_url') or job.get('greenhouse_url', ''),
                'title': job.get('title', ''),
                'location': job.get('location', '')
            }
    
    print(f"[*] Loaded {len(jobs_map)} jobs")
    return jobs_map


def update_skill_tree_file(filepath: str, jobs_map: Dict[int, Dict[str, Any]]) -> bool:
    """Update a single skill tree JSON file with application URL."""
    try:
        # Read the skill tree JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            skill_tree = json.load(f)
        
        # Get job ID from file or JSON
        job_id = skill_tree.get('job_id')
        if not job_id:
            # Try to extract from filename
            filename = os.path.basename(filepath)
            job_id = extract_job_id_from_filename(filename)
        
        if not job_id:
            print(f"  [WARNING] Could not find job_id in {filepath}")
            return False
        
        # Check if URL already exists
        if skill_tree.get('application_url'):
            print(f"  [SKIP] Job {job_id} already has application_url")
            return False
        
        # Get job data from mapping
        job_data = jobs_map.get(job_id)
        if not job_data:
            print(f"  [WARNING] Job {job_id} not found in xai_jobs.json")
            return False
        
        # Add application URL
        skill_tree['application_url'] = job_data['application_url']
        
        # Optionally update title and location if they're missing or different
        if not skill_tree.get('job_title') and job_data.get('title'):
            skill_tree['job_title'] = job_data['title']
        if not skill_tree.get('location') and job_data.get('location'):
            skill_tree['location'] = job_data['location']
        
        # Save updated JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(skill_tree, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Updated job {job_id}: {job_data.get('title', 'Unknown')}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Invalid JSON in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] Error processing {filepath}: {e}")
        return False


def update_all_skill_trees(skill_trees_dir: str = "job_skill_trees", jobs_file: str = "xai_jobs.json"):
    """Update all skill tree JSON files with application URLs."""
    if not os.path.exists(skill_trees_dir):
        print(f"[ERROR] Skill trees directory not found: {skill_trees_dir}")
        return
    
    # Load jobs mapping
    jobs_map = load_jobs_mapping(jobs_file)
    if not jobs_map:
        print("[ERROR] No jobs loaded. Exiting.")
        return
    
    # Find all skill tree JSON files
    print(f"\n[*] Scanning {skill_trees_dir} for skill tree JSON files...")
    json_files = [
        os.path.join(skill_trees_dir, f)
        for f in os.listdir(skill_trees_dir)
        if f.endswith('_skill_tree.json')
    ]
    
    print(f"[*] Found {len(json_files)} skill tree JSON files")
    
    # Update each file
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        result = update_skill_tree_file(filepath, jobs_map)
        if result:
            updated_count += 1
        elif "already has" in str(result) or "SKIP" in str(result):
            skipped_count += 1
        else:
            error_count += 1
    
    # Print summary
    print(f"\n[*] Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped (already had URL): {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(json_files)}")


def main():
    """Main entry point."""
    import sys
    
    skill_trees_dir = "job_skill_trees"
    jobs_file = "xai_jobs.json"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage: python add_urls_to_skill_trees.py [skill_trees_dir] [jobs_file]")
            print("\nUpdates existing skill tree JSON files with application URLs from xai_jobs.json")
            print("\nArguments:")
            print("  skill_trees_dir  Directory containing skill tree JSON files (default: job_skill_trees)")
            print("  jobs_file        Path to jobs JSON file (default: xai_jobs.json)")
            return
        
        skill_trees_dir = sys.argv[1]
    
    if len(sys.argv) > 2:
        jobs_file = sys.argv[2]
    
    update_all_skill_trees(skill_trees_dir, jobs_file)


if __name__ == "__main__":
    main()

