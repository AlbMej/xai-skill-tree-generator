"""
Job Skill Tree Generator
Extracts required skills from job postings and creates skill tree visualizations.
Uses xAI API to analyze job descriptions and identify required qualifications.
"""

import os
import json
import requests
from typing import Dict, Any, List
import html
import re

from skill_tree_common import build_skill_tree, generate_html_visualization


class JobSkillTreeGenerator:
    def __init__(self, api_key: str = None):
        """Initialize the job skill tree generator."""
        self.api_key = api_key or os.getenv('XAI_API_KEY')
        self.api_url = "https://api.x.ai/v1/chat/completions"
    
    def clean_job_description(self, description: str) -> str:
        """Clean and extract text from HTML job description."""
        if not description:
            return ""
        
        # Decode HTML entities
        text = html.unescape(description)
        
        # Remove HTML tags using regex
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def analyze_job_with_xai(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """Use xAI API to analyze job posting and extract required skills."""
        
        # Clean the description
        clean_description = self.clean_job_description(job_description)
        
        prompt = f"""Analyze the following job posting and extract all required skills, qualifications, and experience needed for a candidate to match this position.

Job Title: {job_title}

Job Description:
{clean_description}

Please identify:
1. Required technical skills (programming languages, frameworks, tools, technologies)
2. Required soft skills (communication, leadership, etc.)
3. Domain expertise required (AI/ML, web development, etc.)
4. Required certifications and qualifications
5. Education requirements (degrees, fields of study)
6. Experience requirements (years, specific roles, industries)
7. Preferred qualifications (nice-to-have skills)

Return a JSON structure with this format:
{{
    "skills": {{
        "technical": {{
            "programming_languages": ["skill1", "skill2"],
            "frameworks": ["skill1", "skill2"],
            "tools": ["skill1", "skill2"],
            "databases": ["skill1", "skill2"],
            "cloud_platforms": ["skill1", "skill2"],
            "technologies": ["tech1", "tech2"]
        }},
        "soft_skills": ["skill1", "skill2"],
        "domains": ["domain1", "domain2"],
        "certifications": ["cert1", "cert2"],
        "education": ["requirement1", "requirement2"],
        "experience_requirements": ["requirement1", "requirement2"]
    }},
    "required_vs_preferred": {{
        "required": ["skill1", "skill2"],
        "preferred": ["skill1", "skill2"]
    }}
}}

Only return valid JSON, no additional text."""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert job posting analyzer. Extract required skills and qualifications. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4-latest",
            "stream": False,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Extract the JSON from the response
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Try to parse JSON from the content
            content = content.strip()
            if content.startswith('```'):
                # Remove markdown code blocks
                lines = content.split('\n')
                content = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            
            skill_data = json.loads(content)
            return skill_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response content: {content[:500]}")
            return self._fallback_skill_extraction(job_title, clean_description)
        except Exception as e:
            print(f"Error calling xAI API: {e}")
            return self._fallback_skill_extraction(job_title, clean_description)
    
    def _fallback_skill_extraction(self, job_title: str, description: str) -> Dict[str, Any]:
        """Fallback skill extraction using keyword matching if API fails."""
        tech_keywords = {
            'programming_languages': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'TypeScript', 'SQL', 'R', 'Swift', 'Kotlin'],
            'frameworks': ['React', 'Vue', 'Angular', 'Django', 'Flask', 'FastAPI', 'Spring', 'Node.js', 'Express', 'TensorFlow', 'PyTorch'],
            'tools': ['Git', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Jenkins', 'CI/CD', 'Linux', 'MongoDB', 'PostgreSQL', 'Redis']
        }
        
        found_skills = {'programming_languages': [], 'frameworks': [], 'tools': []}
        
        desc_lower = description.lower()
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    found_skills[category].append(keyword)
        
        return {
            "skills": {
                "technical": found_skills,
                "soft_skills": [],
                "domains": [],
                "certifications": [],
                "education": [],
                "experience_requirements": []
            },
            "required_vs_preferred": {
                "required": [],
                "preferred": []
            }
        }
    
    def generate_skill_tree_for_job(self, job: Dict[str, Any], output_dir: str = "job_skill_trees") -> Dict[str, Any]:
        """
        Generate skill tree for a single job posting.
        
        Args:
            job: Job dictionary with title and description
            output_dir: Directory to save output files
            
        Returns:
            Skill tree dictionary
        """
        job_id = job.get('id', 'unknown')
        job_title = job.get('title', 'Unknown Position')
        job_description = job.get('description', '')
        
        print(f"\n[*] Analyzing job: {job_title} (ID: {job_id})")
        
        if not job_description:
            print(f"[WARNING] No description found for job {job_id}, skipping...")
            return None
        
        # Analyze job with xAI
        if self.api_key:
            print(f"  Analyzing job description with xAI API...")
            skill_data = self.analyze_job_with_xai(job_title, job_description)
        else:
            print(f"  No API key found, using fallback extraction...")
            clean_description = self.clean_job_description(job_description)
            skill_data = self._fallback_skill_extraction(job_title, clean_description)
        
        # Build skill tree
        print(f"  Building skill tree structure...")
        skill_tree = build_skill_tree(skill_data)
        
        # Add job metadata to tree
        skill_tree['job_id'] = job_id
        skill_tree['job_title'] = job_title
        skill_tree['location'] = job.get('location', 'Not specified')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Sanitize filename
        safe_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        output_json = os.path.join(output_dir, f"job_{job_id}_{safe_title}_skill_tree.json")
        output_html = os.path.join(output_dir, f"job_{job_id}_{safe_title}_skill_tree.html")
        
        # Save JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(skill_tree, f, indent=2, ensure_ascii=False)
        print(f"  Saved skill tree JSON to {output_json}")
        
        # Generate HTML visualization
        title = f"Required Skills: {job_title}"
        generate_html_visualization(skill_tree, output_html, title)
        print(f"  Generated HTML visualization: {output_html}")
        
        return skill_tree
    
    def generate_skill_trees_for_all_jobs(self, jobs_file: str = "xai_jobs.json", output_dir: str = "job_skill_trees", limit: int = None):
        """
        Generate skill trees for all jobs in the JSON file.
        
        Args:
            jobs_file: Path to JSON file with job listings
            output_dir: Directory to save output files
            limit: Optional limit on number of jobs to process
        """
        if not os.path.exists(jobs_file):
            print(f"[ERROR] Jobs file not found: {jobs_file}")
            print(f"[*] Please run fetch_jobs.py --details first to fetch job descriptions")
            return
        
        print(f"[*] Loading jobs from {jobs_file}...")
        with open(jobs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        total_jobs = len(jobs)
        
        if limit:
            jobs = jobs[:limit]
            print(f"[*] Processing {len(jobs)} of {total_jobs} jobs (limit: {limit})")
        else:
            print(f"[*] Processing all {total_jobs} jobs")
        
        skill_trees = []
        successful = 0
        failed = 0
        
        for i, job in enumerate(jobs, 1):
            try:
                skill_tree = self.generate_skill_tree_for_job(job, output_dir)
                if skill_tree:
                    skill_trees.append(skill_tree)
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"[ERROR] Failed to process job {job.get('id', 'unknown')}: {e}")
                failed += 1
        
        # Save summary
        summary = {
            'total_jobs_processed': len(jobs),
            'successful': successful,
            'failed': failed,
            'skill_trees': skill_trees
        }
        
        summary_file = os.path.join(output_dir, 'job_skill_trees_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SUCCESS] Processed {successful} jobs successfully, {failed} failed")
        print(f"[*] Summary saved to {summary_file}")


def main():
    """Main entry point."""
    import sys
    
    jobs_file = "xai_jobs.json"
    output_dir = "job_skill_trees"
    limit = None
    
    # Parse command line arguments
    if '--jobs-file' in sys.argv:
        idx = sys.argv.index('--jobs-file')
        if idx + 1 < len(sys.argv):
            jobs_file = sys.argv[idx + 1]
    
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    if '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        if idx + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[idx + 1])
            except ValueError:
                print("[ERROR] Invalid limit value")
                return
    
    generator = JobSkillTreeGenerator()
    generator.generate_skill_trees_for_all_jobs(jobs_file, output_dir, limit)


if __name__ == "__main__":
    main()

